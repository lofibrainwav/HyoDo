"""Evidence collectors for the In, Hyo, and Yeong pillars.

Every value produced here is a direct measurement of the target checkout:
stdlib ``ast`` walks over the package source, or append-only local receipts
under ``.hyodo/``. When a source is unavailable the collector reports that
honestly instead of inventing a value, and the dashboard keeps rendering the
pillar as ``Not measured``.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

HISTORY_RELATIVE_PATH = Path(".hyodo") / "history.jsonl"
RECEIPT_SCHEMA_VERSION = "hyodo.history-receipt/v2"


def gate_set_fingerprint(gate_names: Iterable[str]) -> str:
    """Return a short, deterministic fingerprint of a gate-name set.

    Payload is ``json.dumps(sorted(names), separators=(",", ":"))`` so names
    that contain JSON metacharacters (including ``|``) cannot collide.
    First 12 hex chars of SHA-256 of the UTF-8 payload. An empty name set is
    still deterministic (hash of ``[]``).
    """
    payload = json.dumps(sorted(gate_names), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _fingerprint_for_receipt_entry(entry: dict[str, Any]) -> str:
    """Resolve the gate-set fingerprint for one history receipt.

    Prefer the stored ``gate_set_fingerprint`` when present (v2+). Legacy
    entries without the field derive the same value from ``gates`` keys so
    streak boundaries remain comparable without rewriting the ledger.
    """
    stored = entry.get("gate_set_fingerprint")
    if isinstance(stored, str) and len(stored) == 12:
        return stored
    gates = entry.get("gates", {})
    names = gates.keys() if isinstance(gates, dict) else ()
    return gate_set_fingerprint(names)


# Outbound-capable modules whose presence in the package would open a
# telemetry or data-exfiltration pathway. http.server (inbound loopback
# serving) is intentionally not in this set.
OUTBOUND_NETWORK_MODULES = {
    "aiohttp",
    "http.client",
    "httpx",
    "requests",
    "socket",
    "urllib.request",
}

# CLI flags that mutate the user's files. Consent means they must default off.
MUTATING_FLAG_NAMES = {"--fix"}

# Built from parts so this module's own sentinel is not counted by its own
# AST scan (ast.parse does not constant-fold string concatenation).
_NON_LOOPBACK_BIND = "0.0" + ".0.0"


_EXCLUDED_TOP_LEVEL_DIRS = {".venv", "venv", "node_modules"}

_ROOT_SCRIPT_SCAN_LIMIT = 50


def _pyproject_project_name(root: Path) -> str | None:
    """Best-effort read of ``[project].name`` from ``pyproject.toml``.

    A minimal line scan (not a full TOML parser) is deliberate: it needs no
    TOML library (``tomllib`` is unavailable on the project's own minimum of
    Python 3.10) and this is a discovery heuristic, not a config loader.
    """
    try:
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return None
    in_project_table = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("["):
            in_project_table = line == "[project]"
            continue
        if not in_project_table:
            continue
        key, sep, value = line.partition("=")
        if not sep or key.strip() != "name":
            continue
        name = value.strip().strip('"').strip("'")
        return name or None
    return None


def _iter_top_level_package_dirs(root: Path) -> list[Path]:
    """Top-level directories that look like Python packages, sorted by name."""
    candidates: list[Path] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name in _EXCLUDED_TOP_LEVEL_DIRS:
            continue
        if (entry / "__init__.py").is_file():
            candidates.append(entry)
    return candidates


def _resolve_scan_target(root: Path) -> tuple[list[Path], str]:
    """Locate the Python files the In/Hyo collectors should scan for *root*.

    Priority: (a) ``root/hyodo`` — the HyoDo checkout itself, preserving the
    original hardcoded behaviour byte-for-byte; (b) a ``src/<name>`` or
    ``<name>`` directory matching ``pyproject.toml``'s ``[project].name``;
    (c) the first top-level directory (sorted, ``.venv``/``node_modules``/
    hidden excluded) that has an ``__init__.py``; (d) up to
    ``_ROOT_SCRIPT_SCAN_LIMIT`` root-level ``*.py`` files. Returns
    ``([], "")`` when no Python code is found anywhere, so callers can be
    honest instead of inventing a measurement.
    """
    hyodo_dir = root / "hyodo"
    if hyodo_dir.is_dir():
        files = sorted(hyodo_dir.rglob("*.py"))
        return files, "ast scan of the checkout's hyodo/ package"

    name = _pyproject_project_name(root)
    if name:
        normalized = name.replace("-", "_")
        for relative in (Path("src") / normalized, Path(normalized)):
            candidate = root / relative
            if candidate.is_dir() and (candidate / "__init__.py").is_file():
                return sorted(candidate.rglob("*.py")), f"ast scan of {relative.as_posix()}"

    package_dirs = _iter_top_level_package_dirs(root)
    if package_dirs:
        candidate = package_dirs[0]
        relative = candidate.relative_to(root)
        return sorted(candidate.rglob("*.py")), f"ast scan of {relative.as_posix()}"

    root_py_files = sorted(p for p in root.glob("*.py") if p.is_file())[:_ROOT_SCRIPT_SCAN_LIMIT]
    if root_py_files:
        return root_py_files, "ast scan of root-level *.py files"

    return [], ""


def _parse_python_files(paths: list[Path]) -> list[ast.Module]:
    trees: list[ast.Module] = []
    for path in paths:
        try:
            trees.append(ast.parse(path.read_text(encoding="utf-8")))
        except (OSError, SyntaxError):
            # An unreadable file is a missing data point, not a zero; the
            # remaining files still produce an honest partial measurement.
            continue
    return trees


def _is_typer_parameter(node: ast.Call) -> bool:
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in {"Option", "Argument"}
        and isinstance(func.value, ast.Name)
        and func.value.id == "typer"
    )


def _is_normal_typer_exit(node: ast.AST) -> bool:
    """Return whether *node* is Typer's argument-free successful CLI exit."""
    return (
        isinstance(node, ast.Call)
        and not node.args
        and not node.keywords
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Exit"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "typer"
    )


