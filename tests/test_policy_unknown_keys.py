"""Fail-closed regression: unknown policy.toml keys must never silently weaken policy.

Golden hostile fixture (issue #505): a typo such as ``allowed_toolz`` was
previously ignored, so the intended allowlist never applied and the policy
checker could return ALLOW. All four cases below pin the corrected behavior.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest
from hyodo.policy import PolicyConfigError, load_policy_config, try_load_policy

runner = CliRunner()


def _write_policy(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".hyodo" / "policy.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _event(tool: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "unknown-key-run",
        "ts": "2026-09-25T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": tool,
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": []},
    }


def _run_policy_check(tmp_path: Path) -> object:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(_event({"name": "evil_unlisted_tool", "paths": [], "urls": []})),
        encoding="utf-8",
    )
    return runner.invoke(
        app,
        ["policy", "check", "--file", str(event_path), "--root", str(tmp_path), "--json"],
    )


# --- A: misspelled allowlist at the root must fail closed -----------------

TYPO_ALLOWLIST_POLICY = """schema = "hyodo.policy/v1"
allowed_toolz = ["search"]
"""


def test_unknown_root_key_typo_rejected(tmp_path: Path):
    policy = _write_policy(tmp_path, TYPO_ALLOWLIST_POLICY)
    with pytest.raises(PolicyConfigError, match="allowed_toolz"):
        load_policy_config(policy)
    cfg, error_code = try_load_policy(policy)
    assert cfg is None
    assert error_code == "policy_invalid"


def test_unknown_root_key_typo_names_the_offending_key(tmp_path: Path):
    policy = _write_policy(tmp_path, TYPO_ALLOWLIST_POLICY)
    with pytest.raises(PolicyConfigError) as excinfo:
        load_policy_config(policy)
    # The offending key must always appear; a did-you-mean hint is optional DX.
    assert "allowed_toolz" in str(excinfo.value)


def test_unknown_root_key_never_surfaces_allow_in_cli(tmp_path: Path):
    _write_policy(tmp_path, TYPO_ALLOWLIST_POLICY)
    result = _run_policy_check(tmp_path)
    assert result.exit_code != 0
    assert "ALLOW" not in result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "UNOBSERVED"
    assert payload["reason"] == "policy_invalid"
    assert payload["exit_code"] == 2


# --- B: an unknown deny-shaped key is equally rejected --------------------


def test_unknown_deny_key_rejected(tmp_path: Path):
    policy = _write_policy(
        tmp_path,
        """schema = "hyodo.policy/v1"
deny_pattern = ["*"]
""",
    )
    with pytest.raises(PolicyConfigError, match="deny_pattern"):
        load_policy_config(policy)
    _, error_code = try_load_policy(policy)
    assert error_code == "policy_invalid"

    result = _run_policy_check(tmp_path)
    assert result.exit_code != 0
    assert "ALLOW" not in result.output


# --- C: unknown keys inside supported nested tables -----------------------


def test_unknown_nested_web_key_rejected(tmp_path: Path):
    policy = _write_policy(
        tmp_path,
        """schema = "hyodo.policy/v1"

[web]
allow_non_gt = true
""",
    )
    with pytest.raises(PolicyConfigError, match="allow_non_gt"):
        load_policy_config(policy)

    result = _run_policy_check(tmp_path)
    assert result.exit_code != 0
    assert "ALLOW" not in result.output


@pytest.mark.parametrize(
    ("table", "key"),
    [
        ("trust", "max_lvl"),
        ("ephemeral", "phash_distance_threshhold"),
    ],
)
def test_unknown_nested_keys_rejected(tmp_path: Path, table: str, key: str):
    policy = _write_policy(
        tmp_path,
        f'schema = "hyodo.policy/v1"\n\n[{table}]\n{key} = 1\n',
    )
    with pytest.raises(PolicyConfigError, match=key):
        load_policy_config(policy)


# --- D: valid v1 policies keep existing semantics --------------------------

VALID_FULL_POLICY = """schema = "hyodo.policy/v1"
max_steps = 7
allowed_tools = ["search", "web_fetch"]
blocked_path_globs = ["**/.env"]
require_declared_paths = true
require_mission_prompt = true
ask_tools = ["mcp__custom"]
ask_threshold = 2

[web]
allowed_domains = ["api.example.com", "*.trusted.dev"]
allow_non_get = true
allow_credential_paths = true

[trust]
max_level = 2

[ephemeral]
phash_distance_threshold = 5
"""


def test_valid_v1_policy_still_loads_with_existing_semantics(tmp_path: Path):
    policy = _write_policy(tmp_path, VALID_FULL_POLICY)
    cfg = load_policy_config(policy)
    assert cfg.max_steps == 7
    assert cfg.allowed_tools == ("search", "web_fetch")
    assert cfg.blocked_path_globs == ("**/.env",)
    assert cfg.require_declared_paths is True
    assert cfg.require_mission_prompt is True
    assert cfg.ask_tools == ("mcp__custom",)
    assert cfg.ask_threshold == 2
    assert cfg.web is not None
    assert cfg.web.allowed_domains == ("api.example.com", "*.trusted.dev")
    assert cfg.web.allow_non_get is True
    assert cfg.web.allow_credential_paths is True
    assert cfg.trust is not None
    assert cfg.trust.max_level == 2
    assert cfg.ephemeral is not None
    assert cfg.ephemeral.phash_distance_threshold == 5


def test_minimal_v1_policy_still_loads(tmp_path: Path):
    policy = _write_policy(tmp_path, 'schema = "hyodo.policy/v1"\n')
    cfg = load_policy_config(policy)
    assert cfg.allowed_tools is None
    assert cfg.web is None
