"""TDD for Stage 2 package 2-D: `hyodo eye capture|verify` (ephemeral visual evidence).

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-stage2-design.md,
Package 2-D, plus its seven test-plan rows (search "| 2-D |").
"""

from __future__ import annotations

import json
import struct
import zlib
from types import SimpleNamespace

from typer.testing import CliRunner

from hyodo import eye
from hyodo.cli.main import app
from hyodo.events import read_agent_events, validate_event
from hyodo.policy import (
    _BUILTIN_SUPPLY_CHAIN_TOOLS,
    POLICY_SCHEMA_ID,
    EphemeralPolicy,
    PolicyConfig,
    PolicyConfigError,
    TrustPolicy,
    evaluate_policy,
    load_policy_config,
)
from hyodo.policy_trust import grant_policy_trust

runner = CliRunner()


# --- fixtures -------------------------------------------------------------


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _make_png(width: int, height: int, fill=(30, 60, 90)) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(height):
        raw += b"\x00" + bytes(fill) * width
    idat = zlib.compress(raw)
    return sig + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def _bare_policy(trust: TrustPolicy | None = None, ephemeral: EphemeralPolicy | None = None):
    return PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=None,
        allowed_tools=None,
        blocked_path_globs=(),
        trust=trust,
        ephemeral=ephemeral,
    )


def _install_fake_capture(monkeypatch, image_bytes: bytes | None):
    """Bypass the real BYOM tool: pretend a command is configured and make
    running it write *image_bytes* to the chosen output path."""
    monkeypatch.setattr(eye, "load_capture_command", lambda root: ["FAKE", "{out}"])

    def _fake_run(argv):
        from pathlib import Path

        out_path = Path(argv[-1])
        if image_bytes is not None:
            out_path.write_bytes(image_bytes)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(eye, "run_capture_command", _fake_run)


def _no_sleep(_seconds):
    return None


# --- data model / validate_event ------------------------------------------


def test_supply_chain_tools_constant_includes_eye_capture():
    assert "eye.capture" in _BUILTIN_SUPPLY_CHAIN_TOOLS


def test_pre_2d_event_has_ephemeral_null():
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e1",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "hyodo",
    }
    ok, reasons, normalized = validate_event(raw)
    assert ok, reasons
    assert normalized["meta"]["ephemeral"] is None


def test_malformed_phash_fails_validate_event_before_any_capture():
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e1",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "hyodo",
        "meta": {
            "tags": ["eye-capture"],
            "ephemeral": {
                "ttl_s": 5,
                "phash_algo": "dct64",
                "phash": "DEADBEEF",  # uppercase, wrong length -> invalid
                "destroyed_at": None,
                "kept": False,
            },
        },
    }
    ok, reasons, normalized = validate_event(raw)
    assert not ok
    assert "invalid_field:meta.ephemeral.phash" in reasons
    assert normalized is None


def test_valid_ephemeral_meta_round_trips():
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e1",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "hyodo",
        "meta": {
            "tags": ["eye-capture"],
            "ephemeral": {
                "ttl_s": 5,
                "phash_algo": "dct64",
                "phash": "a1b2c3d4e5f60718",
                "destroyed_at": None,
                "kept": False,
            },
        },
    }
    ok, reasons, normalized = validate_event(raw)
    assert ok, reasons
    assert normalized["meta"]["ephemeral"]["phash"] == "a1b2c3d4e5f60718"


def test_null_phash_allowed_with_unsupported_flag():
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e1",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "hyodo",
        "meta": {
            "tags": ["eye-capture"],
            "ephemeral": {
                "ttl_s": 5,
                "phash_algo": "dct64",
                "phash": None,
                "destroyed_at": None,
                "kept": False,
                "unsupported": True,
            },
        },
    }
    ok, reasons, normalized = validate_event(raw)
    assert ok, reasons
    assert normalized["meta"]["ephemeral"]["phash"] is None
    assert normalized["meta"]["ephemeral"]["unsupported"] is True


# --- policy: trust ladder ---------------------------------------------------


def _tool_call_event(tool_name="eye.capture"):
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e1",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "hyodo",
        "tool": {"name": tool_name},
    }
    ok, _reasons, normalized = validate_event(raw)
    assert ok
    return normalized


