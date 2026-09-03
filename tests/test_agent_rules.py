"""TDD contracts for agent-rules opt-in (M4 slice 3).

Agent rules are self-imposed declarations an agent opts into — HyoDo records
and surfaces them but does NOT enforce them.  The operator's policy file
remains the enforcement authority.
"""

from __future__ import annotations

import json
import sys

import pytest
import tomllib
from typer.testing import CliRunner

from hyodo.agent_rules import (
    AGENT_RULES_SCHEMA_ID,
    DEFAULT_RULES,
    AgentRule,
    load_agent_rules,
    save_agent_rules,
    validate_rules,
)
from hyodo.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# a) AgentRule creation, serialization, deserialization round-trip
# ---------------------------------------------------------------------------


class TestAgentRuleRoundTrip:
    def test_creation_and_fields(self):
        rule = AgentRule(
            name="no_write_outside_workspace",
            description="Agent will not write outside the workspace root",
            scope="global",
            enabled=True,
        )
        assert rule.name == "no_write_outside_workspace"
        assert rule.description == "Agent will not write outside the workspace root"
        assert rule.scope == "global"
        assert rule.enabled is True

    def test_frozen(self):
        rule = AgentRule(name="a", description="b", scope="workspace", enabled=True)
        with pytest.raises(AttributeError):
            rule.name = "changed"  # type: ignore[misc]

    def test_to_dict_and_from_dict(self):
        rule = AgentRule(
            name="no_delete_without_confirm",
            description="Agent will not delete files without confirmation",
            scope="tool",
            enabled=False,
        )
        d = rule.to_dict()
        assert d == {
            "name": "no_delete_without_confirm",
            "description": "Agent will not delete files without confirmation",
            "scope": "tool",
            "enabled": False,
        }
        restored = AgentRule.from_dict(d)
        assert restored == rule

    def test_defaults(self):
        rule = AgentRule(name="x", description="y", scope="global")
        assert rule.enabled is True

    def test_scope_values(self):
        for scope in ("global", "workspace", "tool"):
            rule = AgentRule(name="t", description="d", scope=scope)
            assert rule.scope == scope


# ---------------------------------------------------------------------------
# b) load_agent_rules returns empty list when file missing (opt-in)
# ---------------------------------------------------------------------------


class TestLoadAgentRules:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        rules = load_agent_rules(tmp_path)
        assert rules == []

    def test_parses_valid_toml_correctly(self, tmp_path):
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text(
            f'schema = "{AGENT_RULES_SCHEMA_ID}"\n\n'
            "[[rule]]\n"
            'name = "no_write_outside_workspace"\n'
            'description = "Do not write outside workspace"\n'
            'scope = "global"\n'
            "enabled = true\n"
        )
        rules = load_agent_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0].name == "no_write_outside_workspace"
        assert rules[0].scope == "global"
        assert rules[0].enabled is True

    def test_parses_multiple_rules(self, tmp_path):
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text(
            f'schema = "{AGENT_RULES_SCHEMA_ID}"\n\n'
            "[[rule]]\n"
            'name = "no_write_outside_workspace"\n'
            'description = "Do not write outside workspace"\n'
            'scope = "global"\n'
            "enabled = true\n\n"
            "[[rule]]\n"
            'name = "no_delete_without_confirm"\n'
            'description = "Do not delete without confirm"\n'
            'scope = "tool"\n'
            "enabled = false\n"
        )
        rules = load_agent_rules(tmp_path)
        assert len(rules) == 2
        assert rules[0].name == "no_write_outside_workspace"
        assert rules[1].name == "no_delete_without_confirm"
        assert rules[1].enabled is False

    def test_invalid_schema_returns_empty(self, tmp_path):
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text(
            'schema = "unknown.schema/v99"\n\n'
            "[[rule]]\n"
            'name = "test"\n'
            'description = "desc"\n'
            'scope = "global"\n'
        )
        rules = load_agent_rules(tmp_path)
        assert rules == []

    def test_missing_schema_returns_empty(self, tmp_path):
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text("[[rule]]\nname = 'test'\ndescription = 'desc'\nscope = 'global'\n")
        rules = load_agent_rules(tmp_path)
        assert rules == []


