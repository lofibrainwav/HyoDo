"""Agent-rules opt-in for connecting agents (M4 slice 3).

Agent rules are **self-imposed declarations** — an agent connecting via MCP
opts into them.  HyoDo records and surfaces these declarations but does NOT
enforce them.  The operator's policy file (``.hyodo/policy.toml``) remains
the enforcement authority.

The file format lives at ``.hyodo/agent-rules.toml`` (schema
``hyodo.agent-rules/v1``).  Missing file = opt-in not exercised, never an
error.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]

AGENT_RULES_SCHEMA_ID = "hyodo.agent-rules/v1"
AGENT_RULES_PATH = Path(".hyodo") / "agent-rules.toml"

Scope = Literal["global", "workspace", "tool"]

_VALID_SCOPES: frozenset[str] = frozenset({"global", "workspace", "tool"})


def _toml_escape(value: str) -> str:
    """Escape a string for a TOML basic string."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def _dump_agent_rules_toml(rules: list[AgentRule]) -> str:
    """Serialize agent rules to TOML without requiring a TOML writer.

    The format is simple enough to emit directly:
        schema = "hyodo.agent-rules/v1"

        [[rule]]
        name = "..."
        description = "..."
        scope = "..."
        enabled = true
    """
    lines: list[str] = [f'schema = "{AGENT_RULES_SCHEMA_ID}"']
    for rule in rules:
        lines.append("")
        lines.append("[[rule]]")
        lines.append(f'name = "{_toml_escape(rule.name)}"')
        lines.append(f'description = "{_toml_escape(rule.description)}"')
        lines.append(f'scope = "{_toml_escape(rule.scope)}"')
        lines.append(f"enabled = {'true' if rule.enabled else 'false'}")
    lines.append("")
    return "\n".join(lines)


@dataclass(frozen=True)
class AgentRule:
    """A single self-imposed agent rule declaration."""

    name: str
    description: str
    scope: str  # Scope, but stored as str for TOML fidelity
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (TOML-friendly)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentRule:
        """Deserialize from a plain dict."""
        return cls(
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            scope=str(d.get("scope", "global")),
            enabled=bool(d.get("enabled", True)),
        )


DEFAULT_RULES: frozenset[AgentRule] = frozenset(
    {
        AgentRule(
            name="no_write_outside_workspace",
            description="Agent will not write files outside the workspace root",
            scope="global",
            enabled=True,
        ),
        AgentRule(
            name="no_delete_without_confirm",
            description="Agent will not delete files without explicit confirmation",
            scope="tool",
            enabled=True,
        ),
        AgentRule(
            name="no_network_request_without_policy",
            description="Agent will not make network requests unless policy allows",
            scope="global",
            enabled=True,
        ),
    }
)


def load_agent_rules(root: Path) -> list[AgentRule]:
    """Load agent rules from ``.hyodo/agent-rules.toml`` under *root*.

    Returns an empty list when the file is missing (opt-in, not required).
    Returns an empty list when the file has an unsupported schema.
    """
    path = root / AGENT_RULES_PATH
    if not path.exists():
        return []

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    try:
        raw = tomllib.loads(raw_text)
    except Exception:
        return []

    if not isinstance(raw, dict):
        return []

    schema = raw.get("schema")
    if schema != AGENT_RULES_SCHEMA_ID:
        return []

    rule_dicts = raw.get("rule", [])
    if not isinstance(rule_dicts, list):
        return []

    rules: list[AgentRule] = []
    for item in rule_dicts:
        if not isinstance(item, dict):
            continue
        rules.append(AgentRule.from_dict(item))
    return rules


def save_agent_rules(root: Path, rules: list[AgentRule]) -> Path:
    """Write *rules* to ``.hyodo/agent-rules.toml`` under *root*.

    Creates the ``.hyodo`` directory if needed.  Returns the path written.
    """
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    path = hyodo_dir / "agent-rules.toml"

    toml_text = _dump_agent_rules_toml(rules)
    path.write_text(toml_text, encoding="utf-8")
    return path


def validate_rules(rules: list[AgentRule]) -> list[str]:
    """Return a list of validation errors.  Empty list = valid."""
    errors: list[str] = []
    for i, rule in enumerate(rules):
        if not rule.name or not rule.name.strip():
            errors.append(f"rule[{i}]: name must be a non-empty string")
        if not rule.description or not rule.description.strip():
            errors.append(f"rule[{i}]: description must be a non-empty string")
        if rule.scope not in _VALID_SCOPES:
            errors.append(
                f"rule[{i}]: scope must be one of {sorted(_VALID_SCOPES)}, got {rule.scope!r}"
            )
    return errors