def test_eye_capture_unconditionally_produces_eye_capture_external_variable(tmp_path):
    event = _tool_call_event()
    decision = evaluate_policy(event, _bare_policy(), observed_steps=0, root=tmp_path)
    assert "eye_capture" in decision.external_variables


def test_trust_level_1_stays_ask(tmp_path):
    event = _tool_call_event()
    decision = evaluate_policy(event, _bare_policy(), observed_steps=0, root=tmp_path)
    assert decision.decision == "ASK"


def test_trust_level_2_does_not_soften_eye_capture_to_allow(tmp_path):
    event = _tool_call_event()
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 2, by="human:test")
    decision = evaluate_policy(event, policy, observed_steps=0, root=tmp_path)
    assert decision.decision != "ALLOW"


def test_trust_level_3_softens_eye_capture_to_allow(tmp_path):
    event = _tool_call_event()
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")
    decision = evaluate_policy(event, policy, observed_steps=0, root=tmp_path)
    assert decision.decision == "ALLOW"


# --- policy: [ephemeral] config parsing ------------------------------------


def test_ephemeral_config_parses_threshold(tmp_path):
    path = tmp_path / "policy.toml"
    path.write_text(
        'schema = "hyodo.policy/v1"\n\n[ephemeral]\nphash_distance_threshold = 7\n',
        encoding="utf-8",
    )
    cfg = load_policy_config(path)
    assert cfg.ephemeral is not None
    assert cfg.ephemeral.phash_distance_threshold == 7


def test_ephemeral_config_absent_is_none(tmp_path):
    path = tmp_path / "policy.toml"
    path.write_text('schema = "hyodo.policy/v1"\n', encoding="utf-8")
    cfg = load_policy_config(path)
    assert cfg.ephemeral is None


def test_ephemeral_config_rejects_bad_threshold(tmp_path):
    path = tmp_path / "policy.toml"
    path.write_text(
        'schema = "hyodo.policy/v1"\n\n[ephemeral]\nphash_distance_threshold = 999\n',
        encoding="utf-8",
    )
    try:
        load_policy_config(path)
        raised = False
    except PolicyConfigError:
        raised = True
    assert raised


# --- eye.py: load_capture_command ------------------------------------------


def test_load_capture_command_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HYODO_EYE_COMMAND", json.dumps(["screencapture", "-x", "{out}"]))
    command = eye.load_capture_command(tmp_path)
    assert command == ["screencapture", "-x", "{out}"]


def test_load_capture_command_from_config(monkeypatch, tmp_path):
    monkeypatch.delenv("HYODO_EYE_COMMAND", raising=False)
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "config.toml").write_text(
        'schema = "hyodo.config/v1"\n\n[eye]\ncommand = ["cp", "src.png", "{out}"]\n',
        encoding="utf-8",
    )
    command = eye.load_capture_command(tmp_path)
    assert command == ["cp", "src.png", "{out}"]


def test_load_capture_command_absent_is_none(monkeypatch, tmp_path):
    monkeypatch.delenv("HYODO_EYE_COMMAND", raising=False)
    assert eye.load_capture_command(tmp_path) is None


# --- eye.capture(): the seven 2-D spec rows ---------------------------------


def test_capture_no_tool_configured_exits_2_eye_tool_absent(monkeypatch, tmp_path):
    monkeypatch.delenv("HYODO_EYE_COMMAND", raising=False)
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")
    result = eye.capture(tmp_path, policy, ttl_s=0, sleep=_no_sleep)
    assert result.decision == "UNOBSERVED"
    assert result.rule_id == "eye_tool_absent"
    assert result.exit_code == 2


def test_capture_trust_level_1_and_2_stay_ask_level_3_is_allow(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))

    level1_policy = _bare_policy()
    r1 = eye.capture(tmp_path, level1_policy, ttl_s=0, sleep=_no_sleep)
    assert r1.decision == "ASK"
    assert r1.exit_code == 3

    tmp2 = tmp_path / "lvl2"
    tmp2.mkdir()
    policy2 = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp2, 2, by="human:test")
    r2 = eye.capture(tmp2, policy2, ttl_s=0, sleep=_no_sleep)
    assert r2.decision == "ASK"
    assert r2.exit_code == 3

    tmp3 = tmp_path / "lvl3"
    tmp3.mkdir()
    policy3 = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp3, 3, by="human:test")
    r3 = eye.capture(tmp3, policy3, ttl_s=0, sleep=_no_sleep)
    assert r3.decision == "ALLOW"
    assert r3.exit_code == 0


