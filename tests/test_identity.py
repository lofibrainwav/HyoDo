"""Contract tests for the loopback runtime identity receipt."""

from __future__ import annotations

import json
from pathlib import Path

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.identity import RUNTIME_IDENTITY_SCHEMA_VERSION, build_runtime_identity


def test_identity_distinguishes_missing_ledger_and_connect_state(tmp_path: Path) -> None:
    identity = build_runtime_identity(tmp_path, endpoint="127.0.0.1:9999")

    assert identity["schema_version"] == RUNTIME_IDENTITY_SCHEMA_VERSION
    assert identity["service"] == {
        "name": "hyodo-dashboard",
        "endpoint": "127.0.0.1:9999",
        "http_observed": True,
    }
    assert identity["connect"]["state"] == "ABSENT"
    assert identity["ledger"]["state"] == "ABSENT"
    assert identity["ledger"]["events"] == 0


def test_identity_reports_observed_ledger_and_corruption(tmp_path: Path) -> None:
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir()
    ledger.write_text(
        json.dumps(
            {
                "schema_version": "hyodo.agent-event/v1",
                "event_id": "e1",
                "run_id": "r1",
                "ts": "2026-09-11T00:00:00+00:00",
                "kind": "prompt",
                "actor": "human",
                "step_index": 0,
            }
        )
        + "\nnot-json\n",
        encoding="utf-8",
    )

    identity = build_runtime_identity(tmp_path)

    assert identity["ledger"]["state"] == "OBSERVED"
    assert identity["ledger"]["events"] == 1
    assert identity["ledger"]["corrupt_lines"] == 1
