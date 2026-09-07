"""Developer-experience (DX) signal collection for `hyodo check`.

Deterministic, offline, in-process detection of three onboarding signals
that `hyodo/score_derive.py::_derive_benevolence` already knows how to
consume (`readme_present`, `start_hint_present`, `help_text_present`, under
rule ids `check.readme_present` / `check.start_hint_present` /
`check.help_text_present`). Nothing here shells out or executes a project
binary -- every check is a filesystem read or an in-process import of
HyoDo's own CLI module.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

try:  # Python 3.11+ ships tomllib in the standard library.
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]

# Minimum non-whitespace README size (bytes, UTF-8) to count as "non-empty".
_README_MIN_BYTES = 200

# Project-level start/setup commands recognized as onboarding entry points.
# Order matters only for which evidence string is reported first.
_START_COMMANDS = (
    "hyodo start",
    "npm start",
    "make setup",
    "pip install -e",
    "uv sync",
    "cargo run",
    "docker compose up",
)

# Headings that count as an onboarding section when followed by a code block.
_START_HEADING_RE = re.compile(
    r"^#{1,6}\s*(getting started|quick start|installation)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Files (relative to root, in this priority order) scanned for a start hint.
_START_HINT_CANDIDATES = (
    "README.md",
    "CONTRIBUTING.md",
    "docs/ONBOARDING.md",
    "docs/GETTING_STARTED.md",
)

_USAGE_HINT_RE = re.compile(r"--help|usage:", re.IGNORECASE)


@dataclass(frozen=True)
class DxSignals:
    """Three boolean onboarding signals plus evidence for each."""

    readme_present: bool
    start_hint_present: bool
    help_text_present: bool
    evidence: dict[str, str] = field(default_factory=dict)


def _find_readme(root: Path) -> Path | None:
    """Return the first case-insensitive `readme.*` file directly under root."""
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return None
    candidates = [p for p in entries if p.is_file() and p.name.lower().startswith("readme")]
    if not candidates:
        return None
    # Prefer README.md exactly if present, else the first match alphabetically.
    for candidate in candidates:
        if candidate.name.lower() == "readme.md":
            return candidate
    return candidates[0]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _detect_readme(root: Path) -> tuple[bool, str | None, Path | None]:
    readme = _find_readme(root)
    if readme is None:
        return False, None, None
    text = _read_text(readme)
    if text is None:
        return False, None, readme
    size = len(text.strip().encode("utf-8"))
    if size <= _README_MIN_BYTES:
        return False, f"{readme.name}: only {size} bytes (need > {_README_MIN_BYTES})", readme
    return True, f"{readme.name} ({size} bytes)", readme


def _detect_start_hint(root: Path, readme_path: Path | None) -> tuple[bool, str | None]:
    for relative in _START_HINT_CANDIDATES:
        candidate = readme_path if relative == "README.md" and readme_path else root / relative
        if candidate is None or not candidate.is_file():
            continue
        text = _read_text(candidate)
        if text is None:
            continue
        for command in _START_COMMANDS:
            if command in text:
                return True, f"{candidate.name}: `{command}`"
        heading_match = _START_HEADING_RE.search(text)
        if heading_match and "```" in text[heading_match.end() :]:
            heading = heading_match.group(1)
            return True, f"{candidate.name}: heading '{heading}' followed by a code block"
    return False, None


def _load_toml(path: Path) -> dict | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        return tomllib.loads(text)
    except Exception:  # tomllib.TOMLDecodeError, but be defensive like other loaders here.
        return None


def _load_json(path: Path) -> dict | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        loaded = json.loads(text)
    except Exception:
        return None
    return loaded if isinstance(loaded, dict) else None


def _hyodo_self_check_entrypoint(pyproject: dict) -> str | None:
    """Return the entry point target if this project is HyoDo itself, else None."""
    project = pyproject.get("project")
    if not isinstance(project, dict) or project.get("name") != "hyodo":
        return None
    scripts = project.get("scripts")
    if not isinstance(scripts, dict):
        return None
    target = scripts.get("hyodo")
    if not isinstance(target, str) or ":" not in target:
        return None
    module, _, _attr = target.partition(":")
    if not module.startswith("hyodo"):
        return None
    return target


def _check_hyodo_help_text(target: str) -> tuple[bool, str]:
    """Import HyoDo's own Typer app in-process and confirm commands carry help.

    Only ever called against HyoDo's own entry point (module path starts
    with `hyodo`) -- never a foreign project's binary, and never via
    subprocess.
    """
    module_name, _, attr_name = target.partition(":")
    try:
        import importlib

        module = importlib.import_module(module_name)
        app = getattr(module, attr_name)
        commands = getattr(app, "registered_commands", None)
        if not commands:
            return False, f"entrypoint:{module_name} (no registered commands found)"
        missing = []
        for command in commands:
            help_text = command.help
            if not help_text and command.callback is not None:
                help_text = command.callback.__doc__
            if not help_text or not help_text.strip():
                missing.append(command.name or getattr(command.callback, "__name__", "?"))
        if missing:
            return False, f"entrypoint:{module_name} ({len(missing)} command(s) missing help)"
        return True, f"entrypoint:{module_name} ({len(commands)} commands with help)"
    except Exception as exc:  # defensive: import must never crash the collector
        return False, f"entrypoint:{module_name} (import failed: {exc})"


def _detect_help_text(root: Path, readme_path: Path | None) -> tuple[bool, str | None]:
    pyproject_path = root / "pyproject.toml"
    pyproject = _load_toml(pyproject_path) if pyproject_path.is_file() else None

    self_target = _hyodo_self_check_entrypoint(pyproject) if pyproject else None
    if self_target is not None:
        ok, evidence = _check_hyodo_help_text(self_target)
        return ok, evidence

    entry_point_name: str | None = None
    if pyproject is not None:
        scripts = pyproject.get("project", {})
        scripts = scripts.get("scripts") if isinstance(scripts, dict) else None
        if isinstance(scripts, dict) and scripts:
            entry_point_name = next(iter(scripts))

    if entry_point_name is None:
        package_json_path = root / "package.json"
        package_json = _load_json(package_json_path) if package_json_path.is_file() else None
        if package_json is not None and package_json.get("bin"):
            bin_field = package_json["bin"]
            entry_point_name = (
                next(iter(bin_field)) if isinstance(bin_field, dict) else package_json.get("name")
            )

    if entry_point_name is None:
        cargo_toml_path = root / "Cargo.toml"
        cargo_toml = _load_toml(cargo_toml_path) if cargo_toml_path.is_file() else None
        if cargo_toml is not None:
            bins = cargo_toml.get("bin")
            if isinstance(bins, list) and bins:
                first = bins[0]
                if isinstance(first, dict) and "name" in first:
                    entry_point_name = first["name"]

    if entry_point_name is None:
        return False, None

    # Foreign project: entry point exists. Also require a README/usage mention
    # of `--help` (never execute the project's own binary to find out).
    readme_text = _read_text(readme_path) if readme_path else None
    if readme_text and _USAGE_HINT_RE.search(readme_text):
        return True, f"entrypoint:{entry_point_name} + README usage/--help mention"
    return False, f"entrypoint:{entry_point_name} found, but no README usage/--help mention"


def collect_dx_signals(root: Path) -> DxSignals:
    """Collect the three onboarding/DX signals for *root*, deterministically.

    Never executes a subprocess or an arbitrary project binary: readme and
    start-hint detection are pure filesystem reads and regex matches;
    help-text detection either imports HyoDo's own CLI module in-process
    (only when *root* is the HyoDo checkout itself) or looks for a README
    usage mention alongside a foreign project's declared entry point.
    """
    evidence: dict[str, str] = {}

    readme_ok, readme_evidence, readme_path = _detect_readme(root)
    if readme_evidence:
        evidence["readme_present"] = readme_evidence

    start_ok, start_evidence = _detect_start_hint(root, readme_path)
    if start_evidence:
        evidence["start_hint_present"] = start_evidence

    help_ok, help_evidence = _detect_help_text(root, readme_path)
    if help_evidence:
        evidence["help_text_present"] = help_evidence

    return DxSignals(
        readme_present=readme_ok,
        start_hint_present=start_ok,
        help_text_present=help_ok,
        evidence=evidence,
    )
