"""Evidence collectors for the In, Hyo, and Yeong pillars.

Every value produced here is a direct measurement of the target checkout:
stdlib ``ast`` walks over the package source, or append-only local receipts
under ``.hyodo/``. When a source is unavailable the collector reports that
honestly instead of inventing a value, and the dashboard keeps rendering the
pillar as ``Not measured``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

HISTORY_RELATIVE_PATH = Path(".hyodo") / "history.jsonl"
RECEIPT_SCHEMA_VERSION = "hyodo.history-receipt/v1"

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


def _package_trees(root: Path) -> list[ast.Module]:
    trees: list[ast.Module] = []
    for path in sorted((root / "hyodo").rglob("*.py")):
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
    public_defs = 0
    documented = 0
    messageless_raises = 0
    parameters_total = 0
    parameters_with_help = 0
    for tree in _package_trees(root):
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
        "sources": ["ast scan of the checkout's hyodo/ package"],
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
    outbound_import_sites = 0
    non_loopback_bind_literals = 0
    mutating_flags: list[str] = []
    mutating_flags_defaulting_on: list[str] = []
    for tree in _package_trees(root):
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
        "sources": ["ast scan of the checkout's hyodo/ package"],
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

    streak = 0
    all_pass_runs = 0
    runs_with_skipped_gates = 0
    last_non_pass_at = ""
    for entry in reversed(entries):
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
