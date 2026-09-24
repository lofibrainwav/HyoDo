"""Verification-matrix cells the hostile-clone gauntlet does not cover.

The gauntlet attacks a fresh clone. These cases cover the other columns of
the 4.21.7 matrix: stale state, an operator upgrading with pre-4.21.7 files
still in the checkout (existing HOME), and the interactive local path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import typer

import hyodo.cli.main as cli_main
import hyodo.gates as gates
from hyodo.continuity import measure_continuity
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH, append_agent_event, validate_event
from hyodo.exceptions import (
    EXCEPTIONS_APPROVED,
    SCAN_EXCEPTIONS_RELATIVE_PATH,
    load_scan_exceptions,
)
from hyodo.gates import (
    GATES_TRUST_RELATIVE_PATH,
    SCHEMA_ID,
    GatesConfig,
    UserGate,
    compute_gate_set_fingerprint,
    resolve_gate_trust,
    run_user_gates,
)
from hyodo.ledger_origin import ORIGIN_DIVERGED, ledger_origin


def _event(actor_id: str) -> dict:
    ok, reasons, normalized = validate_event(
        {
            "schema_version": "hyodo.agent-event/v1",
            "event_id": f"e-{actor_id}",
            "run_id": f"r-{actor_id}",
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


# --- stale -------------------------------------------------------------------


def test_ledger_edited_after_hyodo_wrote_it_is_diverged_not_ready(tmp_path: Path) -> None:
    for actor in ("hook:a", "hook:b"):
        assert append_agent_event(tmp_path, _event(actor))
    assert measure_continuity(tmp_path)["status"] == "READY"

    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.write_text(ledger.read_text(encoding="utf-8").replace("hook:b", "hook:z"))

    assert ledger_origin(tmp_path, AGENT_EVENTS_RELATIVE_PATH) == ORIGIN_DIVERGED
    receipt = measure_continuity(tmp_path)
    assert receipt["status"] != "READY"
    assert "agent_events_origin_diverged" in receipt["reasons"]


# --- existing HOME: upgrading with pre-4.21.7 files in the checkout ----------


def test_upgrade_with_legacy_checkout_receipt_asks_again_then_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An honest operator's old in-checkout approval is not honored; one new
    interactive approval restores the normal flow, and the legacy file stays
    reported as ignored rather than deleted."""
    marker = tmp_path / "ran.txt"
    probe = f"import pathlib; pathlib.Path({str(marker)!r}).write_text('ok')"
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(name="g", pillar="truth", command=(sys.executable, "-c", probe), timeout=10),
        ),
    )
    legacy = tmp_path / GATES_TRUST_RELATIVE_PATH
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        json.dumps(
            {
                "schema": "hyodo.gates-trust/v1",
                "approved": {compute_gate_set_fingerprint(config): {"via": "prompt"}},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(gates, "_is_noninteractive", lambda: True)
    assert resolve_gate_trust(config, tmp_path).approved is False
    assert not marker.exists()

    monkeypatch.setattr(gates, "_is_noninteractive", lambda: False)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    results = run_user_gates(config, tmp_path)
    assert results[0].status == "PASS"
    assert marker.exists()

    monkeypatch.setattr(gates, "_is_noninteractive", lambda: True)
    decision = resolve_gate_trust(config, tmp_path)
    assert decision.approved is True
    assert "checkout-local .hyodo/gates-trust.json ignored" in decision.reason
    assert legacy.exists()


# --- interactive local: scan exception approval -------------------------------


def _write_exceptions(root: Path) -> None:
    path = root / SCAN_EXCEPTIONS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'schema = "hyodo.scan-exceptions/v1"\n\n'
        "[[safety_exceptions]]\n"
        'path = "fixtures/**"\n'
        'rule = "dangerous_command/git_push_force"\n'
        'reason = "detection fixture"\n',
        encoding="utf-8",
    )


def _force_terminal(monkeypatch: pytest.MonkeyPatch, answer: str) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)


def test_interactive_exception_approval_applies_that_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_exceptions(tmp_path)
    _force_terminal(monkeypatch, "y")

    with pytest.raises(typer.Exit) as exit_info:
        cli_main._approve_scan_exceptions_interactively(tmp_path)

    assert exit_info.value.exit_code == 0
    assert load_scan_exceptions(tmp_path).status == EXCEPTIONS_APPROVED


def test_declined_exception_approval_leaves_them_withheld(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_exceptions(tmp_path)
    _force_terminal(monkeypatch, "n")

    with pytest.raises(typer.Exit) as exit_info:
        cli_main._approve_scan_exceptions_interactively(tmp_path)

    assert exit_info.value.exit_code == 2
    assert load_scan_exceptions(tmp_path).status != EXCEPTIONS_APPROVED


def test_exception_approval_is_refused_in_ci_even_with_a_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_exceptions(tmp_path)
    _force_terminal(monkeypatch, "y")
    monkeypatch.setenv("CI", "true")

    with pytest.raises(typer.Exit) as exit_info:
        cli_main._approve_scan_exceptions_interactively(tmp_path)

    assert exit_info.value.exit_code == 2
    assert load_scan_exceptions(tmp_path).status != EXCEPTIONS_APPROVED
