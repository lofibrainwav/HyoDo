"""Synthetic observations only; passing these is not production attestation."""

import hashlib
import json

import pytest

from hyodo.handoff import REQUIRED, inspect_handoff


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    return sha(raw)


def bundle(root, kind="code"):
    (root / "source.txt").write_text("synthetic original\n")
    (root / "output.txt").write_text("synthetic result\n")
    artifacts = [
        {"path": name, "sha256": sha((root / name).read_bytes()), "role": role}
        for name, role in [("source.txt", "source"), ("output.txt", "output")]
    ]
    plan = {
        "schema": "hyodo.handoff-plan/v1",
        "kind": kind,
        "run_id": "fresh-run",
        "created_at": 1000,
        "max_age_seconds": 60,
        "producer": "writer",
        "artifacts": artifacts,
        "checks": [],
    }
    for cid in sorted(REQUIRED[kind]):
        row = {
            "schema": "hyodo.handoff-check/v1",
            "id": cid,
            "run_id": "fresh-run",
            "status": "PASS",
            "coverage": "OBSERVED",
            "exit_code": 0,
            "observed_at": 1001,
            "producer": "reviewer" if cid == "review" else "tool",
            "artifact_digests": {a["path"]: a["sha256"] for a in artifacts},
        }
        digest = save(root / f"{cid}.json", row)
        plan["checks"].append({"id": cid, "path": f"{cid}.json", "sha256": digest})
    return plan


def run(root, plan, **kwargs):
    pin = save(root / "plan.json", plan)
    return inspect_handoff(
        root,
        root / "plan.json",
        pin,
        kwargs.pop("run_id", "fresh-run"),
        now=kwargs.pop("now", 1002),
        **kwargs,
    )


@pytest.mark.parametrize("kind", REQUIRED)
def test_complete_required_evidence_passes_without_action_authority(tmp_path, kind):
    result = run(tmp_path, bundle(tmp_path, kind))
    assert result["status"] == "VERIFIED_EVIDENCE"
    assert result["external_action_allowed"] is False
    assert result["same_account_execution_attestation"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "failure",
        "timeout",
        "partial",
        "unavailable",
        "exit",
        "bool_exit",
        "future",
        "stale",
        "replay",
        "binding",
    ],
)
def test_failed_observations_hold(tmp_path, mutation):
    plan = bundle(tmp_path)
    item = plan["checks"][0]
    path = tmp_path / item["path"]
    row = json.loads(path.read_bytes())
    if mutation == "missing":
        path.unlink()
    else:
        if mutation in ("failure", "timeout", "unavailable"):
            row["status"] = mutation.upper()
        elif mutation == "partial":
            row["coverage"] = "PARTIAL"
        elif mutation == "exit":
            row["exit_code"] = 2
        elif mutation == "bool_exit":
            row["exit_code"] = False
        elif mutation in ("future", "stale"):
            row["observed_at"] = 2000 if mutation == "future" else 999
        elif mutation == "replay":
            row["run_id"] = "old"
        else:
            row["artifact_digests"] = {}
        item["sha256"] = save(path, row)
    assert run(tmp_path, plan)["status"] == "HOLD"


@pytest.mark.parametrize("name", ["source.txt", "output.txt", "tests.json"])
def test_post_check_modification_or_deletion_holds(tmp_path, name):
    plan = bundle(tmp_path)
    (tmp_path / name).write_text("changed after inspection")
    assert run(tmp_path, plan)["status"] == "HOLD"
    (tmp_path / name).unlink()
    assert run(tmp_path, plan)["status"] == "HOLD"


@pytest.mark.parametrize("kind", REQUIRED)
def test_omitted_required_check_holds(tmp_path, kind):
    plan = bundle(tmp_path, kind)
    plan["checks"].pop()
    assert run(tmp_path, plan)["status"] == "HOLD"


def test_plan_pin_replay_and_freshness(tmp_path):
    plan = bundle(tmp_path)
    assert run(tmp_path, plan, now=1061)["status"] == "HOLD"
    assert run(tmp_path, plan, run_id="another-run")["status"] == "HOLD"
    pin = save(tmp_path / "plan.json", plan)
    (tmp_path / "plan.json").write_text("{}")
    assert (
        inspect_handoff(tmp_path, tmp_path / "plan.json", pin, "fresh-run", 1002)["status"]
        == "HOLD"
    )


def test_independent_review_required(tmp_path):
    plan = bundle(tmp_path, "accounting")
    review = next(c for c in plan["checks"] if c["id"] == "review")
    row = json.loads((tmp_path / review["path"]).read_bytes())
    row["producer"] = "writer"
    review["sha256"] = save(tmp_path / review["path"], row)
    assert run(tmp_path, plan)["status"] == "HOLD"


