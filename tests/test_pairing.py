"""Tests for the untracked M5-B pairing lifecycle store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.pairing import (
    PAIRING_RELATIVE_PATH,
    PAIRING_SCHEMA_ID,
    PairingState,
    create_pairing,
    load_pairing,
    pairing_state,
    revoke_pairing,
    touch_last_seen,
    verify_token,
)

runner = CliRunner()


def test_pairing_state_missing_file_is_unpaired(tmp_path: Path):
    assert pairing_state(tmp_path) is PairingState.UNPAIRED
    assert load_pairing(tmp_path) is None
    assert verify_token(tmp_path, "any-token") is PairingState.UNPAIRED


def test_create_pairing_round_trips_and_never_writes_the_token(tmp_path: Path):
    record, token = create_pairing(tmp_path)

    assert pairing_state(tmp_path) is PairingState.PAIRED
    loaded = load_pairing(tmp_path)
    assert loaded == record
    assert verify_token(tmp_path, token) is PairingState.PAIRED

    raw = (tmp_path / PAIRING_RELATIVE_PATH).read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload["schema"] == PAIRING_SCHEMA_ID
    assert token not in raw
    assert payload["token_digest"] != token


def test_wrong_token_never_reports_paired(tmp_path: Path):
    create_pairing(tmp_path)

    assert verify_token(tmp_path, "wrong-token") is PairingState.UNPAIRED


def test_revoke_pairing_takes_effect_on_next_verify(tmp_path: Path):
    _record, token = create_pairing(tmp_path)

    revoked = revoke_pairing(tmp_path)

    assert revoked is not None
    assert revoked.revoked_at is not None
    assert pairing_state(tmp_path) is PairingState.REVOKED
    assert verify_token(tmp_path, token) is PairingState.REVOKED


def test_revoke_pairing_is_idempotent(tmp_path: Path):
    create_pairing(tmp_path)
    first = revoke_pairing(tmp_path)
    second = revoke_pairing(tmp_path)

    assert first is not None
    assert second is not None
    assert first.revoked_at == second.revoked_at


def test_revoke_pairing_missing_file_returns_none(tmp_path: Path):
    assert revoke_pairing(tmp_path) is None


def test_touch_last_seen_updates_the_record(tmp_path: Path):
    create_pairing(tmp_path)
    before = load_pairing(tmp_path)
    assert before is not None
    assert before.last_seen_at is None

    touch_last_seen(tmp_path)

    after = load_pairing(tmp_path)
    assert after is not None
    assert after.last_seen_at is not None


def test_touch_last_seen_on_missing_pairing_never_raises(tmp_path: Path):
    touch_last_seen(tmp_path)  # must not raise
    assert load_pairing(tmp_path) is None


def test_create_pairing_keeps_device_id_stable_across_re_pair(tmp_path: Path):
    first, _token1 = create_pairing(tmp_path)
    second, _token2 = create_pairing(tmp_path)

    assert first.device_id == second.device_id
    assert first.workspace_id != second.workspace_id


@pytest.mark.parametrize(
    "payload",
    [
        "{not json",
        json.dumps({"schema": "wrong-schema", "workspace_id": "x"}),
        json.dumps(
            {
                "schema": PAIRING_SCHEMA_ID,
                "workspace_id": "w",
                "device_id": "d",
                "root": "/tmp",
                # token_digest missing
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ),
    ],
)
def test_corrupt_pairing_file_is_unobserved_and_fails_closed(tmp_path: Path, payload: str):
    path = tmp_path / PAIRING_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")

    assert pairing_state(tmp_path) is PairingState.UNOBSERVED
    assert load_pairing(tmp_path) is None
    assert verify_token(tmp_path, "whatever") is PairingState.UNOBSERVED


# ── CLI: hyodo mcp pair / unpair / revoke / pairing show ───────────────────


def test_cli_mcp_pair_prints_the_token_once_and_json_receipt(tmp_path: Path):
    result = runner.invoke(app, ["mcp", "pair", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["exit_code"] == 0
    assert payload["token"]
    assert (tmp_path / PAIRING_RELATIVE_PATH).exists()


def test_cli_mcp_pair_rejects_missing_workspace(tmp_path: Path):
    missing = tmp_path / "missing"

    result = runner.invoke(app, ["mcp", "pair", "--root", str(missing), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["ok"] is False


def test_cli_mcp_pairing_show_reports_paired(tmp_path: Path):
    runner.invoke(app, ["mcp", "pair", "--root", str(tmp_path)])

    result = runner.invoke(app, ["mcp", "pairing", "show", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["state"] == "PAIRED"
    assert payload["ok"] is True
    assert "token" not in payload


def test_cli_mcp_pairing_show_reports_unpaired_exit_2(tmp_path: Path):
    result = runner.invoke(app, ["mcp", "pairing", "show", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["state"] == "UNPAIRED"
    assert payload["ok"] is False


def test_cli_mcp_pairing_show_reports_unobserved_for_corrupt_file(tmp_path: Path):
    path = tmp_path / PAIRING_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    result = runner.invoke(app, ["mcp", "pairing", "show", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["state"] == "UNOBSERVED"


def test_cli_mcp_revoke_marks_the_pairing_revoked(tmp_path: Path):
    runner.invoke(app, ["mcp", "pair", "--root", str(tmp_path)])

    revoke_result = runner.invoke(app, ["mcp", "revoke", "--root", str(tmp_path), "--json"])
    show_result = runner.invoke(app, ["mcp", "pairing", "show", "--root", str(tmp_path), "--json"])

    assert revoke_result.exit_code == 0
    assert json.loads(revoke_result.output)["state"] == "REVOKED"
    assert show_result.exit_code == 2
    assert json.loads(show_result.output)["state"] == "REVOKED"


def test_cli_mcp_unpair_is_the_same_operation_as_revoke(tmp_path: Path):
    runner.invoke(app, ["mcp", "pair", "--root", str(tmp_path)])

    result = runner.invoke(app, ["mcp", "unpair", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.output)["state"] == "REVOKED"


def test_cli_mcp_revoke_without_a_pairing_is_exit_2(tmp_path: Path):
    result = runner.invoke(app, ["mcp", "revoke", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["state"] == "UNPAIRED"