def collect_in_evidence(root: Path) -> dict[str, Any]:
    """Measure how kindly the checkout treats the humans who use it."""
    files, source = _resolve_scan_target(root)
    if not files:
        return {"sources": [], "metrics": {}}
    public_defs = 0
    documented = 0
    messageless_raises = 0
    parameters_total = 0
    parameters_with_help = 0
    for tree in _parse_python_files(files):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if not node.name.startswith("_"):
                    public_defs += 1
                    if ast.get_docstring(node):
                        documented += 1
            elif isinstance(node, ast.Raise) and node.exc is not None:
                exc = node.exc
                if not _is_normal_typer_exit(exc) and (
                    isinstance(exc, ast.Name)
                    or (isinstance(exc, ast.Call) and not exc.args and not exc.keywords)
                ):
                    messageless_raises += 1
            elif isinstance(node, ast.Call) and _is_typer_parameter(node):
                parameters_total += 1
                if any(keyword.arg == "help" for keyword in node.keywords):
                    parameters_with_help += 1
    return {
        "sources": [source],
        "metrics": {
            "public_docstring_coverage": {"documented": documented, "public": public_defs},
            "cli_parameters_with_help": {
                "with_help": parameters_with_help,
                "total": parameters_total,
            },
            "messageless_raises": messageless_raises,
        },
    }


