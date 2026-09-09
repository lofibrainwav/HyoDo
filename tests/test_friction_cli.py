"""Installed CLI tests for the local-only Friction Contribution surface."""

from __future__ import annotations

import json
import stat
from pathlib import Path

from click.testing import Result
from typer.testing import CliRunner

from hyodo.cli.dispatch import app
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.friction import FRICTION_EXPORT_RELATIVE_PATH, FRICTION_STATE_RELATIVE_PATH

runner = CliRunner()


def _write_event(root: Path) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "private-event-id",
        "run_id": "private-run-id",
        "ts": "2026-09-08T12:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "agent",
        "actor_id": "private-seat",
        "parent_event_id": None,
        "evidence_refs": ["gate:test@abcdef0"],
        "tool": {
            "name": "private.tool",
            "paths": ["/private/customer/payment.py"],
            "method": "PATCH",
            "urls": [],
        },
        "io": {
            "input_text": "PROMPT SECRET",
            "output_text": "CUSTOMER SOURCE CODE",
        },
        "policy": {
            "decision": "ALLOW",
            "rule_id": "local-rule",
            "reason": "private reason",
            "evaluated_by": "hyodo.policy/v1",
        },
        "meta": {"model": "claude-private-build", "tags": ["task:code_change", "retry"]},
    }
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")


def _json_output(result: Result) -> dict[str, object]:
    return json.loads(result.output)


def test_dispatcher_preserves_existing_commands_and_adds_friction_help():
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "friction" in help_result.output
    assert "check" in help_result.output
    assert "safe" in help_result.output
    assert "event" in help_result.output