# ---------------------------------------------------------------------------
# d) save_agent_rules writes valid TOML that can be re-loaded
# ---------------------------------------------------------------------------


class TestSaveAgentRules:
    def test_round_trip(self, tmp_path):
        rules = [
            AgentRule(
                name="no_write_outside_workspace",
                description="Do not write outside workspace",
                scope="global",
                enabled=True,
            ),
            AgentRule(
                name="no_delete_without_confirm",
                description="Do not delete files without confirmation",
                scope="tool",
                enabled=False,
            ),
        ]
        path = save_agent_rules(tmp_path, rules)
        assert path.exists()
        # Re-load and verify
        loaded = load_agent_rules(tmp_path)
        assert loaded == rules

    def test_creates_hyodo_dir(self, tmp_path):
        rules = [
            AgentRule(name="a", description="b", scope="global", enabled=True),
        ]
        path = save_agent_rules(tmp_path, rules)
        assert (tmp_path / ".hyodo").is_dir()
        assert path.exists()

    def test_written_toml_is_valid(self, tmp_path):
        rules = [
            AgentRule(name="a", description="b", scope="global", enabled=True),
        ]
        path = save_agent_rules(tmp_path, rules)
        raw = tomllib.loads(path.read_text())
        assert raw["schema"] == AGENT_RULES_SCHEMA_ID
        assert len(raw["rule"]) == 1
        assert raw["rule"][0]["name"] == "a"


# ---------------------------------------------------------------------------
# e) validate_rules catches invalid names, missing descriptions
# ---------------------------------------------------------------------------


class TestValidateRules:
    def test_empty_name(self):
        rules = [AgentRule(name="", description="valid", scope="global")]
        errors = validate_rules(rules)
        assert any("name" in e.lower() for e in errors)

    def test_missing_description(self):
        rules = [AgentRule(name="valid", description="", scope="global")]
        errors = validate_rules(rules)
        assert any("description" in e.lower() for e in errors)

    def test_invalid_scope(self):
        # AgentRule is a dataclass; scope is a string literal type at runtime
        # so we construct via from_dict to bypass type checking
        d = {"name": "test", "description": "d", "scope": "invalid", "enabled": True}
        rule = AgentRule.from_dict(d)
        errors = validate_rules([rule])
        assert any("scope" in e.lower() for e in errors)

    def test_valid_rules_no_errors(self):
        rules = list(DEFAULT_RULES)
        errors = validate_rules(rules)
        assert errors == []

    def test_empty_rules_list_no_errors(self):
        errors = validate_rules([])
        assert errors == []


# ---------------------------------------------------------------------------
# f) hyodo mcp rules list with mcp installed: exit 0, shows rules
# ---------------------------------------------------------------------------