def collect_hyo_evidence(root: Path) -> dict[str, Any]:
    """Measure the consent and data-protection posture of the checkout."""
    files, source = _resolve_scan_target(root)
    if not files:
        return {"sources": [], "metrics": {}}
    outbound_import_sites = 0
    non_loopback_bind_literals = 0
    mutating_flags: list[str] = []
    mutating_flags_defaulting_on: list[str] = []
    for tree in _parse_python_files(files):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                outbound_import_sites += sum(
                    1 for alias in node.names if alias.name in OUTBOUND_NETWORK_MODULES
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module in OUTBOUND_NETWORK_MODULES:
                    outbound_import_sites += 1
            elif isinstance(node, ast.Constant) and node.value == _NON_LOOPBACK_BIND:
                non_loopback_bind_literals += 1
            elif isinstance(node, ast.Call) and _is_typer_parameter(node):
                flag_names = {
                    arg.value
                    for arg in node.args
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                }
                matched = sorted(flag_names & MUTATING_FLAG_NAMES)
                if not matched:
                    continue
                mutating_flags.extend(matched)
                default = node.args[0] if node.args else None
                opt_in = isinstance(default, ast.Constant) and default.value is False
                if not opt_in:
                    mutating_flags_defaulting_on.extend(matched)
    return {
        "sources": [source],
        "metrics": {
            "outbound_network_import_sites": outbound_import_sites,
            "non_loopback_bind_literals": non_loopback_bind_literals,
            "mutating_flags": {
                "flags": sorted(set(mutating_flags)),
                "defaulting_on": sorted(set(mutating_flags_defaulting_on)),
            },
        },
    }


def append_history_receipt(root: Path, evidence: dict[str, Any]) -> bool:
    """Append one measurement receipt to the local ledger; never raise."""
    gates = evidence.get("gates", {})
    statuses: dict[str, str] = {}
    for name, gate in gates.items():
        if not isinstance(gate, dict):
            continue
        raw = gate.get("status", "")
        # GateStatus enums must land as their value ("PASS"), not "GateStatus.PASS".
        statuses[name] = str(getattr(raw, "value", raw))
    entry = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "measured_at": evidence.get("measured_at"),
        "gates": statuses,
        # Gate-set fingerprint: streak metrics must not silently continue across
        # a coverage shrink (e.g. 4-gate preset -> trivial single BYOG gate).
        "gate_set_fingerprint": gate_set_fingerprint(statuses.keys()),
    }
    path = root / HISTORY_RELATIVE_PATH
    try:
        path.parent.mkdir(exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return True
    except OSError:
        return False


def collect_yeong_evidence(root: Path) -> dict[str, Any]:
    """Measure durability from the append-only local measurement ledger."""
    path = root / HISTORY_RELATIVE_PATH
    empty: dict[str, Any] = {"sources": [], "metrics": {}}
    if not path.exists():
        return empty
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return empty
    entries: list[dict[str, Any]] = []
    corrupt_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            corrupt_lines += 1
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
        else:
            corrupt_lines += 1
    if not entries:
        return empty

    def executed_all_pass(gates: dict[str, Any]) -> bool:
        """SKIP/UNSUPPORTED gates are unobserved, not failed: they neither
        satisfy nor block all-PASS. A run with zero executed gates never
        counts as all-PASS (no false green from pure skips)."""
        executed = [status for status in gates.values() if status in ("PASS", "FAIL")]
        return bool(executed) and all(status == "PASS" for status in executed)

    # Streak is scoped to the latest gate-set fingerprint. A coverage change
    # (different gate names) ends the streak even if every run is all-PASS.
    latest_fingerprint = _fingerprint_for_receipt_entry(entries[-1])
    streak = 0
    all_pass_runs = 0
    runs_with_skipped_gates = 0
    last_non_pass_at = ""
    for entry in reversed(entries):
        if _fingerprint_for_receipt_entry(entry) != latest_fingerprint:
            break
        if executed_all_pass(entry.get("gates", {})):
            streak += 1
        else:
            break
    for entry in entries:
        gates = entry.get("gates", {})
        if any(status not in ("PASS", "FAIL") for status in gates.values()):
            runs_with_skipped_gates += 1
        if executed_all_pass(gates):
            all_pass_runs += 1
        else:
            last_non_pass_at = str(entry.get("measured_at", ""))
    return {
        "sources": [f"{HISTORY_RELATIVE_PATH} append-only receipts"],
        "metrics": {
            "recorded_runs": len(entries),
            "consecutive_all_pass_runs": streak,
            "all_pass_runs": all_pass_runs,
            "runs_with_skipped_gates": runs_with_skipped_gates,
            "last_non_pass_at": last_non_pass_at,
            "first_recorded_at": str(entries[0].get("measured_at", "")),
            "last_recorded_at": str(entries[-1].get("measured_at", "")),
            "corrupt_lines": corrupt_lines,
        },
    }