def test_status_defaults_off_and_transport_disabled(tmp_path: Path):
    result = runner.invoke(app, ["friction", "status", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = _json_output(result)
    assert payload["enabled"] is False
    assert payload["state"] == "default_off"
    assert payload["network_consent"] is False
    assert payload["network_transport"] == "disabled"
    assert payload["nothing_transmitted"] is True


def test_on_requires_explicit_noninteractive_confirmation(tmp_path: Path):
    result = runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 1
    payload = _json_output(result)
    assert payload["nothing_transmitted"] is True
    assert not (tmp_path / FRICTION_STATE_RELATIVE_PATH).exists()


def test_on_yes_then_off_changes_local_state_only(tmp_path: Path):
    enabled = runner.invoke(
        app,
        ["friction", "on", "--root", str(tmp_path), "--yes", "--json"],
    )
    assert enabled.exit_code == 0
    enabled_payload = _json_output(enabled)
    assert enabled_payload["enabled"] is True
    assert enabled_payload["network_consent"] is False
    assert enabled_payload["network_transport"] == "disabled"

    status = runner.invoke(app, ["friction", "status", "--root", str(tmp_path), "--json"])
    assert status.exit_code == 0
    assert _json_output(status)["enabled"] is True

    disabled = runner.invoke(app, ["friction", "off", "--root", str(tmp_path), "--json"])
    assert disabled.exit_code == 0
    disabled_payload = _json_output(disabled)
    assert disabled_payload["enabled"] is False
    assert disabled_payload["network_consent"] is False


def test_preview_never_echoes_raw_content_identifiers_or_paths(tmp_path: Path):
    _write_event(tmp_path)
    result = runner.invoke(
        app,
        ["friction", "preview", "--root", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0
    payload = _json_output(result)
    assert payload["nothing_transmitted"] is True
    assert payload["network_transport"] == "disabled"
    assert len(payload["contributions"]) == 1
    serialized = result.output
    for forbidden in (
        "private-event-id",
        "private-run-id",
        "private-seat",
        "/private/customer/payment.py",
        "PROMPT SECRET",
        "CUSTOMER SOURCE CODE",
        "private.tool",
        "local-rule",
        "private reason",
        "2026-09-08T12:00:00+00:00",
        "claude-private-build",
    ):
        assert forbidden not in serialized
    contribution = payload["contributions"][0]
    assert contribution["task_class"] == "code_change"
    assert contribution["risk_bucket"] == "medium"
    assert contribution["provider_class"] == "anthropic"
    assert contribution["outcome"] == "pass"


def test_preview_run_id_filters_locally_but_does_not_echo_filter(tmp_path: Path):
    _write_event(tmp_path)
    result = runner.invoke(
        app,
        [
            "friction",
            "preview",
            "--root",
            str(tmp_path),
            "--run-id",
            "private-run-id",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "private-run-id" not in result.output
    assert _json_output(result)["observation"]["runs_observed"] == 1


def test_contract_is_strict_and_has_no_identity_fields():
    result = runner.invoke(app, ["friction", "contract", "--json"])
    assert result.exit_code == 0
    schema = _json_output(result)
    assert schema["additionalProperties"] is False
    properties = schema["properties"]
    for forbidden in ("run_id", "event_id", "actor_id", "timestamp", "prompt", "path"):
        assert forbidden not in properties


def test_export_requires_enabled_state_and_never_writes_when_disabled(tmp_path: Path):
    result = runner.invoke(
        app,
        ["friction", "export", "--root", str(tmp_path), "--yes", "--json"],
    )
    assert result.exit_code == 1
    assert _json_output(result)["reason"] == "export_disabled: run friction on first"
    assert not (tmp_path / FRICTION_EXPORT_RELATIVE_PATH).exists()


def test_export_requires_yes_in_noninteractive_mode(tmp_path: Path):
    runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--yes"])
    result = runner.invoke(app, ["friction", "export", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 1
    assert _json_output(result)["reason"] == "confirmation_required: pass --yes"
    assert not (tmp_path / FRICTION_EXPORT_RELATIVE_PATH).exists()


def test_export_writes_preview_objects_to_a_separate_private_local_file(tmp_path: Path):
    _write_event(tmp_path)
    runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--yes"])
    preview = runner.invoke(
        app,
        [
            "friction",
            "preview",
            "--root",
            str(tmp_path),
            "--run-id",
            "private-run-id",
            "--json",
        ],
    )
    assert preview.exit_code == 0
    result = runner.invoke(
        app,
        [
            "friction",
            "export",
            "--root",
            str(tmp_path),
            "--run-id",
            "private-run-id",
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0
    export_path = tmp_path / FRICTION_EXPORT_RELATIVE_PATH
    assert export_path.exists()
    assert stat.S_IMODE(export_path.stat().st_mode) == 0o600

    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert set(payload) == {
        "schema",
        "hyodo_version",
        "exported_at",
        "consent",
        "observation",
        "contributions",
        "never_export",
        "authority",
    }
    assert payload["schema"] == "hyodo.friction-export/v1"
    assert payload["consent"] == {
        "enabled": True,
        "network_consent": False,
        "scope": "local_only_v1",
    }
    assert payload["observation"]["network_transport"] == "disabled"
    assert payload["contributions"][0]["schema"] == "hyodo.friction-contribution/v1"
    assert payload["contributions"] == _json_output(preview)["contributions"]
    assert "private-run-id" not in export_path.read_text(encoding="utf-8")
    for forbidden in (
        "private-event-id",
        "private-seat",
        "/private/customer/payment.py",
        "PROMPT SECRET",
        "CUSTOMER SOURCE CODE",
        "claude-private-build",
    ):
        assert forbidden not in export_path.read_text(encoding="utf-8")
    assert not (tmp_path / FRICTION_STATE_RELATIVE_PATH).samefile(export_path)


def test_export_unreadable_ledger_fails_closed_without_creating_file(tmp_path: Path):
    runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--yes"])
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_bytes(b"\xff\xfe")
    result = runner.invoke(
        app,
        ["friction", "export", "--root", str(tmp_path), "--yes", "--json"],
    )
    assert result.exit_code == 2
    assert _json_output(result)["reason"] == "ledger_unreadable"
    assert not (tmp_path / FRICTION_EXPORT_RELATIVE_PATH).exists()


def test_export_honors_explicit_out_path_without_changing_envelope_contract(tmp_path: Path):
    _write_event(tmp_path)
    runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--yes"])
    output_path = tmp_path / "review" / "friction.json"
    result = runner.invoke(
        app,
        [
            "friction",
            "export",
            "--root",
            str(tmp_path),
            "--out",
            str(output_path),
            "--yes",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "hyodo.friction-export/v1"
    assert set(payload["contributions"][0]) == {
        "schema",
        "source_schema",
        "hyodo_version",
        "task_class",
        "risk_bucket",
        "orchestration_pattern",
        "event_count_bucket",
        "parallelism_bucket",
        "retry_bucket",
        "rework_bucket",
        "verification_failure_bucket",
        "human_intervention_bucket",
        "approval_wait_bucket",
        "resource_conflict_bucket",
        "evidence_completeness",
        "outcome",
        "provider_class",
        "source_quality",
    }


def test_export_rejects_state_file_as_output_path(tmp_path: Path):
    _write_event(tmp_path)
    runner.invoke(app, ["friction", "on", "--root", str(tmp_path), "--yes"])
    state_path = tmp_path / FRICTION_STATE_RELATIVE_PATH
    before = state_path.read_text(encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "friction",
            "export",
            "--root",
            str(tmp_path),
            "--out",
            str(state_path),
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 1
    assert _json_output(result)["reason"] == "export_path_conflicts_with_state"
    assert state_path.read_text(encoding="utf-8") == before