def test_capture_produces_two_events_second_carries_destroyed_at_and_same_phash(
    monkeypatch, tmp_path
):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")

    result = eye.capture(tmp_path, policy, ttl_s=0, sleep=_no_sleep)
    assert result.decision == "ALLOW"

    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    capture_events = [e for e in events if e.get("meta", {}).get("tags") == ["eye-capture"]]
    destroy_events = [e for e in events if e.get("meta", {}).get("tags") == ["eye-destroy"]]
    assert len(capture_events) == 1
    assert len(destroy_events) == 1
    cap_eph = capture_events[0]["meta"]["ephemeral"]
    dest_eph = destroy_events[0]["meta"]["ephemeral"]
    assert cap_eph["destroyed_at"] is None
    assert dest_eph["destroyed_at"] is not None
    assert cap_eph["phash"] == dest_eph["phash"]
    assert destroy_events[0]["parent_event_id"] == capture_events[0]["event_id"]


def test_keep_below_trust_2_is_deny_no_capture(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    policy = _bare_policy()  # trust None -> level 1
    result = eye.capture(tmp_path, policy, ttl_s=0, keep=True, sleep=_no_sleep)
    assert result.decision == "DENY"
    assert result.rule_id == "eye_keep_insufficient_trust"
    assert result.exit_code == 1
    events, _corrupt = read_agent_events(tmp_path)
    assert events == []


def test_keep_at_trust_2_sets_kept_true_destroyed_at_null_ledger_write_required(
    monkeypatch, tmp_path
):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 2, by="human:test")
    result = eye.capture(tmp_path, policy, ttl_s=0, keep=True, yes=True, sleep=_no_sleep)
    assert result.decision == "ALLOW"
    assert result.kept is True
    assert result.destroyed_at is None
    assert result.ledger_write_required is True

    events, _corrupt = read_agent_events(tmp_path)
    capture_events = [e for e in events if e.get("meta", {}).get("tags") == ["eye-capture"]]
    assert capture_events[0]["meta"]["ephemeral"]["kept"] is True
    assert capture_events[0]["meta"]["ephemeral"]["destroyed_at"] is None
    destroy_events = [e for e in events if e.get("meta", {}).get("tags") == ["eye-destroy"]]
    assert destroy_events == []


