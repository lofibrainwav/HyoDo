"""CLI exit-contract tests for policy ASK and UNOBSERVED decisions."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest

runner = CliRunner()


def _event(tool: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "cli-policy-run",
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": tool,
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": []},
    }


def _write_event(tmp_path: Path, event: dict[str, object]) -> Path:
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event), encoding="utf-8")
    return path


def _write_policy(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".hyodo" / "policy.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_policy_check_ask_exits_three_and_serializes_measurement(tmp_path: Path):
    policy = _write_policy(
        tmp_path,
        """schema = "hyodo.policy/v1"

[web]
allowed_domains = ["allowed.example.com"]
""",
    )
    event = _write_event(
        tmp_path,
        _event(
            {
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "method": "GET",
                "urls": [{"domain": "unlisted.example.com", "path": "/v1"}],
            }
        ),
    )
    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event),
            "--config",
            str(policy),
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 3, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "ASK"
    assert payload["exit_code"] == 3
    assert payload["external_variables"]


def test_event_record_ask_exits_three_but_records_audit_event(tmp_path: Path):
    policy = _write_policy(
        tmp_path,
        """schema = "hyodo.policy/v1"

[web]
allowed_domains = ["allowed.example.com"]
""",
    )
    event = _write_event(
        tmp_path,
        _event(
            {
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "method": "GET",
                "urls": [{"domain": "unlisted.example.com", "path": "/v1"}],
            }
        ),
    )
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event),
            "--root",
            str(tmp_path),
            "--policy",
            str(policy),
            "--json",
        ],
    )
    assert result.exit_code == 3, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "ASK"
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    assert ledger.exists()
    assert '"decision": "ASK"' in ledger.read_text(encoding="utf-8")


def test_event_record_policy_unobserved_exits_two_and_records_measurement(tmp_path: Path):
    policy = _write_policy(
        tmp_path,
        """schema = "hyodo.policy/v1"
ask_tools = ["send_email"]

[trust]
max_level = 3
""",
    )
    event = _write_event(
        tmp_path,
        _event({"name": "send_email", "args_digest": None, "paths": []}),
    )
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event),
            "--root",
            str(tmp_path),
            "--policy",
            str(policy),
            "--json",
        ],
    )
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "UNOBSERVED"
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    assert ledger.exists()
    assert '"decision": "UNOBSERVED"' in ledger.read_text(encoding="utf-8")


def test_policy_check_missing_policy_remains_unobserved_exit_two(tmp_path: Path):
    event = _write_event(
        tmp_path,
        _event({"name": "search", "args_digest": None, "paths": []}),
    )
    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event),
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 2
    assert json.loads(result.output)["decision"] == "UNOBSERVED"