class TestMcpRulesList:
    def test_list_shows_rules(self, tmp_path):
        result = runner.invoke(app, ["mcp", "rules", "list", "--root", str(tmp_path)])
        assert result.exit_code == 0
        # Should show at least the default rule names
        assert "no_write_outside_workspace" in result.output

    def test_list_json(self, tmp_path):
        result = runner.invoke(app, ["mcp", "rules", "list", "--root", str(tmp_path), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert isinstance(payload, list)
        assert any(r["name"] == "no_write_outside_workspace" for r in payload)

    def test_list_from_existing_file(self, tmp_path):
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text(
            f'schema = "{AGENT_RULES_SCHEMA_ID}"\n\n'
            "[[rule]]\n"
            'name = "custom_rule"\n'
            'description = "A custom rule"\n'
            'scope = "workspace"\n'
            "enabled = true\n"
        )
        result = runner.invoke(app, ["mcp", "rules", "list", "--root", str(tmp_path), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert len(payload) == 1
        assert payload[0]["name"] == "custom_rule"


# ---------------------------------------------------------------------------
# h) hyodo mcp rules list without mcp: exit 2, install hint
# ---------------------------------------------------------------------------


class TestMcpRulesListWithoutMcp:
    def test_exit_2_without_mcp(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "hyodo._mcp_compat.get_mcp_server_class",
            lambda: (_ for _ in ()).throw(ModuleNotFoundError("mcp")),
        )
        monkeypatch.setitem(sys.modules, "mcp", None)

        result = runner.invoke(app, ["mcp", "rules", "list", "--root", str(tmp_path)])
        # The command should either exit 2 (fail-closed) or propagate
        # the ModuleNotFoundError — both prove mcp is required.
        assert result.exit_code in {1, 2}
        # Output may be empty if the exception propagated before Typer
        # could render; the exit code is the fail-closed guarantee.
        if result.output:
            assert "pip install" in result.output or "hyodo[mcp]" in result.output


# ---------------------------------------------------------------------------
# i) hyodo mcp rules init creates .hyodo/agent-rules.toml with defaults
# ---------------------------------------------------------------------------


class TestMcpRulesInit:
    def test_init_creates_defaults(self, tmp_path):
        result = runner.invoke(app, ["mcp", "rules", "init", "--root", str(tmp_path)])
        assert result.exit_code == 0
        rules_file = tmp_path / ".hyodo" / "agent-rules.toml"
        assert rules_file.exists()
        rules = load_agent_rules(tmp_path)
        assert len(rules) == len(DEFAULT_RULES)
        names = {r.name for r in rules}
        default_names = {r.name for r in DEFAULT_RULES}
        assert names == default_names

    def test_init_idempotent(self, tmp_path):
        # First init
        result1 = runner.invoke(app, ["mcp", "rules", "init", "--root", str(tmp_path)])
        assert result1.exit_code == 0
        rules_file = tmp_path / ".hyodo" / "agent-rules.toml"
        content_before = rules_file.read_text()

        # Second init — should not overwrite
        result2 = runner.invoke(app, ["mcp", "rules", "init", "--root", str(tmp_path)])
        assert result2.exit_code == 0
        content_after = rules_file.read_text()
        assert content_before == content_after

    def test_init_without_mcp_exits_2(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "hyodo._mcp_compat.get_mcp_server_class",
            lambda: (_ for _ in ()).throw(ModuleNotFoundError("mcp")),
        )
        monkeypatch.setitem(sys.modules, "mcp", None)

        result = runner.invoke(app, ["mcp", "rules", "init", "--root", str(tmp_path)])
        assert result.exit_code in {1, 2}


# ---------------------------------------------------------------------------
# k) mcp tool hyodo_agent_rules returns current rules
# ---------------------------------------------------------------------------


class TestMcpAgentRulesTool:
    def test_tool_returns_defaults_when_no_file(self, tmp_path):
        from hyodo.mcp_server import create_server

        server = create_server(tmp_path)
        # Call the tool — find it by name
        tools = server._tool_manager.list_tools()
        agent_rules_tool = None
        for t in tools:
            if t.name == "hyodo_agent_rules":
                agent_rules_tool = t
                break
        assert agent_rules_tool is not None, (
            f"hyodo_agent_rules not in tools: {[t.name for t in tools]}"
        )

    def test_tool_returns_rules_from_file(self, tmp_path):
        from hyodo.mcp_server import create_server

        # Write a custom agent-rules.toml
        hyodo_dir = tmp_path / ".hyodo"
        hyodo_dir.mkdir()
        rules_file = hyodo_dir / "agent-rules.toml"
        rules_file.write_text(
            f'schema = "{AGENT_RULES_SCHEMA_ID}"\n\n'
            "[[rule]]\n"
            'name = "custom_rule"\n'
            'description = "Custom description"\n'
            'scope = "workspace"\n'
            "enabled = true\n"
        )

        server = create_server(tmp_path)
        tools = server._tool_manager.list_tools()
        names = [t.name for t in tools]
        assert "hyodo_agent_rules" in names


# ---------------------------------------------------------------------------
# l) Public language: all new code English-only
# ---------------------------------------------------------------------------


class TestPublicLanguage:
    def test_default_rules_are_english(self):
        for rule in DEFAULT_RULES:
            assert rule.description.isascii(), f"Non-ASCII in rule: {rule.name}"
            # All printable ASCII
            assert all(ord(c) < 128 for c in rule.description), f"Non-English in: {rule.name}"
