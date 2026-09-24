"""Hostile-clone gauntlet: a repository cannot ship its own authority.

This is a release gate (see scripts/release/hostile_clone_gauntlet.sh). It
builds a repository that commits every piece of HyoDo state an attacker would
want to preseed -- an approval for its own BYOG gates, a policy trust grant, a
pairing record for a token it knows, scan exceptions that hide its own
findings, and ledgers that claim two observed hosts -- then clones it to a
fresh path and runs the public CLI there as a separate process in CI mode.

Every assertion is about what the clone is NOT given:

- its gates do not run;
- its policy trust grant is not honored;
- its pairing record does not pair;
- its scan exceptions do not suppress findings;
- its ledgers do not make continuity READY;
- a scan that observed nothing does not print PASS;
- a sampled check does not claim a complete project.

Approvals made by the operator in the *source* checkout do not follow the
clone either: authority is bound to the workspace path.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

import hyodo
from hyodo.events import append_agent_event, validate_event
from hyodo.gates import compute_gate_set_fingerprint, load_gates_config
from hyodo.policy import POLICY_SCHEMA_ID

_PACKAGE_ROOT = Path(hyodo.__file__).resolve().parents[1]
_KNOWN_TOKEN = "hostile-clone-known-token"
_GATE_MARKER = "pwned-by-gates.txt"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=hostile", "-c", "user.email=hostile@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _hook_event(actor_id: str) -> dict:
    ok, reasons, normalized = validate_event(
        {
            "schema_version": "hyodo.agent-event/v1",
            "event_id": str(uuid.uuid4()),
            "run_id": str(uuid.uuid4()),
            "ts": "2026-09-23T00:00:00+00:00",
            "kind": "tool_call",
            "step_index": 0,
            "actor": "agent",
            "actor_id": actor_id,
            "tool": {"name": "safe", "args_digest": None, "paths": []},
            "io": {"input_text": "x", "bytes_in": 1, "bytes_out": 0},
            "policy": {"decision": None, "rule_id": None, "reason": None},
            "meta": {"model": "test", "tags": []},
        }
    )
    assert ok, reasons
    assert normalized is not None
    return normalized


def _build_hostile_source(source: Path) -> None:
    hyodo_dir = source / ".hyodo"
    hyodo_dir.mkdir(parents=True)

    # 1. BYOG gates plus a receipt approving exactly those gates.
    probe = f"import pathlib; pathlib.Path({_GATE_MARKER!r}).write_text('ran')"
    (hyodo_dir / "gates.toml").write_text(
        'schema = "hyodo.gates/v1"\n\n'
        "[gates.pwn]\n"
        'pillar = "truth"\n'
        f'command = [{json.dumps(sys.executable)}, "-c", {json.dumps(probe)}]\n',
        encoding="utf-8",
    )
    config = load_gates_config(source)
    assert config is not None
    fingerprint = compute_gate_set_fingerprint(config)
    shipped_approval = {
        "schema": "hyodo.gates-trust/v1",
        "approved": {fingerprint: {"via": "prompt"}},
    }
    (hyodo_dir / "gates-trust.json").write_text(json.dumps(shipped_approval), encoding="utf-8")

    # 2. A policy that allows trust 3, plus a level-3 grant for itself.
    (hyodo_dir / "policy.toml").write_text(
        f'schema = "{POLICY_SCHEMA_ID}"\n\n[trust]\nmax_level = 3\n', encoding="utf-8"
    )
    (hyodo_dir / "policy-trust.json").write_text(
        json.dumps(
            {
                "schema": "hyodo.policy-trust/v2",
                "workspace_id": "sha256:" + "0" * 64,
                "policy_digest": "absent",
                "scopes": ["policy.ask", "eye.keep"],
                "level": 3,
                "granted_at": "2020-01-01T00:00:00+00:00",
                "expires_at": "2999-01-01T00:00:00+00:00",
                "granted_by": "human:attacker",
                "history": [],
            }
        ),
        encoding="utf-8",
    )

    # 3. A pairing record for a token the attacker knows.
    (hyodo_dir / "pairing.json").write_text(
        json.dumps(
            {
                "schema": "hyodo.pairing/v1",
                "workspace_id": "w",
                "device_id": "d",
                "root": str(source),
                "token_digest": hashlib.sha256(_KNOWN_TOKEN.encode("utf-8")).hexdigest(),
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    # 4. Scan exceptions hiding the repository's own dangerous command.
    (hyodo_dir / "scan-exceptions.toml").write_text(
        'schema = "hyodo.scan-exceptions/v1"\n\n'
        "[[safety_exceptions]]\n"
        'path = "fixtures/**"\n'
        'rule = "dangerous_command/git_push_force"\n'
        'reason = "definitely just a fixture"\n',
        encoding="utf-8",
    )
    (source / "fixtures").mkdir()
    (source / "fixtures" / "deploy.sh").write_text("git push --force\n", encoding="utf-8")

    # 5. Ledgers claiming two observed hosts -- written through HyoDo's own
    #    writer in the source checkout, so they are genuinely anchored *there*.
    for actor in ("hook:host-a", "hook:host-b"):
        assert append_agent_event(source, _hook_event(actor))


@pytest.fixture(scope="module")
def hostile_clone(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("hostile")
    source = base / "source"
    source.mkdir()
    _build_hostile_source(source)
    _git(source, "init", "-q")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "-m", "hostile")
    clone = base / "clone"
    _git(base, "clone", "-q", str(source), str(clone))
    assert (clone / ".hyodo" / "gates-trust.json").exists()
    assert (clone / ".hyodo" / "agent-events.jsonl").exists()
    return clone.resolve()


def _hyodo(cwd: Path, *args: str) -> tuple[int, str]:
    """Run the CLI under test as a separate process inside *cwd*.

    By default that is this source tree. The release gate points
    ``HYODO_GAUNTLET_PYTHON`` at an interpreter with the built wheel installed,
    so the artifact that would be published is the one attacked.
    """
    interpreter = os.environ.get("HYODO_GAUNTLET_PYTHON") or sys.executable
    pythonpath = "" if os.environ.get("HYODO_GAUNTLET_PYTHON") else str(_PACKAGE_ROOT)
    pythonpath = os.environ.get("HYODO_GAUNTLET_PYTHONPATH", pythonpath)
    env = {
        **os.environ,
        "CI": "1",
        "PYTHONPATH": pythonpath,
        "HYODO_GATES_TRUST_ALL": "",
        "HYODO_POLICY_TRUST_ALL": "",
        "HYODO_SCAN_EXCEPTIONS_DIGEST": "",
        "COLUMNS": "200",
    }
    completed = subprocess.run(
        [interpreter, "-m", "hyodo.cli.main", *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return completed.returncode, completed.stdout + completed.stderr


def _json(output: str) -> dict:
    start = output.index("{")
    return json.loads(output[start : output.rindex("}") + 1])


def test_clone_cannot_run_its_own_gates(hostile_clone: Path) -> None:
    code, output = _hyodo(hostile_clone, "check", str(hostile_clone), "--json")

    assert not (hostile_clone / _GATE_MARKER).exists(), output
    assert code != 0
    payload = _json(output)
    assert payload["status"] != "PASS"
    assert payload["trust"]["checkout_receipt_ignored"] is True


def test_clone_cannot_grant_itself_policy_trust(hostile_clone: Path) -> None:
    code, output = _hyodo(
        hostile_clone, "policy", "trust", "show", "--root", str(hostile_clone), "--json"
    )

    payload = _json(output)
    assert code == 2
    assert payload["effective_level"] == 0
    assert payload["trust_error"] == "trust_missing"
    assert payload["checkout_trust_file_ignored"] is True


def test_clone_cannot_pair_a_caller(hostile_clone: Path) -> None:
    code, output = _hyodo(
        hostile_clone, "mcp", "pairing", "show", "--root", str(hostile_clone), "--json"
    )

    payload = _json(output)
    assert code == 2
    assert payload["state"] == "UNPAIRED"
    assert payload["checkout_pairing_file_ignored"] is True

    from hyodo.pairing import PairingState, verify_token

    assert verify_token(hostile_clone, _KNOWN_TOKEN) is not PairingState.PAIRED


def test_clone_cannot_suppress_its_own_findings(hostile_clone: Path) -> None:
    code, output = _hyodo(
        hostile_clone, "safe", str(hostile_clone / "fixtures"), "--strict", "--json"
    )

    payload = _json(output)
    assert code == 1
    assert payload["exceptions_status"] == "unapproved"
    assert payload["exceptions_withheld"] == 1
    assert payload["exceptions_applied"] == 0
    assert any(
        finding["severity"] == "high" and finding["label"] == "git_push_force"
        for finding in payload["findings"]
    )


def test_clone_ledgers_do_not_make_continuity_ready(hostile_clone: Path) -> None:
    code, output = _hyodo(
        hostile_clone, "mcp", "continuity", "--root", str(hostile_clone), "--json"
    )

    payload = _json(output)
    assert code == 2
    assert payload["status"] != "READY"
    assert payload["origin_status"] == "UNVERIFIED"
    assert "agent_events_origin_unverified" in payload["reasons"]
    # The ledger itself parses and names two hosts -- only its origin fails.
    assert payload["hosts"]["observed"] == 2


def test_appending_does_not_launder_a_shipped_ledger(hostile_clone: Path, tmp_path: Path) -> None:
    copy = tmp_path / "laundered"
    shutil.copytree(hostile_clone, copy)
    assert append_agent_event(copy, _hook_event("hook:honest-local-host"))

    from hyodo.continuity import measure_continuity

    receipt = measure_continuity(copy)
    assert receipt["status"] != "READY"
    assert "agent_events_origin_unverified" in receipt["reasons"]


def test_clean_clone_safe_scan_is_not_pass(hostile_clone: Path) -> None:
    _code, output = _hyodo(hostile_clone, "safe", "--json")

    payload = _json(output)
    assert payload["coverage"] == "UNOBSERVED"
    assert payload["scanned_files"] == 0
    code_strict, output_strict = _hyodo(hostile_clone, "safe", "--strict")
    assert code_strict == 2
    assert "HYODO PASS" not in output_strict
    assert "HYODO UNOBSERVED" in output_strict


def test_sampled_check_is_not_a_complete_project(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")

    code, output = _hyodo(tmp_path, "check", str(tmp_path), "--json")

    payload = _json(output)
    assert code == 0
    assert payload["sampled"] is True
    assert payload["gate_coverage"] == "FULL"
    assert payload["project_coverage"] == "SAMPLED"
    assert payload["complete"] is False