def test_missing_source_and_conflicting_amount_hold(tmp_path):
    plan = bundle(tmp_path, "accounting")
    plan["artifacts"] = [a for a in plan["artifacts"] if a["role"] != "source"]
    assert run(tmp_path, plan)["status"] == "HOLD"
    plan = bundle(tmp_path, "accounting")
    item = next(c for c in plan["checks"] if c["id"] == "reconciliation")
    row = json.loads((tmp_path / item["path"]).read_bytes())
    row["status"] = "AMOUNT_MISMATCH"
    item["sha256"] = save(tmp_path / item["path"], row)
    assert run(tmp_path, plan)["status"] == "HOLD"


@pytest.mark.parametrize("bad", ["../outside", "/etc/passwd", "./source.txt", "source.txt//x"])
def test_path_escape_holds(tmp_path, bad):
    plan = bundle(tmp_path)
    plan["artifacts"][0]["path"] = bad
    assert run(tmp_path, plan)["status"] == "HOLD"


def test_external_symlink_holds(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    plan = bundle(root)
    outside = tmp_path / "outside"
    outside.write_bytes((root / "source.txt").read_bytes())
    (root / "source.txt").unlink()
    (root / "source.txt").symlink_to(outside)
    assert run(root, plan)["status"] == "HOLD"


def test_duplicate_keys_hold(tmp_path):
    bundle(tmp_path)
    raw = b'{"schema":"hyodo.handoff-plan/v1","schema":"hyodo.handoff-plan/v1"}'
    (tmp_path / "plan.json").write_bytes(raw)
    assert (
        inspect_handoff(tmp_path, tmp_path / "plan.json", sha(raw), "fresh-run", 1002)["status"]
        == "HOLD"
    )


@pytest.mark.parametrize("where", ["plan", "artifact", "check", "observation"])
def test_unrecognized_failure_fields_hold(tmp_path, where):
    plan = bundle(tmp_path)
    if where == "plan":
        plan["errors"] = ["unresolved"]
    elif where == "artifact":
        plan["artifacts"][0]["unreadable"] = True
    elif where == "check":
        plan["checks"][0]["timed_out"] = True
    else:
        item = plan["checks"][0]
        row = json.loads((tmp_path / item["path"]).read_bytes())
        row["errors"] = ["security scan failed"]
        item["sha256"] = save(tmp_path / item["path"], row)
    assert run(tmp_path, plan)["status"] == "HOLD"


def test_whitespace_reviewer_alias_holds(tmp_path):
    plan = bundle(tmp_path, "accounting")
    item = next(c for c in plan["checks"] if c["id"] == "review")
    row = json.loads((tmp_path / item["path"]).read_bytes())
    row["producer"] = "writer "
    item["sha256"] = save(tmp_path / item["path"], row)
    assert run(tmp_path, plan)["status"] == "HOLD"


def test_fifo_artifact_holds_without_blocking(tmp_path):
    import os
    import subprocess
    import sys

    plan = bundle(tmp_path)
    pin = save(tmp_path / "plan.json", plan)
    (tmp_path / "source.txt").unlink()
    os.mkfifo(tmp_path / "source.txt")
    script = (
        "from pathlib import Path; from hyodo.handoff import inspect_handoff; "
        f"r=inspect_handoff(Path({str(tmp_path)!r}),Path({str(tmp_path / 'plan.json')!r}),"
        f"{pin!r},'fresh-run',1002); assert r['status']=='HOLD'"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, timeout=3)
    assert result.returncode == 0, result.stderr


def test_cli_persists_hold_if_final_reinspection_fails(tmp_path, monkeypatch):
    import time

    from typer.testing import CliRunner

    import hyodo.handoff as module
    from hyodo.cli.main import app

    plan = bundle(tmp_path)
    plan["created_at"] = time.time() - 2
    for item in plan["checks"]:
        row = json.loads((tmp_path / item["path"]).read_bytes())
        row["observed_at"] = time.time() - 1
        item["sha256"] = save(tmp_path / item["path"], row)
    pin = save(tmp_path / "plan.json", plan)
    actual = module.inspect_handoff
    calls = []

    def inspect(*args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            (tmp_path / "output.txt").write_text("changed at final check")
        return actual(*args, **kwargs)

    monkeypatch.setattr(module, "inspect_handoff", inspect)
    receipt = tmp_path / "receipt.json"
    result = CliRunner().invoke(
        app,
        [
            "handoff",
            "--root",
            str(tmp_path),
            "--plan",
            str(tmp_path / "plan.json"),
            "--plan-sha256",
            pin,
            "--run-id",
            "fresh-run",
            "--receipt",
            str(receipt),
        ],
    )
    assert result.exit_code == 2, result.output
    assert json.loads(result.output)["status"] == "HOLD"
    assert json.loads(receipt.read_bytes())["status"] == "HOLD"
