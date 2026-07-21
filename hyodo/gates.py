"""Bring-Your-Own-Gates: absorb a user's existing quality tools into HyoDo.

HyoDo does not reinvent linters, type checkers, or test runners. Instead a
checkout can register its own commands in ``.hyodo/gates.toml`` (schema
``hyodo.gates/v1``) and HyoDo will execute them as first-class gates,
attributing each one to a pillar (truth/goodness/beauty/benevolence/hyo/
eternity).

This module is intentionally standalone: it has no dependency on
``hyodo.cli`` so it can be wired into a CLI surface, a library caller, or a
future automation without pulling in Typer/Rich. Every result is an honest,
directly-observed subprocess outcome -- a missing binary is reported as
``SKIP``, never silently upgraded to ``PASS``.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover - py3.10 checkouts without tomllib
    try:
        import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ImportError(
            "hyodo.gates requires Python 3.11+ (stdlib tomllib) or the "
            "'tomli' backport installed for Python 3.10."
        ) from exc

SCHEMA_ID = "hyodo.gates/v1"
VALID_PILLARS = frozenset({"truth", "goodness", "beauty", "benevolence", "hyo", "eternity"})
DEFAULT_TIMEOUT_SECONDS = 120
GATES_CONFIG_RELATIVE_PATH = Path(".hyodo") / "gates.toml"
GATE_MESSAGE_TAIL_CHARS = 200

# A leading token shaped like ``KEY=VALUE`` (POSIX env-prefix assignment) that
# must be separated from the executable when running with shell=False.
_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Argument characters that mark a token as a glob pattern needing expansion.
_GLOB_CHARS = ("*", "?", "[")

_HEADER_COMMENT = (
    "# HyoDo Bring-Your-Own-Gates: absorb your existing tools as command gates.\n"
    "# 仁(benevolence, In)/孝(hyo)/永(eternity, Yeong) pillars are not command\n"
    "# gates -- HyoDo measures them natively from the checkout (see\n"
    "# hyodo/pillars.py). Command gates below are typically\n"
    "# truth/goodness/beauty, absorbed from tools this checkout already runs."
)


class GatesConfigError(ValueError):
    """Raise when ``.hyodo/gates.toml`` exists but fails schema validation."""


@dataclass(frozen=True)
class UserGate:
    """One user-supplied quality gate absorbed from ``.hyodo/gates.toml``."""

    name: str
    pillar: str
    command: tuple[str, ...]
    timeout: int
    # Leading ``KEY=VALUE`` assignments peeled from the command so shell=False
    # can still honor ``VAR=value bin args``. Empty means no env-prefix syntax.
    env: tuple[str, ...] = ()


@dataclass(frozen=True)
class GatesConfig:
    """Parsed and validated ``.hyodo/gates.toml`` contents."""

    schema: str
    gates: tuple[UserGate, ...]


@dataclass(frozen=True)
class UserGateResult:
    """Outcome of executing one absorbed user gate."""

    name: str
    pillar: str
    status: str
    message: str


def load_gates_config(root: Path) -> GatesConfig | None:
    """Load and validate ``.hyodo/gates.toml`` under *root*.

    Returns ``None`` when the file does not exist (Bring-Your-Own-Gates is an
    opt-in feature). Raises `GatesConfigError` for any structural or schema
    problem so a caller never silently runs zero gates while believing it ran
    the user's suite.
    """
    path = root / GATES_CONFIG_RELATIVE_PATH
    if not path.exists():
        return None

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GatesConfigError(f"{path}: could not read file: {exc}") from exc

    try:
        raw = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise GatesConfigError(f"{path}: invalid TOML: {exc}") from exc

    schema = raw.get("schema")
    if schema != SCHEMA_ID:
        raise GatesConfigError(f"{path}: unsupported schema {schema!r}; expected {SCHEMA_ID!r}")

    gates_table = raw.get("gates")
    if not isinstance(gates_table, dict) or not gates_table:
        raise GatesConfigError(f"{path}: no gates defined under [gates.<name>]")

    gates: list[UserGate] = []
    for name, spec in gates_table.items():
        gates.append(_parse_gate_spec(path, name, spec))

    return GatesConfig(schema=schema, gates=tuple(gates))


def _parse_gate_spec(path: Path, name: str, spec: Any) -> UserGate:
    if not isinstance(spec, dict):
        raise GatesConfigError(f"{path}: gate {name!r} must be a table")

    pillar = spec.get("pillar")
    if pillar not in VALID_PILLARS:
        raise GatesConfigError(
            f"{path}: gate {name!r} has invalid pillar {pillar!r}; "
            f"expected one of {sorted(VALID_PILLARS)}"
        )

    command = spec.get("command")
    if isinstance(command, str) and command.strip():
        tokens: list[str] = shlex.split(command)
    elif isinstance(command, list) and command and all(isinstance(part, str) for part in command):
        tokens = list(command)
    else:
        raise GatesConfigError(
            f"{path}: gate {name!r} is missing a valid 'command' "
            "(non-empty string or array of strings)"
        )

    # Peel leading KEY=VALUE assignments off the command. With shell=False the
    # subprocess module would otherwise treat the first ``KEY=VALUE`` as the
    # executable path (surfacing as ``"<KEY>=value not installed"``). Emulating
    # POSIX ``VAR=value bin args`` means these tokens become an env override
    # and the real executable stays ``command[0]``.
    env_tokens: list[str] = []
    while tokens and _ENV_ASSIGNMENT_RE.match(tokens[0]):
        env_tokens.append(tokens.pop(0))
    if not tokens:
        raise GatesConfigError(
            f"{path}: gate {name!r} command has only env assignments; "
            "missing executable after them"
        )

    command_tuple = tuple(tokens)
    if not command_tuple:
        raise GatesConfigError(f"{path}: gate {name!r} command resolved to zero arguments")

    timeout = spec.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise GatesConfigError(f"{path}: gate {name!r} has invalid timeout {timeout!r}")

    return UserGate(
        name=name,
        pillar=pillar,
        command=command_tuple,
        timeout=timeout,
        env=tuple(env_tokens),
    )


def _tail(text: str | None) -> str:
    return (text or "").strip()[-GATE_MESSAGE_TAIL_CHARS:]


def run_user_gates(config: GatesConfig, root: Path, verbose: bool = False) -> list[UserGateResult]:
    """Execute every gate in *config* against *root* and report honest outcomes."""
    return [_run_one_gate(gate, root, verbose=verbose) for gate in config.gates]


def _expand_glob_args(args: tuple[str, ...], root: Path) -> list[str]:
    """Expand wildcard args relative to *root* (POSIX nullglob=off).

    Only arguments containing ``*``, ``?`` or ``[`` are treated as patterns;
    literal arguments are passed through untouched. Zero matches keep the
    original literal so a stray pattern is surfaced to the underlying tool
    rather than dropped silently.

    ``glob.glob(..., root_dir=...)`` is not a sandbox: an absolute pattern
    (e.g. ``/etc/*``) ignores ``root_dir`` entirely and a ``../`` pattern can
    walk above *root*. Absolute patterns are therefore never expanded (kept
    literal), and relative-pattern matches are filtered to those that resolve
    to a path inside *root* before being accepted.
    """
    resolved_root = root.resolve()
    expanded: list[str] = []
    for arg in args:
        if any(ch in arg for ch in _GLOB_CHARS):
            if os.path.isabs(arg):
                expanded.append(arg)
                continue
            matches = sorted(glob.glob(arg, root_dir=str(root)))
            in_root_matches = [
                match for match in matches if _is_within_root(root, match, resolved_root)
            ]
            expanded.extend(in_root_matches if in_root_matches else [arg])
        else:
            expanded.append(arg)
    return expanded


def _is_within_root(root: Path, match: str, resolved_root: Path) -> bool:
    """Return whether *match* (relative to *root*) resolves inside *root*."""
    resolved_match = (root / match).resolve()
    return resolved_match == resolved_root or resolved_root in resolved_match.parents


def _build_env(env_tokens: tuple[str, ...]) -> dict[str, str] | None:
    """Merge leading ``KEY=VALUE`` assignments onto ``os.environ``.

    An empty tuple means the gate did not use env-prefix syntax; returning
    ``None`` keeps ``subprocess.run`` on its default inherit-parent path so
    pre-existing behavior is byte-for-byte unchanged.
    """
    if not env_tokens:
        return None
    merged = dict(os.environ)
    for token in env_tokens:
        key, _, value = token.partition("=")
        merged[key] = value
    return merged


def _run_one_gate(gate: UserGate, root: Path, *, verbose: bool) -> UserGateResult:
    binary = gate.command[0]
    if shutil.which(binary) is None:
        return UserGateResult(gate.name, gate.pillar, "SKIP", f"{binary} not installed")

    args = _expand_glob_args(gate.command, root)
    env = _build_env(gate.env)

    try:
        completed = subprocess.run(
            args,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=gate.timeout,
            env=env,
            shell=False,
        )
    except FileNotFoundError:
        return UserGateResult(gate.name, gate.pillar, "SKIP", f"{binary} not installed")
    except subprocess.TimeoutExpired:
        return UserGateResult(gate.name, gate.pillar, "FAIL", "timeout")

    if completed.returncode == 0:
        message = _tail(completed.stdout) if verbose else ""
        return UserGateResult(gate.name, gate.pillar, "PASS", message or "ok")

    message = _tail(completed.stderr) or _tail(completed.stdout)
    return UserGateResult(
        gate.name, gate.pillar, "FAIL", message or f"exit code {completed.returncode}"
    )


def _detect_pyproject_gates(root: Path) -> dict[str, dict[str, str]]:
    path = root / "pyproject.toml"
    if not path.exists():
        return {}
    try:
        lowered = path.read_text(encoding="utf-8").lower()
    except OSError:
        return {}

    detected: dict[str, dict[str, str]] = {}
    if "pytest" in lowered:
        detected["pytest"] = {
            "pillar": "goodness",
            "command": "pytest -q",
            "source": "pyproject.toml",
        }
    if "mypy" in lowered:
        detected["mypy"] = {"pillar": "truth", "command": "mypy", "source": "pyproject.toml"}
    if "pyright" in lowered:
        detected["pyright"] = {"pillar": "truth", "command": "pyright", "source": "pyproject.toml"}
    if "ruff" in lowered:
        detected["ruff"] = {"pillar": "beauty", "command": "ruff check", "source": "pyproject.toml"}
    return detected


def _detect_package_json_gates(root: Path) -> dict[str, dict[str, str]]:
    path = root / "package.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return {}

    detected: dict[str, dict[str, str]] = {}
    test_script = scripts.get("test")
    if (
        isinstance(test_script, str)
        and test_script.strip()
        and "no test specified" not in test_script.lower()
    ):
        detected["npm-test"] = {
            "pillar": "goodness",
            "command": "npm test",
            "source": "package.json",
        }
    lint_script = scripts.get("lint")
    if isinstance(lint_script, str) and lint_script.strip():
        detected["npm-lint"] = {
            "pillar": "beauty",
            "command": "npm run lint",
            "source": "package.json",
        }
    return detected


def _detect_tsconfig_gates(root: Path) -> dict[str, dict[str, str]]:
    if not (root / "tsconfig.json").exists():
        return {}
    return {"tsc": {"pillar": "truth", "command": "npx tsc --noEmit", "source": "tsconfig.json"}}


def _detect_go_gates(root: Path) -> dict[str, dict[str, str]]:
    if not (root / "go.mod").exists():
        return {}
    return {
        "go-vet": {"pillar": "truth", "command": "go vet ./...", "source": "go.mod"},
        "go-test": {"pillar": "goodness", "command": "go test ./...", "source": "go.mod"},
    }


def _detect_cargo_gates(root: Path) -> dict[str, dict[str, str]]:
    if not (root / "Cargo.toml").exists():
        return {}
    return {
        "cargo-check": {"pillar": "truth", "command": "cargo check -q", "source": "Cargo.toml"},
        "cargo-test": {"pillar": "goodness", "command": "cargo test -q", "source": "Cargo.toml"},
    }


def _find_makefile(root: Path) -> Path | None:
    for name in ("Makefile", "makefile"):
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def _detect_makefile_gates(root: Path) -> dict[str, dict[str, str]]:
    makefile = _find_makefile(root)
    if makefile is None:
        return {}
    try:
        text = makefile.read_text(encoding="utf-8")
    except OSError:
        return {}

    detected: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("test:"):
            detected["make-test"] = {
                "pillar": "goodness",
                "command": "make test",
                "source": f"{makefile.name} (test: target)",
            }
        elif stripped.startswith("lint:"):
            detected["make-lint"] = {
                "pillar": "beauty",
                "command": "make lint",
                "source": f"{makefile.name} (lint: target)",
            }
    return detected


def detect_project_gates(root: Path) -> dict[str, dict[str, str]]:
    """Scan *root* for existing tool footprints and propose gates to absorb.

    Returns a mapping of ``gate_name -> {"pillar", "command", "source"}``.
    Every entry carries its detection *source* so a human can see why HyoDo
    proposed it. An unrecognized/empty checkout returns an empty mapping --
    detection is honest about finding nothing rather than guessing.
    """
    detected: dict[str, dict[str, str]] = {}
    detected.update(_detect_pyproject_gates(root))
    detected.update(_detect_package_json_gates(root))
    detected.update(_detect_tsconfig_gates(root))
    detected.update(_detect_go_gates(root))
    detected.update(_detect_cargo_gates(root))
    detected.update(_detect_makefile_gates(root))
    return detected


def render_gates_toml(detected: dict[str, Any]) -> str:
    """Render *detected* (as returned by `detect_project_gates`) as schema v1 TOML.

    Uses plain string formatting rather than a TOML writer dependency --
    the output shape is fixed and simple enough that a template is both
    sufficient and dependency-free.
    """
    lines: list[str] = [f'schema = "{SCHEMA_ID}"', "", _HEADER_COMMENT]

    for name in sorted(detected):
        spec = detected[name]
        pillar = spec["pillar"]
        command = spec["command"]
        source = spec.get("source")
        timeout = int(spec.get("timeout", DEFAULT_TIMEOUT_SECONDS))

        lines.append("")
        if source:
            lines.append(f"# detected from: {source}")
        lines.append(f"[gates.{name}]")
        lines.append(f'pillar = "{pillar}"')
        lines.append(f'command = "{command}"')
        lines.append(f"timeout = {timeout}")

    lines.append("")
    return "\n".join(lines)