def test_simulated_deletion_failure_records_evidence_destruction_failed(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")

    from pathlib import Path

    def _raise_unlink(self):
        raise OSError("simulated deletion failure")

    monkeypatch.setattr(Path, "unlink", _raise_unlink)

    result = eye.capture(tmp_path, policy, ttl_s=0, sleep=_no_sleep)
    assert result.exit_code == 2
    assert result.rule_id == "evidence_destruction_failed"

    events, _corrupt = read_agent_events(tmp_path)
    failed = [e for e in events if e.get("meta", {}).get("tags") == ["evidence_destruction_failed"]]
    assert len(failed) == 1
    assert failed[0]["meta"]["ephemeral"]["kept"] is True
    assert failed[0]["meta"]["ephemeral"]["destroyed_at"] is None


def test_unsupported_image_format_exits_2_but_still_destroys(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, b"not a real image at all, just garbage bytes")
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")

    result = eye.capture(tmp_path, policy, ttl_s=0, sleep=_no_sleep)
    assert result.decision == "UNOBSERVED"
    assert result.rule_id == "eye_image_unsupported"
    assert result.exit_code == 2
    assert result.phash is None
    assert result.destroyed_at is not None  # destruction still proven

    events, _corrupt = read_agent_events(tmp_path)
    capture_events = [e for e in events if e.get("meta", {}).get("tags") == ["eye-capture"]]
    assert capture_events[0]["meta"]["ephemeral"]["phash"] is None
    assert capture_events[0]["meta"]["ephemeral"]["unsupported"] is True


def test_verify_never_prints_percentage_or_probability(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")
    eye.capture(tmp_path, policy, ttl_s=0, sleep=_no_sleep)
    events, _corrupt = read_agent_events(tmp_path)
    capture_event = next(e for e in events if e.get("meta", {}).get("tags") == ["eye-capture"])

    (tmp_path / ".hyodo").mkdir(exist_ok=True)
    (tmp_path / ".hyodo" / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\n\n[trust]\nmax_level = 3\n',
        encoding="utf-8",
    )
    cli_result = runner.invoke(
        app,
        [
            "eye",
            "verify",
            "--against",
            capture_event["event_id"],
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert "%" not in cli_result.stdout
    assert "probability" not in cli_result.stdout.lower()


# --- CLI ---------------------------------------------------------------


def test_cli_capture_default_ask_exit_3(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    result = runner.invoke(app, ["eye", "capture", "--ttl", "0", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["decision"] == "ASK"


def test_cli_capture_yes_at_trust_3_allows(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8))
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\n\n[trust]\nmax_level = 3\n',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    result = runner.invoke(app, ["eye", "capture", "--ttl", "0", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "ALLOW"
    assert payload["digest"] is not None
    assert payload["phash"] is not None


def test_cli_verify_same_screen(monkeypatch, tmp_path):
    fixed_png = _make_png(8, 8, fill=(1, 2, 3))
    _install_fake_capture(monkeypatch, fixed_png)
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\n\n[trust]\nmax_level = 3\n',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")

    capture_result = runner.invoke(
        app, ["eye", "capture", "--ttl", "0", "--root", str(tmp_path), "--json"]
    )
    assert capture_result.exit_code == 0
    capture_payload = json.loads(capture_result.stdout)

    verify_result = runner.invoke(
        app,
        [
            "eye",
            "verify",
            "--against",
            capture_payload["capture_event_id"],
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert verify_result.exit_code == 0
    verify_payload = json.loads(verify_result.stdout)
    assert verify_payload["verdict"] == "same screen"
    assert verify_payload["distance"] == 0


def test_cli_verify_different_screen(monkeypatch, tmp_path):
    _install_fake_capture(monkeypatch, _make_png(8, 8, fill=(1, 2, 3)))
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\n\n[trust]\nmax_level = 3\n',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    capture_result = runner.invoke(
        app, ["eye", "capture", "--ttl", "0", "--root", str(tmp_path), "--json"]
    )
    capture_payload = json.loads(capture_result.stdout)

    _install_fake_capture(monkeypatch, _make_png(8, 8, fill=(250, 5, 5)))
    verify_result = runner.invoke(
        app,
        [
            "eye",
            "verify",
            "--against",
            capture_payload["capture_event_id"],
            "--phash-threshold",
            "0",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert verify_result.exit_code == 0
    verify_payload = json.loads(verify_result.stdout)
    assert verify_payload["verdict"] == "different screen"


def test_cli_verify_algo_mismatch_exits_1(tmp_path):
    from hyodo.events import append_agent_event

    fake_event = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "old-event",
        "run_id": "r1",
        "ts": "2026-01-01T00:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "hyodo",
        "parent_event_id": None,
        "evidence_refs": [],
        "tool": {"name": None, "args_digest": None, "paths": [], "method": None, "urls": []},
        "io": {"input_digest": None, "output_digest": None, "bytes_in": 0, "bytes_out": 0},
        "policy": {
            "decision": None,
            "rule_id": None,
            "reason": "unevaluated",
            "evaluated_by": None,
        },
        "meta": {
            "model": None,
            "tags": ["eye-capture"],
            "ephemeral": {
                "ttl_s": 5,
                "phash_algo": "dct64",
                "phash": "a1b2c3d4e5f60718",
                "destroyed_at": None,
                "kept": False,
            },
        },
    }
    # Simulate a future algorithm by hand-editing the stored value on disk
    # (validate_event only accepts "dct64" today, so this models drift).
    append_agent_event(tmp_path, fake_event)
    import json as _json

    from hyodo.events import AGENT_EVENTS_RELATIVE_PATH

    path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    lines = path.read_text(encoding="utf-8").splitlines()
    rewritten = _json.loads(lines[0])
    rewritten["meta"]["ephemeral"]["phash_algo"] = "dct64-v2"
    path.write_text(_json.dumps(rewritten) + "\n", encoding="utf-8")

    result = runner.invoke(
        app, ["eye", "verify", "--against", "old-event", "--root", str(tmp_path), "--json"]
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["reason"] == "phash_algo_mismatch"


def test_cli_verify_missing_event_exits_1(tmp_path):
    result = runner.invoke(
        app, ["eye", "verify", "--against", "nope", "--root", str(tmp_path), "--json"]
    )
    assert result.exit_code == 1
