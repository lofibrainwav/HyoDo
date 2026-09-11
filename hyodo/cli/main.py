#!/usr/bin/env python3
"""
HyoDo CLI Main Entry Point

Model-agnostic quality-gate CLI. Works with or without any specific agent UI.
"Model-agnostic" means independent of the AI model or agent UI.
It does not currently mean language-agnostic.

Usage: hyodo [COMMAND] [OPTIONS]

Examples:
    hyodo check              # HyoDo checkout release gates
    hyodo score -t 0.9 -g 0.9 -b 0.9 -i 0.9 -c 0.9
    hyodo safe               # lightweight safety scan
    hyodo safe --strict      # block on high-severity findings
    hyodo trinity "task"     # detailed review checklist
"""

from __future__ import annotations

import ipaddress
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import uuid
import webbrowser
from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import compare_digest, token_urlsafe
from typing import Any
from urllib.parse import parse_qs, urlsplit

import typer
from rich.console import Console
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table

from hyodo import (
    SCORE_FORMULA_LINEAGE,
    SCORE_MODEL_NAME,
    SCORE_PUBLIC_NAME,
    SCORE_SUBSET_NAME,
    __version__,
)
from hyodo.audience import (
    VALID_PROFILES,
    AudienceProfile,
    InvalidAudienceError,
    resolve_audience,
)
from hyodo.audience import (
    write_config as write_audience_config,
)
from hyodo.connect import (
    ALL_TARGETS,
    UNOBSERVED_MESSAGE,
    UNOBSERVED_TARGETS,
    WRITABLE_TARGETS,
    MappedHookEvent,
    check_status,
    load_connect_state,
    map_claude_code_hook_payload,
    plan_target,
    save_connect_state,
    write_target,
)
from hyodo.connect import detect as detect_connect_targets
from hyodo.connector_contract import build_connector_contract
from hyodo.continuity import measure_continuity
from hyodo.dashboard import (
    GRAPH_SCRIPT_SHA256,
    PILLAR_SPECS,
    POLL_SCRIPT_SHA256,
    render_dashboard_html,
    render_graph_html,
)
from hyodo.dx_signals import DxSignals, collect_dx_signals
from hyodo.eval import EvalInputError, run_evaluation
from hyodo.event_graph import render_event_graph_json, validate_event_edges
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    AGENT_EVENTS_RELATIVE_PATH,
    EVENT_ID_CONFLICT,
    EVENT_ID_NEW,
    EVENT_ID_UNOBSERVED,
    append_agent_event,
    check_event_id,
    count_run_events,
    load_event_from_path,
    load_event_from_text,
    read_agent_events,
    strip_full_bodies,
    unevaluated_policy,
    validate_event,
)
from hyodo.exceptions import (
    ScanExceptionsConfig,
    ScanExceptionsConfigError,
    is_general_path_excluded,
    load_scan_exceptions,
)
from hyodo.eye import (
    DEFAULT_TTL_S,
    CaptureResult,
)
from hyodo.eye import (
    capture as run_eye_capture,
)
from hyodo.gates import (
    GATES_CONFIG_RELATIVE_PATH,
    SCHEMA_ID,
    GatesConfigError,
    detect_project_gates,
    load_gates_config,
    render_gates_toml,
    run_user_gates,
)
from hyodo.graph_export import build_graph_export
from hyodo.graph_view import build_actor_rings
from hyodo.host_adapters.codex import map_codex_hook_payload
from hyodo.host_adapters.codex_response import map_codex_permission_response
from hyodo.host_adapters.cursor import map_cursor_hook_payload
from hyodo.host_adapters.cursor_response import map_cursor_permission_response
from hyodo.mcp_config import (
    ALL_HOSTS,
    CHATGPT_UNOBSERVED_MESSAGE,
    DEEP_LINK_HOSTS,
    DEEP_LINK_LABEL,
    MCP_HOSTS,
    UNVERIFIED_FORMAT_LABEL,
    plan_host,
    write_host,
)
from hyodo.mcp_config import (
    detect_hosts as detect_mcp_hosts,
)
from hyodo.orchestration_observation import (
    append_orchestration_observation,
    validate_orchestration_observation,
)
from hyodo.pairing import (
    PAIRING_RELATIVE_PATH,
    PairingState,
    create_pairing,
    load_pairing,
    pairing_state,
    revoke_pairing,
)
from hyodo.phash import phash_distance
from hyodo.pillars import (
    append_history_receipt,
    collect_hyo_evidence,
    collect_in_evidence,
    collect_yeong_evidence,
)
from hyodo.policy import (
    POLICY_RELATIVE_PATH,
    POLICY_SCHEMA_ID,
    PolicyConfig,
    PolicyDecision,
    apply_decision_to_event,
    evaluate_policy,
    try_load_policy,
)
from hyodo.policy_trust import (
    POLICY_TRUST_RELATIVE_PATH,
    default_granted_by,
    effective_trust_level,
    grant_policy_trust,
    load_policy_trust,
    resolve_policy_trust_grant,
)
from hyodo.provenance import resolve_provenance
from hyodo.report import build_report_graph, write_report
from hyodo.safety import run_safety_scan
from hyodo.schema import validate_schema_payload
from hyodo.score_derive import (
    DerivedPillars,
    apply_override,
    derive_pillars,
    geometric_mean_observed,
)
from hyodo.skills import (
    MANIFEST_RELATIVE_PATH as SKILLS_MANIFEST_RELATIVE_PATH,
)
from hyodo.skills import (
    build_ingest_tool,
    build_node_ingest_tool,
    compute_lens,
    load_manifest,
    manifest_entry,
    node_manifest_entry,
    node_rules_for,
    parse_node_retrieval_file,
    parse_skill_rules,
    render_proposal,
    resolve_source,
    save_manifest,
    save_proposal,
    skill_name_for,
    validate_node_retrieval,
)
from hyodo.skills import (
    store_body as store_skill_body,
)
from hyodo.test_integrity import TestIntegrityReport, scan_test_integrity
from hyodo.verdict import explain_decision, render_verdict_line

app = typer.Typer(
    name="hyodo",
    help="HyoDo - model-agnostic AI code quality gates",
    add_completion=True,
)
event_app = typer.Typer(
    name="event",
    help="Agent event ledger (FDE evidence spine; opt-in, not a runtime interceptor)",
    add_completion=False,
)
observation_app = typer.Typer(
    name="observation",
    help="Sidecar orchestration observations (DAG shape; never an agent event)",
    add_completion=False,
)
policy_app = typer.Typer(
    name="policy",
    help="Local policy gate for agent events (ALLOW|DENY; unobserved ≠ ALLOW)",
    add_completion=False,
)
trust_app = typer.Typer(
    name="trust",
    help="Explicit operator grants for policy ASK delegation",
    add_completion=False,
)
schema_app = typer.Typer(
    name="schema",
    help="Deterministic JSON Schema validation for local agent payloads",
    add_completion=False,
)
mcp_app = typer.Typer(
    name="mcp",
    help="Optional local MCP adapter for the HyoDo CLI",
    add_completion=False,
)
rules_app = typer.Typer(
    name="rules",
    help="Agent-rules opt-in declarations",
    add_completion=False,
)
pairing_app = typer.Typer(
    name="pairing",
    help="Read-only pairing status for the M5-B loopback/tailscale bridge",
    add_completion=False,
)
skills_app = typer.Typer(
    name="skills",
    help="Ingest a project's own skills as a lens over the six pillars",
    add_completion=False,
)
# Package 2-C: kept as its own sub-app registration block, deliberately
# small, so a merge with any other lane's CLI edits stays trivial.
graph_app = typer.Typer(
    name="graph",
    help="Evidence-graph export bridge (Package 2-C, no auto-approval)",
    add_completion=False,
)
eye_app = typer.Typer(
    name="eye",
    help="Ephemeral visual evidence: capture, hash, show, destroy -- never store pixels",
    add_completion=False,
)
mcp_app.add_typer(rules_app, name="rules")
mcp_app.add_typer(pairing_app, name="pairing")
app.add_typer(event_app, name="event")
app.add_typer(observation_app, name="observation")
app.add_typer(policy_app, name="policy")
policy_app.add_typer(trust_app, name="trust")
app.add_typer(schema_app, name="schema")
app.add_typer(mcp_app, name="mcp")
app.add_typer(skills_app, name="skills")
app.add_typer(graph_app, name="graph")
app.add_typer(eye_app, name="eye")
console = Console()


class GateStatus(str, Enum):
    """Enumerate the possible outcomes for an individual verification gate."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class GateResult:
    """Store an immutable status and human-readable message for a verification gate."""

    status: GateStatus
    message: str


# hyodo.gates pillar name -> hyodo.dashboard.PILLAR_SPECS key. Both name the
# same six pillars; the dashboard SSOT carries the trilingual (Hanja/Korean/
# English) label, so BYOG output reuses it instead of hardcoding a duplicate.
_PILLAR_SPEC_KEY_BY_GATE_PILLAR = {
    "truth": "jin",
    "goodness": "seon",
    "beauty": "mi",
    "benevolence": "in",
    "hyo": "hyo",
    "eternity": "yeong",
}
_PILLAR_LABELS_BY_SPEC_KEY = {
    key: (hanja, korean, english) for key, hanja, korean, english, _ in PILLAR_SPECS
}


def _trilingual_pillar_label(pillar: str) -> str:
    """Render a `.hyodo/gates.toml` pillar name as Hanja/Korean/English (SSOT: PILLAR_SPECS)."""
    spec_key = _PILLAR_SPEC_KEY_BY_GATE_PILLAR.get(pillar)
    labels = _PILLAR_LABELS_BY_SPEC_KEY.get(spec_key) if spec_key else None
    if labels is None:
        return pillar
    hanja, korean, english = labels
    return f"{hanja} {korean} {english}"


def find_repo_root(start: Path | None = None) -> Path | None:
    """Find a HyoDo repository checkout root from *start* (not always cwd)."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "hyodo").exists():
            return candidate
    return None


def resolve_dashboard_root(start: Path | None = None) -> Path | None:
    """Resolve a directory the dashboard can honestly measure, else ``None``.

    Wider than :func:`find_repo_root` on purpose. That function answers "is
    this a HyoDo package checkout?" and drives ``check`` and built-in preset
    selection, so widening it there would mis-route those. This one answers a
    different question: "can the dashboard collect evidence here?"

    A project that adopted HyoDo through ``hyodo init`` owns
    ``.hyodo/gates.toml``; its gates are already honoured by
    :func:`collect_dashboard_evidence`, so refusing to serve it only hid
    In/Hyo/Yeong from projects that had opted in.

    Pillar collectors stay honest on such targets: when no Python package is
    found they report empty metrics (unobserved) rather than a 0/0 full score.
    """
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    if (current / GATES_CONFIG_RELATIVE_PATH).is_file():
        return current
    return find_repo_root(current)


def resolve_evidence_root(start: Path | None = None) -> Path | None:
    """Resolve an explicit evidence-only root without running project gates.

    This is intentionally separate from :func:`resolve_dashboard_root`: an
    evidence pack is a read-only graph source, not a HyoDo checkout and not a
    BYOG project. The caller must opt into this boundary with
    ``dashboard --evidence-root``.
    """
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    ledger = current / AGENT_EVENTS_RELATIVE_PATH
    return current if ledger.is_file() else None


def resolve_check_target(path: str | None) -> Path:
    """Resolve check target path. Raises FileNotFoundError if missing."""
    raw = path or "."
    target = Path(raw)
    target = target.resolve() if target.is_absolute() else (Path.cwd() / target).resolve()
    if not target.exists():
        raise FileNotFoundError(str(target))
    return target


def _tool_cmd(module: str, *args: str) -> list[str]:
    """Run tooling via the same interpreter that hosts hyodo (venv-safe)."""
    return [sys.executable, "-m", module, *args]


def _module_importable(module: str) -> bool:
    """Return True if `python -m <module>` is available in this interpreter."""
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import importlib.util; raise SystemExit(0 if importlib.util.find_spec({module!r}) else 1)",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return probe.returncode == 0


def _missing_tool_result(tool: str, root: Path | None) -> GateResult:
    """Missing tools: FAIL inside HyoDo checkout; SKIP outside (should not reach)."""
    if root is None:
        return GateResult(GateStatus.SKIP, f"{tool} not installed; skipped (no HyoDo checkout)")
    return GateResult(
        GateStatus.FAIL,
        f"{tool} not found (install: pip install {tool} or hyodo[dev])",
    )


def run_pyright_check(root: Path | None, verbose: bool = False) -> GateResult:
    """Gate 1: Pyright - Truth - Type checking (HyoDo checkout only)."""
    if root is None:
        return GateResult(GateStatus.UNSUPPORTED, "not a HyoDo checkout; typecheck not executed")
    if not _module_importable("pyright"):
        return _missing_tool_result("pyright", root)

    # Pyright otherwise discovers the first `python` on PATH. That can be a
    # different interpreter from the one running HyoDo (for example macOS's
    # system Python when HyoDo is installed in a virtual environment), which
    # makes installed runtime dependencies appear missing.
    cmd = _tool_cmd("pyright", "--pythonpath", sys.executable, "hyodo")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(root))
        if result.returncode == 0:
            return GateResult(GateStatus.PASS, "0 errors, 0 warnings")

        error_count = result.stdout.count("error:") + result.stderr.count("error:")
        warning_count = result.stdout.count("warning:") + result.stderr.count("warning:")
        detail = (result.stdout or result.stderr or "").strip()
        if verbose and detail:
            return GateResult(
                GateStatus.FAIL,
                f"{error_count} errors, {warning_count} warnings\n{detail[:400]}",
            )
        return GateResult(GateStatus.FAIL, f"{error_count} errors, {warning_count} warnings")
    except FileNotFoundError:
        return _missing_tool_result("pyright", root)
    except subprocess.TimeoutExpired:
        return GateResult(GateStatus.FAIL, "timeout (>120s)")
    except Exception as e:
        return GateResult(GateStatus.FAIL, f"exception: {e}")


def run_ruff_check(root: Path | None, fix: bool = False, verbose: bool = False) -> GateResult:
    """Gate 2: Ruff - Beauty - Lint & Format (HyoDo checkout only).

    Runs both ``ruff check`` and ``ruff format --check`` (or format write when
    ``fix=True``). Lint-only success is not a green gate.
    """
    if root is None:
        return GateResult(GateStatus.UNSUPPORTED, "not a HyoDo checkout; lint not executed")
    if not _module_importable("ruff"):
        return _missing_tool_result("ruff", root)

    lint_cmd = _tool_cmd("ruff", "check", "hyodo")
    if fix:
        lint_cmd.append("--fix")
    fmt_cmd = (
        _tool_cmd("ruff", "format", "hyodo")
        if fix
        else _tool_cmd("ruff", "format", "--check", "hyodo")
    )
    try:
        lint = subprocess.run(lint_cmd, capture_output=True, text=True, timeout=60, cwd=str(root))
        fmt = subprocess.run(fmt_cmd, capture_output=True, text=True, timeout=60, cwd=str(root))
        lint_ok = lint.returncode == 0
        fmt_ok = fmt.returncode == 0
        if lint_ok and fmt_ok:
            return GateResult(GateStatus.PASS, "lint + format passed")

        parts: list[str] = []
        if not lint_ok:
            lint_msg = (lint.stdout or lint.stderr or "ruff check failed").strip()
            parts.append(f"lint: {lint_msg[:140]}")
        if not fmt_ok:
            fmt_msg = (fmt.stdout or fmt.stderr or "ruff format failed").strip()
            parts.append(f"format: {fmt_msg[:140]}")
        msg = "; ".join(parts)
        if len(msg) > 200:
            msg = msg[:200] + "..."
        return GateResult(GateStatus.FAIL, msg or "ruff failed")
    except FileNotFoundError:
        return _missing_tool_result("ruff", root)
    except subprocess.TimeoutExpired:
        return GateResult(GateStatus.FAIL, "timeout (>60s)")
    except Exception as e:
        return GateResult(GateStatus.FAIL, f"exception: {e}")


def run_pytest_check(root: Path | None, verbose: bool = False) -> GateResult:
    """Gate 3: pytest - Goodness - Public package tests (HyoDo checkout only)."""
    if root is None:
        return GateResult(GateStatus.UNSUPPORTED, "not a HyoDo checkout; tests not executed")
    if not (root / "tests").exists():
        return GateResult(GateStatus.SKIP, "No tests/ directory in HyoDo checkout")
    if not _module_importable("pytest"):
        return _missing_tool_result("pytest", root)

    cmd = _tool_cmd("pytest", str(root / "tests"), "-q", "--tb=short")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(root))
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "passed" in line.lower():
                    return GateResult(GateStatus.PASS, line.strip())
            return GateResult(GateStatus.PASS, "All tests passed!")

        detail = (result.stdout or result.stderr or "").strip()
        if verbose and detail:
            return GateResult(GateStatus.FAIL, f"exit code {result.returncode}\n{detail[-500:]}")
        summary = detail.splitlines()[-1] if detail else ""
        if summary:
            return GateResult(GateStatus.FAIL, f"exit code {result.returncode}: {summary[:160]}")
        return GateResult(GateStatus.FAIL, f"exit code {result.returncode}")
    except FileNotFoundError:
        return _missing_tool_result("pytest", root)
    except subprocess.TimeoutExpired:
        return GateResult(GateStatus.FAIL, "timeout (>300s)")
    except Exception as e:
        return GateResult(GateStatus.FAIL, f"exception: {e}")


def run_sbom_check(root: Path | None, verbose: bool = False) -> GateResult:
    """Gate 4: SBOM - optional seal (SKIP when script absent, never fake PASS)."""
    if root is None:
        return GateResult(GateStatus.UNSUPPORTED, "not a HyoDo checkout; SBOM not executed")

    sbom_script = root / "scripts" / "generate_sbom.py"
    if not sbom_script.exists():
        return GateResult(GateStatus.SKIP, "SBOM script not found; not executed")

    cmd = [sys.executable, str(sbom_script)]
    # Generating the SBOM builds a wheel + a clean venv (heavier than the lint
    # gates), so it gets a larger budget than the 60s tool gates.
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=str(root))
    except FileNotFoundError:
        return GateResult(GateStatus.SKIP, "python executable not found; SBOM not generated")
    except subprocess.TimeoutExpired:
        return GateResult(GateStatus.SKIP, "SBOM generation timed out (>180s); not generated")
    except OSError as e:  # genuine OS/environment failure — honest SKIP, never a false FAIL
        return GateResult(GateStatus.SKIP, f"SBOM not generated (environment): {e}")
    except Exception as e:  # unexpected error in HyoDo's own invocation path — a real defect
        return GateResult(GateStatus.FAIL, f"SBOM invocation error (unexpected): {e}")

    if result.returncode == 0:
        return GateResult(GateStatus.PASS, "SBOM generated (public surface)")

    detail = (result.stderr.strip() or result.stdout.strip())[:200]
    if result.returncode == 2:
        # A scope violation means the SBOM was generated but is not the public
        # closure — a real defect, so it blocks.
        return GateResult(GateStatus.FAIL, detail or "SBOM scope violation")
    if result.returncode == 3:
        # Exit 3 is the generator's *defined* environment/offline failure: it
        # could not build/install/inventory. Non-blocking, matching the honest
        # absent-script SKIP — never a false FAIL when the SBOM simply could not
        # be produced.
        return GateResult(GateStatus.SKIP, detail or "SBOM not generated (environment)")
    # Any other exit code is an UNEXPECTED generator failure (bug, corrupt output,
    # unhandled exception → exit 1). Surfacing it as FAIL — not a silent SKIP —
    # keeps sec-1's anti-ghost-gate honesty contract.
    return GateResult(
        GateStatus.FAIL, detail or f"SBOM generator failed (exit {result.returncode})"
    )


def _print_gate_result(result: GateResult) -> None:
    if result.status is GateStatus.PASS:
        console.print(f"  [green]PASS {result.message}[/green]")
    elif result.status is GateStatus.FAIL:
        console.print(f"  [red]FAIL {result.message}[/red]")
    elif result.status is GateStatus.SKIP:
        console.print(f"  [yellow]SKIP {result.message}[/yellow]")
    else:
        console.print(f"  [yellow]UNSUPPORTED {result.message}[/yellow]")


def _print_test_integrity_line(report: TestIntegrityReport) -> None:
    """Report-only Phase 1-E line: never affects `check`'s default exit code.

    A project with no discoverable pytest-convention tests is UNOBSERVED, not a
    failure -- the honesty rule that "unenforced is not the same as passing"
    cuts both ways: it is also never silently reported as a clean 0/0.
    """
    if report.total_tests == 0:
        console.print("\n[dim]Test integrity: UNOBSERVED (no pytest-convention tests found)[/dim]")
        return
    console.print(
        f"\nTest integrity: {report.vacuous_tests}/{report.total_tests} tests assert "
        "nothing -- see `hyodo check --json`"
    )


def _dx_signals_gate_result(signals: DxSignals) -> GateResult:
    """Shape `DxSignals` as an advisory Benevolence gate row.

    Never fails `check`: PASS when all three signals were observed, SKIP
    (the existing "advisory, not executed/complete" status) otherwise -- the
    same semantics `check` already uses for gates it does not fully run.
    """
    observed = [
        signals.readme_present,
        signals.start_hint_present,
        signals.help_text_present,
    ]
    names = ("readme", "start-hint", "help-text")
    detail = ", ".join(
        f"{name}={'yes' if ok else 'no'}" for name, ok in zip(names, observed, strict=True)
    )
    if all(observed):
        return GateResult(GateStatus.PASS, detail)
    return GateResult(GateStatus.SKIP, detail)


def _print_dx_signals_line(signals: DxSignals, result: GateResult) -> None:
    """Report-only Benevolence DX-signals line: never affects the exit code."""
    style = "green" if result.status is GateStatus.PASS else "yellow"
    console.print(f"\n[{style}]Benevolence (dx-signals): {result.message}[/{style}]")


def _dx_signals_payload(signals: DxSignals) -> dict[str, Any]:
    """Render `DxSignals` as the `check --json` `dx_signals` object."""
    return {
        "readme_present": signals.readme_present,
        "start_hint_present": signals.start_hint_present,
        "help_text_present": signals.help_text_present,
        "evidence": signals.evidence,
    }


def _test_integrity_payload(report: TestIntegrityReport) -> dict[str, Any]:
    """Render a `TestIntegrityReport` as the `check --json` `test_integrity` object."""
    return {
        "scanned_files": report.scanned_files,
        "total_files": report.total_files,
        "total_tests": report.total_tests,
        "vacuous_tests": report.vacuous_tests,
        "findings": [
            {
                "path": f.path,
                "line": f.line,
                "function": f.function,
                "category": f.category,
                "detail": f.detail,
            }
            for f in report.findings
        ],
    }


def _print_failure_guidance(failures: list[tuple[str, str]]) -> None:
    """Explain failed gates and give consumers a deterministic next action."""
    if not failures:
        return
    console.print("[bold red]Failure details:[/bold red]")
    for name, message in failures:
        console.print(f"  - {name}: {message}")
    console.print("[yellow]Next action: fix the listed gate(s) and re-run hyodo check.[/yellow]")


EVIDENCE_SCHEMA_VERSION = "hyodo.dashboard-evidence/v2"
LOOPBACK_HOST = "127.0.0.1"


def collect_dashboard_evidence(root: Path) -> dict[str, object]:
    """Collect one honest snapshot for the local dashboard.

    Uses `.hyodo/gates.toml` (Bring-Your-Own-Gates, see `hyodo init`) when
    present -- the user's own gate names become the evidence keys -- else the
    built-in HyoDo checkout preset. A malformed gates.toml is surfaced as one
    failing `gates_config` entry rather than silently falling back.
    """
    try:
        gates_config = load_gates_config(root)
    except GatesConfigError as exc:
        gates: dict[str, GateResult] = {
            "gates_config": GateResult(GateStatus.FAIL, f"{GATES_CONFIG_RELATIVE_PATH}: {exc}")
        }
    else:
        if gates_config is not None:
            gates = {
                result.name: GateResult(GateStatus(result.status), result.message)
                for result in run_user_gates(gates_config, root)
            }
        else:
            gates = {
                "typecheck": run_pyright_check(root),
                "lint_format": run_ruff_check(root),
                "tests": run_pytest_check(root),
                "sbom": run_sbom_check(root),
            }
    safety = run_safety_scan(cwd=root)
    safety_source = str(safety["source"])
    # An empty change set gets no risk_score: reporting 0 would read as "scanned, safe".
    # But a bare None cannot tell "the scan never ran" apart from "it ran and had
    # nothing to measure". That ambiguity already misled a consumer, which rendered a
    # scan that had actually run as unobserved. Name the state instead of guessing it.
    safety_measurable = "empty" not in safety_source and "no diff" not in safety_source
    safety_risk: int | None = safety["risk_score"] if safety_measurable else None
    evidence: dict[str, object] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "target": str(root),
        "measured_at": datetime.now(timezone.utc).isoformat(),
        # The portable form: this dict is served over HTTP by `hyodo dashboard`,
        # so it carries commit ids and path digests, never a home directory.
        "provenance": resolve_provenance(root).to_portable_dict(),
        "gates": {name: asdict(result) for name, result in gates.items()},
        "safety": {
            "risk_score": safety_risk,
            # measured       - a real corpus was scored, risk_score is an int
            # no_scan_target - the scan ran and its findings hold, but there was
            #                  nothing to score, so only the number is absent
            "risk_score_state": "measured" if safety_measurable else "no_scan_target",
            "source": safety_source,
            "findings": [asdict(finding) for finding in safety["findings"]],
        },
    }
    # Record this run before reading the ledger so Yeong includes it.
    if not append_history_receipt(root, evidence):
        console.print("[yellow]Could not append .hyodo/history.jsonl receipt.[/yellow]")
    evidence["pillars"] = {
        "in": collect_in_evidence(root),
        "hyo": collect_hyo_evidence(root),
        "yeong": collect_yeong_evidence(root),
    }
    return evidence


def collect_evidence_root_snapshot(root: Path) -> dict[str, object]:
    """Render a graph-only snapshot for an explicit evidence root.

    No gate, safety scan, history receipt, or project inspection runs here.
    Those operations would turn an evidence pack into a new measurement target.
    The graph status is the only observed signal in this mode; the six cards
    remain visibly UNOBSERVED rather than implying checkout health.
    """
    graph = build_report_graph(root)
    graph_status = str(graph.get("status", "UNOBSERVED"))
    graph_message = (
        "Evidence graph is READY; project gates were not executed."
        if graph_status == "READY"
        else f"Evidence graph is {graph_status}; project gates were not executed."
    )
    gates = {
        name: {"status": "UNOBSERVED", "message": "evidence-only root; gate not executed"}
        for name in ("typecheck", "tests", "lint_format", "sbom")
    }
    gates["evidence_graph"] = {"status": graph_status, "message": graph_message}
    empty_pillar = {"metrics": {}, "sources": ["evidence-only root"]}
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "target": str(root),
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "provenance": resolve_provenance(root).to_portable_dict(),
        "gates": gates,
        "safety": {
            "risk_score": None,
            "risk_score_state": "not_executed",
            "source": "evidence-only root; safety not executed",
            "findings": [],
        },
        "pillars": {
            "in": empty_pillar,
            "hyo": empty_pillar,
            "yeong": empty_pillar,
        },
    }


DASHBOARD_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; "
    f"script-src 'sha256-{POLL_SCRIPT_SHA256}' 'sha256-{GRAPH_SCRIPT_SHA256}'; connect-src 'self'"
)


class DashboardState:
    """Thread-safe holder for the latest rendered snapshot."""

    def __init__(
        self, evidence: dict[str, object], *, refresh_token: str = "", interval: int = 0
    ) -> None:
        """Initialize the state with optional local refresh controls."""
        self._lock = threading.Lock()
        self._refresh_token = refresh_token
        self._interval = interval
        self._refreshing = False
        self._refresh_message = "Snapshot ready."
        self._refresh_started_at: str | None = None
        self.update(evidence)

    def _render_locked(self) -> None:
        """Render the page and evidence JSON while the state lock is held."""
        self._page = render_dashboard_html(
            self._evidence,
            refresh_token=self._refresh_token,
            interval=self._interval,
            refreshing=self._refreshing,
            refresh_message=self._refresh_message,
            refresh_started_at=self._refresh_started_at or "",
        ).encode("utf-8")
        self._evidence_json = json.dumps(self._evidence, default=str, sort_keys=True).encode(
            "utf-8"
        )

    def update(self, evidence: dict[str, object]) -> None:
        """Render and atomically replace the dashboard snapshot from evidence."""
        with self._lock:
            self._evidence = evidence
            self._refreshing = False
            self._refresh_message = "Measurement complete."
            self._refresh_started_at = None
            self._render_locked()

    def snapshot(self) -> tuple[bytes, bytes]:
        """Return the current rendered page and serialized evidence snapshot."""
        with self._lock:
            return self._page, self._evidence_json

    def status(self) -> bytes:
        """Return the current refresh state as a small JSON response."""
        with self._lock:
            return json.dumps(
                {
                    "refreshing": self._refreshing,
                    "message": self._refresh_message,
                    "started_at": self._refresh_started_at,
                }
            ).encode("utf-8")

    def begin_refresh(self) -> bool:
        """Mark a manual measurement running unless one is already active."""
        with self._lock:
            if self._refreshing:
                return False
            self._refreshing = True
            self._refresh_message = "Measurement running. This page will update when it finishes."
            self._refresh_started_at = datetime.now(timezone.utc).isoformat()
            self._render_locked()
            return True

    def fail_refresh(self) -> None:
        """Keep the last evidence and expose a refresh failure to the page."""
        with self._lock:
            self._refreshing = False
            self._refresh_message = (
                "Measurement failed; the last successful snapshot is still shown."
            )
            self._refresh_started_at = None
            self._render_locked()


# Only these routes carry evidence read from the loopback board. The HTML
# pages at "/" and "/graph" are never CORS targets (a cross-origin page can
# only read response bodies from these JSON endpoints when the browser
# lets it).
_CORS_ELIGIBLE_PATHS = frozenset({"/api/evidence", "/api/status", "/api/graph", "/api/actor"})


def make_dashboard_handler(
    state: DashboardState,
    refresh: Callable[[], dict[str, object]] | None = None,
    refresh_token: str = "",
    allow_origins: tuple[str, ...] = (),
    root: Path | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Build the loopback request handler serving the current snapshot.

    ``allow_origins`` is an opt-in exact-match CORS allow-list (empty by
    default, matching prior behaviour byte-for-byte: no CORS headers at
    all). No wildcard support — an origin must match one of the configured
    values exactly before ``Access-Control-Allow-Origin`` is echoed back.

    ``root`` is the HyoDo checkout whose ``.hyodo/agent-events.jsonl`` feeds
    the local evidence-graph viewer. Unlike the six-card snapshot above,
    ``GET /graph`` and ``GET /api/graph`` read that ledger live on every
    request via ``build_report_graph`` — the same corrupt/unreadable and
    mission-policy handling as ``hyodo report --format graph`` — instead of
    the cached ``DashboardState`` snapshot, so a paired ``hyodo event
    record`` shows up on the next request without a manual re-measure.
    When ``root`` is omitted, both routes 404 (this handler's behaviour
    before the graph viewer shipped).
    """
    allowed_origins = frozenset(allow_origins)

    class DashboardHandler(BaseHTTPRequestHandler):
        """Serve the dashboard's current loopback snapshot over HTTP."""

        def _path(self) -> str:
            """The request path without its query string (`self.path` carries both)."""
            return urlsplit(self.path).path

        def _resolve(self) -> tuple[bytes, str, int] | None:
            path = self._path()
            if path in ("/graph", "/api/graph"):
                if root is None:
                    return None
                graph = build_report_graph(root)
                if path == "/graph":
                    return (
                        render_graph_html(graph, root=root).encode("utf-8"),
                        "text/html; charset=utf-8",
                        200,
                    )
                return render_event_graph_json(graph).encode("utf-8"), "application/json", 200
            if path == "/api/actor":
                # Package 2-C: actor rings (spec section 5), keyed the same way
                # `build_actor_rows` keys its own `rows` dict (Ruling 3).
                if root is None:
                    return None
                graph = build_report_graph(root)
                rings = build_actor_rings(graph, root)
                query = parse_qs(urlsplit(self.path).query)
                key = query.get("key", [None])[0]
                if key is None or key not in rings:
                    return (
                        json.dumps({"error": "unknown_actor"}).encode("utf-8"),
                        "application/json",
                        404,
                    )
                return json.dumps(rings[key]).encode("utf-8"), "application/json", 200
            page, evidence_json = state.snapshot()
            if path == "/":
                return page, "text/html; charset=utf-8", 200
            if path == "/api/evidence":
                return evidence_json, "application/json", 200
            if path == "/api/status":
                return state.status(), "application/json", 200
            return None

        def _cors_headers(self) -> list[tuple[str, str]]:
            """Return (name, value) CORS header pairs for the current request.

            Empty unless: the path is CORS-eligible, an `Origin` request
            header was sent, and it exactly matches a configured allowed
            origin. No wildcard, no partial/prefix/suffix match.
            """
            if self._path() not in _CORS_ELIGIBLE_PATHS or not allowed_origins:
                return []
            origin = self.headers.get("Origin")
            if not origin or origin not in allowed_origins:
                return []
            return [("Access-Control-Allow-Origin", origin), ("Vary", "Origin")]

        def _send_headers(self, body: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", DASHBOARD_CSP)
            for name, value in self._cors_headers():
                self.send_header(name, value)
            self.end_headers()

        def do_GET(self) -> None:
            """Serve the current page or evidence JSON for a GET request."""
            resolved = self._resolve()
            if resolved is None:
                self.send_error(404, "Not found")
                return
            body, content_type, status = resolved
            self._send_headers(body, content_type, status)
            self.wfile.write(body)

        def do_HEAD(self) -> None:
            """Serve headers for a current page or evidence JSON request."""
            resolved = self._resolve()
            if resolved is None:
                self.send_error(404, "Not found")
                return
            body, content_type, status = resolved
            self._send_headers(body, content_type, status)

        def do_POST(self) -> None:
            """Refresh local evidence only when the server-issued token matches."""
            if self.path != "/api/refresh" or refresh is None:
                self.send_error(404, "Not found")
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400, "Invalid content length")
                return
            if size < 0 or size > 4096:
                self.send_error(413, "Refresh request is too large")
                return
            body = self.rfile.read(min(size, 4096)).decode("utf-8", errors="replace")
            token = parse_qs(body).get("token", [""])[0]
            if not refresh_token or not compare_digest(token, refresh_token):
                self.send_error(403, "Invalid refresh token")
                return
            refresh_callback = refresh
            assert refresh_callback is not None
            if state.begin_refresh():

                def _collect_in_background() -> None:
                    try:
                        state.update(refresh_callback())
                    except Exception:
                        state.fail_refresh()

                threading.Thread(
                    target=_collect_in_background,
                    name="hyodo-dashboard-manual-refresh",
                    daemon=True,
                ).start()
            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", DASHBOARD_CSP)
            self.end_headers()

        def log_message(self, format: str, *_args: object) -> None:
            """Suppress default HTTP request logging for the local dashboard."""
            return

    return DashboardHandler


@app.command()
def dashboard(
    path: str | None = typer.Argument(
        None, help="HyoDo checkout path (defaults to current directory)"
    ),
    port: int = typer.Option(8768, "--port", min=1, max=65535, help="Loopback port"),
    open_browser: bool = typer.Option(
        False, "--open", help="Open the dashboard in the default browser"
    ),
    interval: int = typer.Option(
        0,
        "--interval",
        min=0,
        help="Re-measure every N seconds in the background (0 keeps the snapshot fixed)",
    ),
    allow_origin: list[str] = typer.Option(  # noqa: B008 - typer repeatable-option pattern;
        # ruff's B006/B008 heuristic fires on any `list[...]`-annotated Option default,
        # but typer.Option's default is read once at CLI parse time, never mutated.
        [],
        "--allow-origin",
        help=(
            "Allow this exact Origin (e.g. http://localhost:5173) to read "
            "/api/evidence and /api/status via CORS. Repeatable. No wildcard; "
            "none allowed by default (existing behaviour unchanged)."
        ),
    ),
    evidence_root: str | None = typer.Option(
        None,
        "--evidence-root",
        help=(
            "Serve a read-only evidence pack root. Requires .hyodo/agent-events.jsonl; "
            "project gates and safety scans are not executed."
        ),
    ),
):
    """Serve a local, evidence-only Jin-Seon-Mi-In-Hyo-Yeong dashboard."""
    try:
        if evidence_root is not None and path is not None:
            raise FileNotFoundError("use either PATH or --evidence-root, not both")
        target = resolve_check_target(evidence_root if evidence_root is not None else path)
    except FileNotFoundError as exc:
        console.print(f"[red]Path not found: {exc}[/red]")
        raise typer.Exit(2) from exc
    evidence_only = evidence_root is not None
    root = resolve_evidence_root(target) if evidence_only else resolve_dashboard_root(target)
    if root is None and evidence_only:
        console.print(
            "[red]--evidence-root requires .hyodo/agent-events.jsonl; "
            "the evidence source is not observable.[/red]"
        )
        raise typer.Exit(2)
    if root is None:
        console.print(
            "[red]dashboard requires a HyoDo checkout (pyproject.toml + hyodo/) "
            "or a project with .hyodo/gates.toml.[/red]"
        )
        console.print(
            "[dim]Tip: run 'hyodo init' to adopt this project's own tools as gates.[/dim]"
        )
        raise typer.Exit(2)
    refresh_token = token_urlsafe(32)
    refresh_lock = threading.Lock()

    def _refresh_evidence() -> dict[str, object]:
        """Collect one serialized local measurement without concurrent gate runs."""
        with refresh_lock:
            return (
                collect_evidence_root_snapshot(root)
                if evidence_only
                else collect_dashboard_evidence(root)
            )

    state = DashboardState(_refresh_evidence(), refresh_token=refresh_token, interval=interval)
    stop_refresh = threading.Event()

    def _refresh_loop() -> None:
        while not stop_refresh.wait(interval):
            try:
                state.update(_refresh_evidence())
            except Exception as exc:
                console.print(f"[yellow]Re-measure failed; keeping last snapshot: {exc}[/yellow]")

    try:
        server = ThreadingHTTPServer(
            (LOOPBACK_HOST, port),
            make_dashboard_handler(
                state, _refresh_evidence, refresh_token, tuple(allow_origin), root=root
            ),
        )
    except OSError as exc:
        console.print(f"[red]Cannot bind {LOOPBACK_HOST}:{port}: {exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Dashboard: http://{LOOPBACK_HOST}:{port}[/green]")
    if interval:
        console.print(
            f"[dim]Local only. Press Ctrl+C to stop. Re-measures every {interval}s.[/dim]"
        )
        threading.Thread(target=_refresh_loop, name="hyodo-dashboard-refresh", daemon=True).start()
    else:
        console.print(
            "[dim]Local only. Press Ctrl+C to stop. Snapshot is fixed at server start.[/dim]"
        )
    if open_browser:
        webbrowser.open(f"http://{LOOPBACK_HOST}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\nDashboard stopped.")
    finally:
        stop_refresh.set()
        server.server_close()


@app.command()
def version():
    """Print HyoDo version."""
    console.print(f"HyoDo v{__version__} - model-agnostic quality gates")


_GATES_INIT_EMPTY_TEMPLATE = f"""schema = "{SCHEMA_ID}"

# HyoDo Bring-Your-Own-Gates: no existing tool footprint was detected in this
# checkout (no pyproject.toml/package.json/tsconfig.json/go.mod/Cargo.toml, and
# no Makefile test:/lint: target). Absorb your own commands here -- each
# becomes a first-class gate for `hyodo check`. Uncomment and edit:
#
# [gates.tests]
# pillar = "goodness"
# command = "pytest -q"
# timeout = 120
#
# [gates.lint]
# pillar = "beauty"
# command = "ruff check ."
#
# Benevolence/Hyo/Eternity are measured natively from the checkout (see
# hyodo/pillars.py) and are never command gates.
"""


@app.command()
def init(
    path: str | None = typer.Argument(
        None, help="Project path to scan and initialize (defaults to current directory)"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing .hyodo/gates.toml"),
):
    """
    Detect this project's existing quality tools and write .hyodo/gates.toml.

    Bring-Your-Own-Gates: absorbed commands become first-class `hyodo check`
    gates attributed to Truth/Goodness/Beauty. Benevolence/Hyo/Eternity are
    measured natively from the checkout and are never command gates.
    """
    console.print(Panel.fit("HyoDo init - Bring-Your-Own-Gates", style="bold blue"))
    try:
        target = resolve_check_target(path)
    except FileNotFoundError as exc:
        console.print(f"[red]Path not found: {exc}[/red]")
        raise typer.Exit(2) from exc

    root = target if target.is_dir() else target.parent
    gates_path = root / GATES_CONFIG_RELATIVE_PATH
    console.print(f"Target: {root}")

    if gates_path.exists() and not force:
        console.print(f"[red]{gates_path} already exists.[/red]")
        console.print("[yellow]Use --force to overwrite it.[/yellow]")
        raise typer.Exit(1)

    detected = detect_project_gates(root)

    if detected:
        table = Table(title="Detected gates to absorb", show_header=True)
        table.add_column("Gate", style="cyan")
        table.add_column("Pillar (Hanja/Korean/English)")
        table.add_column("Command")
        table.add_column("Source")
        for name in sorted(detected):
            spec = detected[name]
            table.add_row(
                name, _trilingual_pillar_label(spec["pillar"]), spec["command"], spec["source"]
            )
        console.print(table)
        rendered = render_gates_toml(detected)
    else:
        console.print("[yellow]No existing tooling detected in this checkout.[/yellow]")
        console.print("[dim]Writing a starter .hyodo/gates.toml with commented-out examples.[/dim]")
        rendered = _GATES_INIT_EMPTY_TEMPLATE

    gates_path.parent.mkdir(parents=True, exist_ok=True)
    gates_path.write_text(rendered, encoding="utf-8")
    console.print(f"[green]Wrote {gates_path}[/green]")

    console.print("\n[bold cyan]Next steps:[/bold cyan]")
    console.print("  1. Review/edit .hyodo/gates.toml")
    console.print("  2. hyodo check              # runs the absorbed gates")
    console.print("  3. hyodo dashboard --open   # view evidence")
    console.print(
        "\n[dim]Commit .hyodo/gates.toml (and .hyodo/policy.toml if you use "
        "`hyodo connect`); everything else under .hyodo/ is per-machine "
        "runtime state — see docs/CONNECT.md 'What to commit'.[/dim]"
    )
    raise typer.Exit(0)


@dataclass(frozen=True)
class GeneralGateResult:
    """Result of one language-agnostic gate (``hyodo check --general``)."""

    language: str
    tool: str
    status: GateStatus
    message: str


_GENERAL_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".tox",
    "target",
}
_GENERAL_FILE_CAP = 50


def _collect_files(
    root: Path,
    suffixes: tuple[str, ...],
    cap: int = _GENERAL_FILE_CAP,
    exclusions: ScanExceptionsConfig | None = None,
) -> list[Path]:
    """Collect up to *cap* files under *root* matching *suffixes* (vendor dirs pruned)."""
    collected: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in _GENERAL_SKIP_DIRS and not d.startswith(".")
        )
        for name in sorted(filenames):
            if name.endswith(suffixes):
                candidate = Path(dirpath) / name
                if exclusions is not None and is_general_path_excluded(candidate, root, exclusions):
                    continue
                collected.append(candidate)
                if len(collected) >= cap:
                    return collected
    return collected


def _run_general_cmd(
    language: str,
    tool: str,
    cmd: list[str],
    root: Path,
    verbose: bool,
    ok_detail: str,
) -> GeneralGateResult:
    """Run one gate command and convert the outcome into a GeneralGateResult."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(root))
    except subprocess.TimeoutExpired:
        return GeneralGateResult(language, tool, GateStatus.FAIL, "timeout (>120s)")
    except OSError as e:
        return GeneralGateResult(language, tool, GateStatus.FAIL, f"exception: {e}")
    if proc.returncode == 0:
        return GeneralGateResult(language, tool, GateStatus.PASS, ok_detail)
    detail = (proc.stderr or proc.stdout or "").strip()
    message = f"exit {proc.returncode}"
    if detail:
        message += f": {detail[:600] if verbose else detail[:200]}"
    return GeneralGateResult(language, tool, GateStatus.FAIL, message)


def _run_per_file_general_cmd(
    language: str,
    tool: str,
    binary: str,
    flag: str,
    files: list[Path],
) -> GeneralGateResult:
    """Run ``binary flag <file>`` per file (node --check / bash -n style gates)."""
    bad: list[str] = []
    for file_path in files:
        try:
            proc = subprocess.run(
                [binary, flag, str(file_path)], capture_output=True, text=True, timeout=30
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            bad.append(f"{file_path.name} ({e})")
            continue
        if proc.returncode != 0:
            bad.append(file_path.name)
    if bad:
        return GeneralGateResult(
            language,
            tool,
            GateStatus.FAIL,
            f"{len(bad)}/{len(files)} files failed: " + ", ".join(bad[:5]),
        )
    return GeneralGateResult(language, tool, GateStatus.PASS, f"{len(files)} files parsed")


def _skip_missing_tool(language: str, tool: str) -> GeneralGateResult:
    return GeneralGateResult(language, tool, GateStatus.SKIP, f"{tool} not installed; skipped")


_GENERAL_TSCONFIG_CAP = 20


def _tsconfig_dependencies_missing(tsconfig: Path, root: Path) -> str | None:
    """Return an honest SKIP message if *tsconfig*'s project has a
    ``package.json`` but no installed ``node_modules``, else ``None``.

    Walks from ``tsconfig.parent`` up to (and including) *root*. If a
    ``package.json`` exists anywhere on that path but no ``node_modules``
    directory exists anywhere on that path, the project's dependencies were
    never installed and running ``tsc`` would fail on unresolved imports for
    environment reasons, not a code defect (e.g. a CI runner with a global
    tsc but no ``npm install`` step for a monorepo sub-project). If no
    ``package.json`` exists at all on the path, this returns ``None`` and the
    caller keeps the existing behaviour of running ``tsc`` anyway.
    """
    has_package_json = False
    has_node_modules = False
    current = tsconfig.parent
    while True:
        if (current / "package.json").is_file():
            has_package_json = True
        if (current / "node_modules").is_dir():
            has_node_modules = True
        if current == root or current.parent == current:
            break
        current = current.parent
    if has_package_json and not has_node_modules:
        try:
            rel = tsconfig.relative_to(root)
        except ValueError:
            rel = tsconfig
        return f"dependencies not installed (no node_modules next to {rel}); skipped"
    return None


def _find_tsconfigs(
    root: Path,
    exclusions: ScanExceptionsConfig | None = None,
    cap: int = _GENERAL_TSCONFIG_CAP,
) -> list[Path]:
    """Find up to *cap* ``tsconfig.json`` files anywhere under *root* (vendor dirs pruned).

    A monorepo commonly has no root-level ``tsconfig.json`` at all, only one
    per package/app (e.g. ``apps/learning-platform/tsconfig.json``). Looking
    only at ``root / "tsconfig.json"`` (as the previous implementation did)
    makes every such project's TypeScript invisible to ``--general``.
    """
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in _GENERAL_SKIP_DIRS and not d.startswith(".")
        )
        if "tsconfig.json" in filenames:
            candidate = Path(dirpath) / "tsconfig.json"
            if exclusions is None or not is_general_path_excluded(candidate, root, exclusions):
                found.append(candidate)
                if len(found) >= cap:
                    return found
    return found


def _resolve_tsc_binary(start: Path, root: Path) -> str | None:
    """Resolve a ``tsc`` binary for a tsconfig at *start*, monorepo-aware.

    A package inside a monorepo commonly gets TypeScript only as a local
    devDependency (``apps/<name>/node_modules/.bin/tsc``), never installed
    globally or exposed on PATH. Looking only at ``shutil.which("tsc")`` (as
    the previous implementation did) made every such package's TypeScript
    silently SKIP instead of actually type-checking.

    Walks from *start* up to (and including) *root* looking for
    ``node_modules/.bin/tsc`` at each level -- the same resolution order
    Node tooling itself uses -- and falls back to PATH only if none is found.
    """
    try:
        root_resolved = root.resolve()
        current = start.resolve()
    except OSError:
        return shutil.which("tsc")
    while True:
        candidate = current / "node_modules" / ".bin" / "tsc"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        if current == root_resolved or current.parent == current:
            break
        current = current.parent
    return shutil.which("tsc")


def _run_general_gates(
    root: Path, verbose: bool = False, exclusions: ScanExceptionsConfig | None = None
) -> list[GeneralGateResult]:
    """Auto-detect project languages under *root* and run one syntax/vet gate each.

    Detection is bounded (up to 50 files per language, vendor dirs pruned),
    so PASS means "sampled files parse", not a full-project verification.
    """
    results: list[GeneralGateResult] = []

    py_files = _collect_files(root, (".py",), exclusions=exclusions)
    if py_files:
        results.append(
            _run_general_cmd(
                "Python",
                "py_compile",
                [sys.executable, "-m", "py_compile", *map(str, py_files)],
                root,
                verbose,
                f"{len(py_files)} files compiled",
            )
        )

    ts_files = _collect_files(root, (".ts", ".tsx"), exclusions=exclusions)
    js_files = _collect_files(root, (".js", ".mjs", ".cjs"), exclusions=exclusions)
    tsconfigs = _find_tsconfigs(root, exclusions) if (ts_files or js_files) else []
    if tsconfigs:
        runnable: list[tuple[Path, str]] = []
        for tsconfig in tsconfigs:
            try:
                rel = tsconfig.parent.relative_to(root)
            except ValueError:
                rel = tsconfig.parent
            tool = "tsc" if str(rel) == "." else f"tsc ({rel})"
            deps_missing = _tsconfig_dependencies_missing(tsconfig, root)
            if deps_missing:
                results.append(GeneralGateResult("TypeScript", tool, GateStatus.SKIP, deps_missing))
                continue
            runnable.append((tsconfig, tool))
        if runnable:
            resolved = [
                (tsconfig, tool, _resolve_tsc_binary(tsconfig.parent, root))
                for tsconfig, tool in runnable
            ]
            if any(tsc for _, _, tsc in resolved):
                for tsconfig, tool, tsc in resolved:
                    if tsc:
                        results.append(
                            _run_general_cmd(
                                "TypeScript",
                                tool,
                                [tsc, "--noEmit", "-p", str(tsconfig)],
                                root,
                                verbose,
                                "tsc --noEmit clean",
                            )
                        )
                    else:
                        results.append(
                            GeneralGateResult(
                                "TypeScript",
                                tool,
                                GateStatus.SKIP,
                                "tsc not installed (checked node_modules/.bin up to project root, "
                                "and PATH); skipped",
                            )
                        )
            else:
                results.append(
                    GeneralGateResult(
                        "TypeScript",
                        "tsc",
                        GateStatus.SKIP,
                        f"tsc not installed; skipped ({len(runnable)} tsconfig.json found)",
                    )
                )
    else:
        if ts_files:
            results.append(
                GeneralGateResult(
                    "TypeScript",
                    "tsc",
                    GateStatus.UNSUPPORTED,
                    f"{len(ts_files)} TypeScript file(s) found but no tsconfig.json "
                    "anywhere in project; type-check not executed",
                )
            )
        if js_files:
            node = shutil.which("node")
            if node:
                results.append(
                    _run_per_file_general_cmd(
                        "JavaScript", "node --check", node, "--check", js_files
                    )
                )
            else:
                results.append(_skip_missing_tool("JavaScript", "node"))

    if (root / "go.mod").exists():
        go = shutil.which("go")
        if go:
            results.append(
                _run_general_cmd(
                    "Go", "go vet", [go, "vet", "./..."], root, verbose, "go vet clean"
                )
            )
        else:
            results.append(_skip_missing_tool("Go", "go"))

    if (root / "Cargo.toml").exists():
        cargo = shutil.which("cargo")
        if cargo:
            results.append(
                _run_general_cmd(
                    "Rust",
                    "cargo check",
                    [cargo, "check", "--quiet"],
                    root,
                    verbose,
                    "cargo check clean",
                )
            )
        else:
            results.append(_skip_missing_tool("Rust", "cargo"))

    sh_files = _collect_files(root, (".sh", ".bash"), exclusions=exclusions)
    if sh_files:
        bash = shutil.which("bash")
        if bash:
            results.append(_run_per_file_general_cmd("Shell", "bash -n", bash, "-n", sh_files))
        else:
            results.append(_skip_missing_tool("Shell", "bash"))

    return results


def _print_general_results(results: list[GeneralGateResult], root: Path) -> None:
    """Print one line per general gate result."""
    if not results:
        console.print(
            f"[yellow]No supported languages detected in {root} "
            "(Python/TypeScript/JavaScript/Go/Rust/Shell).[/yellow]"
        )
        return
    styles = {GateStatus.PASS: "green", GateStatus.FAIL: "red"}
    for result in results:
        style = styles.get(result.status, "yellow")
        console.print(
            f"  [{style}]{result.status.value}[/{style}] "
            f"{result.language} ({result.tool}): {result.message}"
        )


def _audience_option() -> str | None:
    return typer.Option(
        None,
        "--audience",
        help="Presentation lens: vibe, engineer, or professional. Never changes the "
        "decision, exit code, rule_id, or evidence -- see docs/AUDIENCE.md. "
        "Resolution: --audience -> HYODO_AUDIENCE -> .hyodo/config.toml -> engineer.",
    )


def _resolve_audience_or_exit(
    root: Path, audience_flag: str | None, command: str, json_output: bool
) -> AudienceProfile:
    """Resolve the audience profile, exiting 2 UNOBSERVED on an invalid explicit value."""
    try:
        return resolve_audience(root, flag=audience_flag, env=os.environ.get("HYODO_AUDIENCE"))
    except InvalidAudienceError as exc:
        reason = str(exc)
        if json_output:
            console.print_json(
                json.dumps({"decision": "UNOBSERVED", "reason": reason, "exit_code": 2})
            )
        else:
            console.print(f"[red]{reason}[/red] -- expected one of {', '.join(VALID_PROFILES)}.")
            console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2) from exc


@contextmanager
def _verdict_output(
    command: str,
    state: dict[str, Any],
    quiet: bool,
    explain: bool,
    json_output: bool,
    audience: AudienceProfile | None = None,
    native_response: bool = False,
) -> Iterator[None]:
    """Stream default details; propagate the original command exit unchanged."""
    profile = audience or AudienceProfile(profile="engineer")
    with console.capture() if quiet or json_output else nullcontext() as captured:
        try:
            yield
        except typer.Exit as exc:
            exit_code = exc.exit_code
        else:
            exit_code = 0
    decision = state.get("decision", {0: "PASS", 1: "FAIL"}.get(exit_code, "UNOBSERVED"))
    detail = state.get("detail", "required evidence UNOBSERVED")
    if command == "check":
        detail = ", ".join(state.get("failed", [])) or (
            "all executed gates passed" if exit_code == 0 else "required gates UNOBSERVED"
        )
    # Measurement provenance is a separate axis from policy: it does not ask
    # whether an actor was permitted to act, it asks whether this measurement
    # is valid at all. A MISMATCH means the gates that just ran came from a
    # different HyoDo than the one being measured, so their verdict describes
    # code nobody asked about — it cannot be reported as green.
    provenance = state.get("provenance")
    if provenance is not None and provenance.validity == "MISMATCH" and decision == "PASS":
        decision = "UNOBSERVED"
        detail = provenance.summary()
    verdict_args = (
        decision,
        state.get("observed", 0),
        state.get("expected", 0),
        state["unit"],
        detail,
    )
    sampled_limitation = (
        f"Sampled syntax gates only (up to {_GENERAL_FILE_CAP} files per language); "
        "not a full-project validation"
        if command == "check" and state.get("sampled")
        else ""
    )
    if json_output:
        if native_response:
            assert captured is not None
            console.print_json(captured.get())
            return
        # --json content stays byte-identical across profiles: the profile
        # is surfaced only as the added "audience" key, never by reflavoring
        # an existing field (including "verdict").
        verdict = render_verdict_line(*verdict_args, audience="engineer")
        if sampled_limitation:
            verdict += f"; {sampled_limitation}"
        if command == "check":
            payload = {
                "status": decision,
                "gates_ran": state.get("observed", 0),
                "gates_total": state.get("expected", 0),
                "failed": state.get("failed", []),
                "exit_code": exit_code,
            }
            if sampled_limitation:
                payload.update(sampled=True, scope="sampled_syntax", limitation=sampled_limitation)
            if "test_integrity" in state:
                payload["test_integrity"] = state["test_integrity"]
            if "dx_signals" in state:
                payload["dx_signals"] = state["dx_signals"]
            if provenance is not None:
                # the portable form: commit ids and digests, never a home
                # directory, because --json output travels into issues
                payload["provenance"] = provenance.to_portable_dict()
        else:
            assert captured is not None
            payload = json.loads(captured.get())
        payload["verdict"] = verdict
        payload["audience"] = profile.profile
        console.print_json(json.dumps(payload))
    else:
        verdict = render_verdict_line(*verdict_args, audience=profile.profile)
        if sampled_limitation:
            verdict += f"; {sampled_limitation}"
        # Local terminal output may carry absolute paths: the person reading it
        # needs to know which directory to go fix. Never silent, even when the
        # provenance is fine, so "measured by what?" always has an answer.
        # Printed before the verdict, because the verdict line is the one
        # callers parse and it has to stay last.
        if provenance is not None and not quiet:
            typer.echo(f"Measurement: {provenance.summary()}")
        typer.echo(verdict)
        if explain:
            typer.echo(
                "Explanation: "
                + explain_decision(
                    command,
                    decision,
                    state.get("rule_id"),
                    audience=profile.profile,
                    domain=profile.domain,
                )
            )
    raise typer.Exit(exit_code)


def _policy_verdict_state(decision: Any) -> dict[str, Any]:
    return {
        "decision": decision.decision,
        "observed": decision.coverage[0],
        "expected": decision.coverage[1],
        "rule_id": decision.rule_id,
        "detail": f"trust={decision.trust_level}, " + (decision.reason or "policy checks allow"),
    }


@app.command()
def check(
    path: str | None = typer.Argument(None, help="Path to file or directory"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply auto-fixes where supported"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    general: bool = typer.Option(
        False, "--general", help="Run language-agnostic gates (auto-detect Python/JS/Go/Rust/Shell)"
    ),
    quiet: bool = typer.Option(False, "--quiet", help="Print only the verdict line"),
    explain: bool = typer.Option(False, "--explain", help="Print a stored explanation"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
    audience: str | None = _audience_option(),
    strict_tests: bool = typer.Option(
        False,
        "--strict-tests",
        help="Fail the Truth gate when pyright passes but vacuous tests are found (Phase 1-E)",
    ),
):
    """
    Run HyoDo checkout release gates (4-Gate CI).

    Model-agnostic means independent of the AI model or agent UI.
    It does not currently mean language-agnostic or any-repo universal.

    Resolution order: --general (explicit opt-in) -> .hyodo/gates.toml
    (Bring-Your-Own-Gates, if present -- see `hyodo init`) -> HyoDo checkout
    preset (Pyright -> Ruff -> pytest -> SBOM) -> built-in sampled fallback.

    --general instead runs bounded language-agnostic syntax gates
    (Python/TS/JS/Go/Rust/Shell auto-detected, up to 50 files per language).
    The same sampled gates run by default outside a HyoDo checkout when no
    BYOG configuration exists. They are not a full-project validation.
    No executed gates exits 2; failed gates exit 1; executed gates all passing exit 0.

    A fifth, report-only computation (test integrity: are the tests asserting
    anything observable?) always runs alongside the HyoDo-checkout preset gates;
    it never changes the exit code unless --strict-tests is passed.
    """

    profile = _resolve_audience_or_exit(Path.cwd(), audience, "check", json_output)
    verdict_state: dict[str, Any] = {"unit": "gates"}
    # Resolved before any gate runs, so the answer to "which HyoDo measured
    # this?" exists even when the gates themselves blow up. Never raises: an
    # unreadable origin is reported as UNOBSERVED, not as a crash.
    verdict_state["provenance"] = resolve_provenance(Path.cwd())
    with _verdict_output("check", verdict_state, quiet, explain, json_output, profile):
        console.print(Panel.fit("HyoDo Code Quality Check", style="bold blue"))

        try:
            target = resolve_check_target(path)
        except FileNotFoundError as exc:
            console.print(f"[red]Path not found: {exc}[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2) from exc

        console.print(f"Target: {target}")
        check_root = target if target.is_dir() else target.parent

        # --general mode: language-agnostic gates (explicit opt-in, unchanged)
        if general:
            gen_root = check_root
            console.print(f"[cyan]General mode: auto-detecting languages in {gen_root}[/cyan]")
            try:
                scan_exceptions = load_scan_exceptions(gen_root)
            except ScanExceptionsConfigError as exc:
                console.print(f"[red]Invalid scan exceptions: {exc}[/red]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
                raise typer.Exit(2) from exc
            gen_results = _run_general_gates(gen_root, verbose, scan_exceptions)
            if scan_exceptions.general:
                console.print(
                    f"[dim]Audited general exclusions configured: {len(scan_exceptions.general)}[/dim]"
                )
            verdict_state.update(
                observed=sum(r.status in {GateStatus.PASS, GateStatus.FAIL} for r in gen_results),
                expected=len(gen_results),
                failed=[
                    f"{r.language} ({r.tool})" for r in gen_results if r.status is GateStatus.FAIL
                ],
                sampled=True,
            )
            _print_general_results(gen_results, gen_root)
            failed = [r for r in gen_results if r.status is GateStatus.FAIL]
            executed = [r for r in gen_results if r.status in {GateStatus.PASS, GateStatus.FAIL}]
            console.print("\n" + "=" * 50)
            if not executed:
                console.print("[bold yellow]No language gates were executed[/bold yellow]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
                raise typer.Exit(2)
            if failed:
                console.print(
                    f"[bold red]Some gates failed[/bold red] "
                    f"({len(executed)}/{len(gen_results)} gates ran)"
                )
                _print_failure_guidance([(f"{r.language} ({r.tool})", r.message) for r in failed])
                raise typer.Exit(1)
            console.print(
                f"[bold green]All executed gates passed "
                f"({len(executed)}/{len(gen_results)} gates ran)[/bold green]"
            )
            console.print(
                "[dim]Sampled syntax gates only (up to 50 files per language) — "
                "not a full-project validation.[/dim]"
            )
            raise typer.Exit(0)

        # Bring-Your-Own-Gates: a `.hyodo/gates.toml` (see `hyodo init`) takes
        # priority over the HyoDo-checkout-only preset below.
        try:
            gates_config = load_gates_config(check_root)
        except GatesConfigError as exc:
            console.print(f"[red]{exc}[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2) from exc

        if gates_config is not None:
            console.print(f"[cyan]User gates: {check_root / GATES_CONFIG_RELATIVE_PATH}[/cyan]")
            user_results = run_user_gates(gates_config, check_root, verbose=verbose)
            verdict_state.update(
                observed=sum(r.status in {"PASS", "FAIL"} for r in user_results),
                expected=len(user_results),
                failed=[r.name for r in user_results if r.status == "FAIL"],
            )
            user_styles = {"PASS": "green", "FAIL": "red", "SKIP": "yellow"}
            for user_result in user_results:
                style = user_styles.get(user_result.status, "yellow")
                console.print(
                    f"  [{style}]{user_result.status}[/{style}] {user_result.name} "
                    f"({_trilingual_pillar_label(user_result.pillar)}): {user_result.message}"
                )
            user_failed = [r for r in user_results if r.status == "FAIL"]
            user_executed = [r for r in user_results if r.status in {"PASS", "FAIL"}]
            console.print("\n" + "=" * 50)
            if not user_executed:
                console.print("[bold yellow]No user gates were executed[/bold yellow]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
                raise typer.Exit(2)
            if user_failed:
                console.print(
                    f"[bold red]Some gates failed[/bold red] "
                    f"({len(user_executed)}/{len(user_results)} gates ran)"
                )
                _print_failure_guidance([(r.name, r.message) for r in user_failed])
                raise typer.Exit(1)
            console.print(
                f"[bold green]All executed gates passed "
                f"({len(user_executed)}/{len(user_results)} gates ran)[/bold green]"
            )
            console.print(
                "[green]Gates support review readiness. Human approval still required.[/green]"
            )
            raise typer.Exit(0)

        root = find_repo_root(target)
        if root is None:
            # Neither a HyoDo package checkout nor a BYOG .hyodo/gates.toml was
            # found. Do not give up on measurement -- fall back to the same
            # built-in, language-agnostic sampled gates `--general` runs, but
            # say plainly this is a sample fallback, not a full-project BYOG
            # gate run, so it never reads as the same-caliber verdict.
            console.print(
                "[yellow]Not a HyoDo package checkout "
                "(requires pyproject.toml + hyodo/ at project root).[/yellow]"
            )
            console.print(
                "[dim]Tip: run 'hyodo init' to absorb this project's own tools as gates "
                "(Bring-Your-Own-Gates).[/dim]"
            )
            console.print(
                "[cyan]Default gates (built-in, sampled) — no project gates found; "
                "run 'hyodo init' for BYOG[/cyan]"
            )
            try:
                scan_exceptions = load_scan_exceptions(check_root)
            except ScanExceptionsConfigError as exc:
                console.print(f"[red]Invalid scan exceptions: {exc}[/red]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
                raise typer.Exit(2) from exc
            gen_results = _run_general_gates(check_root, verbose, scan_exceptions)
            if scan_exceptions.general:
                console.print(
                    f"[dim]Audited general exclusions configured: "
                    f"{len(scan_exceptions.general)}[/dim]"
                )
            verdict_state.update(
                observed=sum(r.status in {GateStatus.PASS, GateStatus.FAIL} for r in gen_results),
                expected=len(gen_results),
                failed=[
                    f"{r.language} ({r.tool})" for r in gen_results if r.status is GateStatus.FAIL
                ],
                sampled=True,
            )
            _print_general_results(gen_results, check_root)
            gen_failed = [r for r in gen_results if r.status is GateStatus.FAIL]
            gen_executed = [
                r for r in gen_results if r.status in {GateStatus.PASS, GateStatus.FAIL}
            ]
            console.print("\n" + "=" * 50)
            if not gen_executed:
                # Keep the wording the public smoke contract greps for
                # (smoke.yml "empty-directory check is not a false green").
                console.print("[bold yellow]No project gates were executed[/bold yellow]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
                raise typer.Exit(2)
            if gen_failed:
                console.print(
                    f"[bold red]Some default gates failed[/bold red] "
                    f"({len(gen_executed)}/{len(gen_results)} gates ran, built-in sampled)"
                )
                _print_failure_guidance(
                    [(f"{r.language} ({r.tool})", r.message) for r in gen_failed]
                )
                raise typer.Exit(1)
            console.print(
                f"[bold green]All executed default gates passed "
                f"({len(gen_executed)}/{len(gen_results)} gates ran)[/bold green]"
            )
            console.print(
                "[dim]Default gates (built-in, sampled) — up to 50 files per language, "
                "not a full-project BYOG validation. Run 'hyodo init' for BYOG.[/dim]"
            )
            raise typer.Exit(0)

        console.print(f"HyoDo checkout: {root}")

        results: list[GateResult] = []

        console.print("\n[1/4] Truth - Type checking...")
        pyright_result = run_pyright_check(root, verbose)
        _print_gate_result(pyright_result)
        results.append(pyright_result)

        console.print("\n[2/4] Beauty - Lint & Format...")
        ruff_result = run_ruff_check(root, fix, verbose)
        _print_gate_result(ruff_result)
        if ruff_result.status is GateStatus.FAIL and "not found" not in ruff_result.message and fix:
            console.print("  [yellow]   Try running with --fix to auto-fix issues[/yellow]")
        results.append(ruff_result)

        console.print("\n[3/4] Goodness - Tests...")
        pytest_result = run_pytest_check(root, verbose)
        _print_gate_result(pytest_result)
        results.append(pytest_result)

        console.print("\n[4/4] Eternity - Security seal...")
        sbom_result = run_sbom_check(root, verbose)
        _print_gate_result(sbom_result)
        results.append(sbom_result)

        # Phase 1-E: report-only fifth computation. Native AST scan (no shelled-out
        # tool, no model call) of whether the project's own tests observe anything.
        # Additive by default -- does not join the results/executed/failed gate list,
        # so the "N/4 gates ran" counting above is unchanged. --strict-tests amends
        # the already-computed Truth (pyright) result in place instead of adding a
        # fifth named gate, per the Phase 1-E spec.
        test_integrity_report = scan_test_integrity(check_root)
        if (
            strict_tests
            and pyright_result.status is GateStatus.PASS
            and test_integrity_report.vacuous_tests > 0
        ):
            pyright_result = GateResult(
                GateStatus.FAIL,
                f"pyright: pass; test-integrity: {test_integrity_report.vacuous_tests}/"
                f"{test_integrity_report.total_tests} tests assert nothing",
            )
            results[0] = pyright_result
            # The live "[1/4] Truth" line above already said PASS; say plainly
            # that the strict test-integrity check amended it.
            console.print(
                "[bold red][1/4] Truth - amended to FAIL by --strict-tests:[/bold red] "
                f"{test_integrity_report.vacuous_tests}/{test_integrity_report.total_tests} "
                "tests assert nothing"
            )
        _print_test_integrity_line(test_integrity_report)
        verdict_state["test_integrity"] = _test_integrity_payload(test_integrity_report)

        # Report-only Benevolence DX-signals gate: additive, like test integrity
        # above -- does not join the results/executed/failed gate list, so the
        # "N/4 gates ran" counting is unchanged, and it never fails `check`.
        dx_signals = collect_dx_signals(check_root)
        dx_gate_result = _dx_signals_gate_result(dx_signals)
        _print_dx_signals_line(dx_signals, dx_gate_result)
        verdict_state["dx_signals"] = _dx_signals_payload(dx_signals)

        executed = [r for r in results if r.status in {GateStatus.PASS, GateStatus.FAIL}]
        failed = [r for r in results if r.status is GateStatus.FAIL]
        ran, total = len(executed), len(results)
        verdict_state.update(
            observed=ran,
            expected=total,
            failed=[
                name
                for name, result in zip(
                    ("Truth (pyright)", "Beauty (ruff)", "Goodness (pytest)", "Eternity (SBOM)"),
                    results,
                    strict=True,
                )
                if result.status is GateStatus.FAIL
            ],
        )

        console.print("\n" + "=" * 50)
        if not executed:
            console.print("[bold yellow]No project gates were executed[/bold yellow]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2)

        if failed:
            console.print(f"[bold red]Some gates failed[/bold red] ({ran}/{total} gates ran)")
            gate_names = (
                "Truth (pyright)",
                "Beauty (ruff)",
                "Goodness (pytest)",
                "Eternity (SBOM)",
            )
            _print_failure_guidance(
                [
                    (name, result.message)
                    for name, result in zip(gate_names, results, strict=True)
                    if result in failed
                ]
            )
            raise typer.Exit(1)

        console.print(
            f"[bold green]All executed gates passed ({ran}/{total} gates ran)[/bold green]"
        )
        console.print(
            "[green]Gates support review readiness. Human approval still required.[/green]"
        )
        raise typer.Exit(0)


def _resolve_score_pillars(
    benevolence: float | None,
    truth: float | None,
    goodness: float | None,
    hyo: float | None,
    beauty: float | None,
    serenity: float | None,
    eternity: float | None,
    partial: bool = False,
) -> tuple[float, float, float, float, float, bool]:
    """Resolve primary vs legacy flags; require all five pillars explicitly.

    When *partial* is True, missing pillars default to 0.5 (neutral); the band
    label stays score-derived and a separate WEAK-confidence marker is emitted
    by the caller (band and input completeness are orthogonal axes).

    Returns (benevolence, truth, goodness, hyo, beauty, partial_filled).
    Raises typer.Exit(2) on dual-flag conflicts or (non-partial) missing pillars.
    """
    if benevolence is not None and serenity is not None:
        console.print(
            "[red]Conflicting flags: pass only one of --benevolence/-i or "
            "--serenity/-s (legacy).[/red]"
        )
        raise typer.Exit(2)
    if hyo is not None and eternity is not None:
        console.print(
            "[red]Conflicting flags: pass only one of --hyo/-c or --eternity/-e (legacy).[/red]"
        )
        raise typer.Exit(2)

    effective_benevolence = benevolence if benevolence is not None else serenity
    effective_hyo = hyo if hyo is not None else eternity

    # Pillars are unit-interval values. The scoring function clamps, so "-t 9" (a very
    # easy typo for "-t 0.9") used to become a silent perfect 1.0 while the table still
    # printed 9. A typo must fail, not award full marks.
    for label, value in (
        ("--benevolence/-i", effective_benevolence),
        ("--truth/-t", truth),
        ("--goodness/-g", goodness),
        ("--hyo/-c", effective_hyo),
        ("--beauty/-b", beauty),
    ):
        if value is None:
            continue
        if not math.isfinite(value):
            console.print(f"[red]{label} must be a finite number, got {value}.[/red]")
            raise typer.Exit(2)
        if not 0.0 <= value <= 1.0:
            console.print(f"[red]{label} must be between 0.0 and 1.0, got {value}.[/red]")
            console.print("[dim]Pillars are unit-interval values, e.g. 0.9 — not 9.[/dim]")
            raise typer.Exit(2)

    missing: list[str] = []
    if effective_benevolence is None:
        missing.append("--benevolence/-i (or legacy --serenity/-s)")
    if truth is None:
        missing.append("--truth/-t")
    if goodness is None:
        missing.append("--goodness/-g")
    if effective_hyo is None:
        missing.append("--hyo/-c (or legacy --eternity/-e)")
    if beauty is None:
        missing.append("--beauty/-b")
    partial_filled = False

    if missing:
        if not partial:
            console.print(
                "[red]All five pillars are required. Missing:[/red] " + ", ".join(missing)
            )
            console.print("[dim]Example: hyodo score -t 0.9 -g 0.9 -b 0.9 -i 0.9 -c 0.9[/dim]")
            console.print(
                "[yellow]Defaults no longer fill missing pillars "
                "(avoids false STRONG signals).[/yellow]"
            )
            console.print(
                "[dim]Use --partial to allow missing pillars "
                "(defaults to 0.5, WEAK-confidence signal).[/dim]"
            )
            raise typer.Exit(2)
        console.print(
            f"[yellow]Partial mode: filling {len(missing)} missing pillar(s) "
            "with 0.5 (neutral).[/yellow]"
        )
        console.print(f"[dim]Missing: {', '.join(missing)}[/dim]")
        if effective_benevolence is None:
            effective_benevolence = 0.5
        if truth is None:
            truth = 0.5
        if goodness is None:
            goodness = 0.5
        if effective_hyo is None:
            effective_hyo = 0.5
        if beauty is None:
            beauty = 0.5
        partial_filled = True

    # Narrowed by the missing check above.
    assert effective_benevolence is not None
    assert truth is not None
    assert goodness is not None
    assert effective_hyo is not None
    assert beauty is not None
    return effective_benevolence, truth, goodness, effective_hyo, beauty, partial_filled


def _collect_check_observation(root: Path) -> dict[str, Any]:
    """Run the Truth/Beauty check gates in-process and shape a `check` dict.

    The gates score_derive.py's rule table consumes are run here (pyright
    for Truth, ruff for Beauty) -- pytest and the SBOM gate are skipped
    since no pillar rule reads them. Onboarding/DX signals (readme_present,
    start_hint_present, help_text_present) come from `collect_dx_signals`,
    a pure filesystem/regex/in-process-import scan -- see
    `hyodo/dx_signals.py` and docs/SCORE_DERIVATION.md.
    """
    pyright_result = run_pyright_check(root)
    ruff_result = run_ruff_check(root)
    dx_signals = collect_dx_signals(root)
    return {
        "truth_gate": pyright_result.status.value
        if pyright_result.status in {GateStatus.PASS, GateStatus.FAIL}
        else None,
        "beauty_gate": ruff_result.status.value
        if ruff_result.status in {GateStatus.PASS, GateStatus.FAIL}
        else None,
        "readme_present": dx_signals.readme_present,
        "start_hint_present": dx_signals.start_hint_present,
        "help_text_present": dx_signals.help_text_present,
    }


def _collect_safe_observation(root: Path) -> dict[str, Any]:
    """Run `hyodo safe` in-process and shape a `safe` dict for score_derive."""
    result = run_safety_scan(path=str(root), cwd=root, max_files=0)
    findings = result["findings"]
    return {
        "high": sum(1 for f in findings if f.severity == "high"),
        "medium": sum(1 for f in findings if f.severity == "medium"),
        "scanned_files": result.get("scanned_files"),
        "total_scannable": result.get("total_scannable"),
    }


def _collect_test_integrity_observation(root: Path) -> dict[str, Any]:
    """Run the test-integrity scan in-process and shape a dict for score_derive."""
    report = scan_test_integrity(root)
    return {"total_tests": report.total_tests, "vacuous_tests": report.vacuous_tests}


def _print_derived_pillars(derived: DerivedPillars) -> None:
    table = Table(title="Derived pillar inputs (hyodo score --from-check)", show_header=True)
    table.add_column("Pillar", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Coverage", justify="center")
    table.add_column("Top provenance")
    for name, result in derived.by_name().items():
        value_display = "UNOBSERVED" if result.value is None else f"{result.value:.1f}"
        coverage_color = {"OBSERVED": "green", "PARTIAL": "yellow", "UNOBSERVED": "red"}[
            result.coverage
        ]
        top_rows = result.top_provenance(3)
        provenance_display = (
            "; ".join(f"{row.rule_id} ({row.contribution:.1f})" for row in top_rows)
            if top_rows
            else "-"
        )
        table.add_row(
            name.capitalize() + (" [override]" if result.override else ""),
            value_display,
            f"[{coverage_color}]{result.coverage}[/{coverage_color}]",
            provenance_display,
        )
    console.print(table)


@app.command()
def score(
    benevolence: float | None = typer.Option(
        None, "--benevolence", "-i", help="Benevolence score (0-1); required"
    ),
    truth: float | None = typer.Option(None, "--truth", "-t", help="Truth score (0-1); required"),
    goodness: float | None = typer.Option(
        None, "--goodness", "-g", help="Goodness score (0-1); required"
    ),
    hyo: float | None = typer.Option(None, "--hyo", "-c", help="Hyo score (0-1); required"),
    beauty: float | None = typer.Option(
        None, "--beauty", "-b", help="Beauty score (0-1); required"
    ),
    serenity: float | None = typer.Option(
        None, "--serenity", "-s", help="[Legacy] maps to benevolence (0-1)"
    ),
    eternity: float | None = typer.Option(
        None, "--eternity", "-e", help="[Legacy] maps to hyo (0-1)"
    ),
    from_check: bool = typer.Option(
        False,
        "--from-check",
        help="Derive pillar inputs from hyodo check/safe/test-integrity instead of flags",
    ),
    root_opt: str | None = typer.Option(
        None, "--root", help="Project root for --from-check (default: current directory)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON (--from-check only)"
    ),
    partial: bool = typer.Option(
        False, "--partial", help="Allow missing pillars (defaults to 0.5, WEAK signal)"
    ),
):
    """
    Compute the HyoDo Integrity Score review signal.

    Model: Six-Virtue Model. Subset: Trinity Gates. Formula lineage: HYOGOOK V5.

    F = sum(five pillars on 1–10 scale) + geometric_mean
    S = geometric_mean

    All five pillars must be provided explicitly (no silent 1.0 defaults).
    Use --partial to allow missing pillars (filled with 0.5, WEAK signal).
    Legacy --serenity/--eternity may substitute for benevolence/hyo, but
    primary and legacy flags for the same pillar cannot be combined.
    Review emphasis labels are philosophical only — not F-score weights.
    Output is a review signal only — not automatic approval.

    --from-check derives the five pillar inputs from `hyodo check` /
    `hyodo safe` / the test-integrity scan instead of requiring flags; any
    of --benevolence/--truth/--goodness/--hyo/--beauty passed alongside it
    overrides that one derived pillar (recorded as an override in the
    provenance, not silently blended in). See docs/SCORE_DERIVATION.md.
    """
    from hyodo import calculate_hygook_v5_score

    if from_check:
        root = Path(root_opt).resolve() if root_opt else Path.cwd().resolve()
        if not root.is_dir():
            console.print(f"[red]--root path not found or not a directory: {root}[/red]")
            raise typer.Exit(2)

        check_obs = _collect_check_observation(root)
        safe_obs = _collect_safe_observation(root)
        test_integrity_obs = _collect_test_integrity_observation(root)
        derived = derive_pillars(
            root, check=check_obs, safe=safe_obs, test_integrity=test_integrity_obs
        )

        overrides = {
            "benevolence": benevolence,
            "truth": truth,
            "goodness": goodness,
            "hyo": hyo if hyo is not None else eternity,
            "beauty": beauty,
        }
        for label, override_value in overrides.items():
            if override_value is None:
                continue
            if not math.isfinite(override_value) or not 0.0 <= override_value <= 1.0:
                console.print(
                    f"[red]--{label} must be a finite number between 0.0 and 1.0, "
                    f"got {override_value}.[/red]"
                )
                raise typer.Exit(2)
            by_name = derived.by_name()
            by_name[label] = apply_override(by_name[label], override_value)
            derived = DerivedPillars(**by_name)

        by_name = derived.by_name()
        observed_pairs: list[tuple[str, float]] = [
            (name, unit_value)
            for name, result in by_name.items()
            if (unit_value := result.unit_value()) is not None
        ]
        unobserved = [name for name, result in by_name.items() if result.value is None]

        if not json_output:
            console.print(
                f"[dim]Model: {SCORE_MODEL_NAME} · Subset: {SCORE_SUBSET_NAME} · "
                f"Formula lineage: {SCORE_FORMULA_LINEAGE} · derived from: {root}[/dim]"
            )
            _print_derived_pillars(derived)

        if len(observed_pairs) == 5:
            values = dict(observed_pairs)
            f_score, s_eternity = calculate_hygook_v5_score(
                values["benevolence"],
                values["truth"],
                values["goodness"],
                values["hyo"],
                values["beauty"],
            )
            score_value = ((f_score - 6) / (60 - 6)) * 100
            eternity_coverage = "OBSERVED"
        else:
            f_score = None
            score_value = None
            s_eternity = (
                geometric_mean_observed([v * 100 for _, v in observed_pairs])
                if observed_pairs
                else None
            )
            eternity_coverage = "PARTIAL" if observed_pairs else "UNOBSERVED"

        if json_output:
            payload = {
                "root": str(root),
                "derivation": derived.as_dict(),
                "eternity": s_eternity,
                "eternity_coverage": eternity_coverage,
                "f_score": f_score,
                "score": score_value,
                "unobserved_pillars": unobserved,
                "note": "Review signal only — not automatic approval.",
            }
            console.print_json(json.dumps(payload))
            raise typer.Exit(0)

        if unobserved:
            console.print(
                f"\n[yellow]Eternity/F: PARTIAL — pillar(s) UNOBSERVED and excluded "
                f"from the geometric mean: {', '.join(unobserved)}.[/yellow]"
            )
            if s_eternity is not None:
                console.print(f"[dim]Eternity (S), observed pillars only: {s_eternity:.4f}[/dim]")
            console.print(
                "[yellow]TOTAL score requires all five pillars; pass the missing pillar(s) "
                "explicitly (e.g. --benevolence 0.8) to complete it.[/yellow]"
            )
        else:
            assert f_score is not None
            assert score_value is not None
            console.print(f"\nEternity (S): {s_eternity:.4f} · F Score: {f_score:.2f}")
            console.print(f"[bold]TOTAL: {score_value:.1f}%[/bold]")
            if score_value >= 90:
                console.print("[bold green]REVIEW_SIGNAL_STRONG (90+)[/bold green]")
            elif score_value >= 70:
                console.print("[bold yellow]REVIEW_SIGNAL_CAUTION (70-89)[/bold yellow]")
            else:
                console.print("[bold red]REVIEW_SIGNAL_BLOCK (<70)[/bold red]")
            console.print(
                "[dim]Review signal only — not automatic approval. "
                "Human approval still required.[/dim]"
            )
        raise typer.Exit(0)

    (
        effective_benevolence,
        truth,
        goodness,
        effective_hyo,
        beauty,
        partial_filled,
    ) = _resolve_score_pillars(
        benevolence, truth, goodness, hyo, beauty, serenity, eternity, partial=partial
    )

    F, S = calculate_hygook_v5_score(effective_benevolence, truth, goodness, effective_hyo, beauty)
    score_value = ((F - 6) / (60 - 6)) * 100

    console.print(
        f"[dim]Model: {SCORE_MODEL_NAME} · Subset: {SCORE_SUBSET_NAME} · "
        f"Formula lineage: {SCORE_FORMULA_LINEAGE}[/dim]"
    )
    table = Table(
        title=SCORE_PUBLIC_NAME,
        show_header=True,
    )
    table.add_column("Pillar", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Review emphasis", justify="right")
    table.add_column("Value", justify="right")

    table.add_row(
        "Benevolence",
        f"{effective_benevolence * 100:.0f}",
        "25% (not in F)",
        f"{effective_benevolence:.2f}",
    )
    table.add_row("Truth", f"{truth * 100:.0f}", "22% (not in F)", f"{truth:.2f}")
    table.add_row("Goodness", f"{goodness * 100:.0f}", "18% (not in F)", f"{goodness:.2f}")
    table.add_row(
        "Hyo",
        f"{effective_hyo * 100:.0f}",
        "15% (not in F)",
        f"{effective_hyo:.2f}",
    )
    table.add_row("Beauty", f"{beauty * 100:.0f}", "15% (not in F)", f"{beauty:.2f}")
    table.add_row("", "", "", "")
    table.add_row("Eternity (S)", "", "geometric mean", f"{S:.4f}")
    table.add_row("F Score", "", "sum + S", f"{F:.2f}")
    table.add_row("", "", "", "")
    table.add_row("[bold]TOTAL", "", "", f"[bold]{score_value:.1f}%[/bold]")

    console.print(table)
    console.print(
        "[dim]Review emphasis is not used in the F formula "
        f"(F = sum(1–10 pillars) + geometric mean). Formula lineage "
        f"{SCORE_FORMULA_LINEAGE} · philosophy V6.[/dim]"
    )

    if score_value >= 90:
        console.print("\n[bold green]REVIEW_SIGNAL_STRONG (90+)[/bold green]")
        console.print(
            "[green]Strong review signal only. Still run tests/security checks; "
            "human approval required.[/green]"
        )
    elif score_value >= 70:
        console.print("\n[bold yellow]REVIEW_SIGNAL_CAUTION (70-89)[/bold yellow]")
        console.print("[yellow]Review recommended before proceed. Not an approval.[/yellow]")
    else:
        console.print("\n[bold red]REVIEW_SIGNAL_BLOCK (<70)[/bold red]")
        console.print(
            "[red]Improve before merge. Score is not a substitute for human judgment.[/red]"
        )

    if partial_filled:
        console.print(
            "[bold yellow]SIGNAL_CONFIDENCE_WEAK[/bold yellow] "
            "[yellow]— missing pillars were defaulted to 0.5; "
            "treat this signal as weak evidence, not a measured score.[/yellow]"
        )


@app.command()
def safe(
    path: str | None = typer.Argument(None, help="Path to scan"),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit 1 when any high-severity finding is present (CI gate)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON instead of formatted text",
    ),
    max_files: int = typer.Option(
        40,
        "--max-files",
        help="Maximum files to scan in directory mode (default 40, use 0 for unlimited)",
    ),
    scan: str | None = typer.Option(
        None,
        "--scan",
        help="External scanner: gitleaks, trufflehog, or all (runs both)",
    ),
    quiet: bool = typer.Option(False, "--quiet", help="Print only the verdict line"),
    explain: bool = typer.Option(False, "--explain", help="Print a stored explanation"),
    audience: str | None = _audience_option(),
):
    """
    Safety early-warning scan.

    Default mode always exits 0 after printing findings (early warning).
    --strict exits 1 on high-severity findings; medium/caution alone stays 0.
    Missing path / scan failure exits 2.
    --json emits a single JSON document instead of formatted text; exit codes
    are identical between the two modes.

    --max-files N: override the directory scan cap (default 40, 0 = unlimited).
    --scan gitleaks: run gitleaks as external secret scanner (offline regex).
    --scan trufflehog: run trufflehog as external verified secret scanner.
    Note: trufflehog live-verifies candidates against issuing-service APIs
    (candidate secrets leave the machine); unverified hits report as medium.
    --scan all: run both gitleaks + trufflehog and merge findings. A scanner
    that fails to run is reported as a medium `*_unavailable` finding, never
    silently dropped.

    Limits: directory scans read at most --max-files files; default mode prefers
    git diff HEAD, else git status text (not full working tree contents).
    Not a full SAST / secret-scan / dependency audit unless --scan is used.
    """

    profile = _resolve_audience_or_exit(Path.cwd(), audience, "safe", json_output)
    verdict_state: dict[str, Any] = {"unit": "files"}
    with _verdict_output("safe", verdict_state, quiet, explain, json_output, profile):
        result = run_safety_scan(
            path=path, strict=strict, cwd=Path.cwd(), max_files=max_files, scan_tool=scan
        )
        source = str(result["source"])
        high_only = [f for f in result["findings"] if f.severity == "high"]

        scanned = result.get("scanned_files")
        total = result.get("total_scannable")
        coverage = result.get("coverage", "UNOBSERVED")
        partial_note = ""
        if coverage == "PARTIAL" and isinstance(scanned, int) and isinstance(total, int):
            unscanned = total - scanned
            partial_note = (
                f"; {unscanned} file(s) unscanned (coverage PARTIAL — pass --max-files 0 "
                "to scan all)"
            )
        verdict_state.update(
            observed=scanned if isinstance(scanned, int) else 0,
            expected=total if isinstance(total, int) and total else "unknown",
            detail=f"{len(high_only)} high findings"
            + (" (advisory; --strict blocks)" if high_only and not strict else "")
            + ("; file coverage UNOBSERVED" if scanned is None or total is None else "")
            + partial_note,
        )
        if source.startswith(("missing:", "error:")):
            verdict_state["detail"] = "scan target UNOBSERVED"
            verdict_state["decision"] = "UNOBSERVED"
        elif strict and high_only:
            verdict_state["decision"] = "FAIL"
        elif coverage == "PARTIAL":
            # A capped/partial scan is not a clean pass: a reader (or a CI gate
            # reading only the verdict line) must not mistake "40/161 files
            # observed" for a full scan that found nothing.
            verdict_state["decision"] = "PARTIAL"
        else:
            verdict_state["decision"] = "PASS"
        if json_output:
            exit_code = (
                2
                if source.startswith(("missing:", "error:"))
                else (1 if strict and high_only else 0)
            )
            payload = {
                "source": source,
                "scope": result.get("scope", "none"),
                "coverage": result.get("coverage", "UNOBSERVED"),
                "risk_score": result["risk_score"],
                "level": result["level"],
                "action": result["action"],
                "strict": strict,
                "exit_code": exit_code,
                "findings": [asdict(f) for f in result["findings"]],
                "exceptions_applied": int(result.get("exceptions_applied", 0)),
                "scanned_files": result.get("scanned_files"),
                "total_scannable": result.get("total_scannable"),
            }
            console.print_json(json.dumps(payload))
            raise typer.Exit(exit_code)

        console.print(Panel.fit("HyoDo Safety Check (early warning)", style="bold yellow"))
        console.print(f"source: {source}")
        scope = result.get("scope", "none")
        coverage = result.get("coverage", "UNOBSERVED")
        scanned_for_line = result.get("scanned_files")
        total_for_line = result.get("total_scannable")
        scanned_display = scanned_for_line if isinstance(scanned_for_line, int) else "?"
        total_display = total_for_line if isinstance(total_for_line, int) else "?"
        console.print(
            f"Scope: {scope} · Coverage: {coverage} ({scanned_display}/{total_display} files)"
        )
        if scope in ("diff", "status"):
            console.print("Hint: pass a directory (hyodo safe . --max-files 0) to scan the tree.")
        exceptions_applied = int(result.get("exceptions_applied", 0))
        if exceptions_applied:
            console.print(
                f"[yellow]Audited safety exceptions applied: {exceptions_applied}[/yellow]"
            )

        # missing path OR unreadable/scan IO failure — not a validation pass
        if source.startswith("missing:"):
            console.print("[red]Scan target not found.[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2)
        if source.startswith("error:"):
            console.print("[red]Scan failed (read error).[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2)

        for check_name, status, color in result["rows"]:
            console.print(f"  [{color}]{status}[/{color}] {check_name}")

        high_findings = [f for f in result["findings"] if f.severity in {"high", "medium"}]
        if high_findings:
            console.print("\n[bold]Findings[/bold]")
            for finding in high_findings[:12]:
                loc = ""
                if finding.path:
                    loc = f" @ {finding.path}"
                    if finding.line is not None:
                        loc += f":{finding.line}"
                elif finding.line is not None:
                    loc = f" @ line {finding.line}"
                console.print(
                    f"  - [{finding.severity}] {finding.category}/{finding.label}: "
                    f"{finding.detail}{loc}"
                )

        console.print(
            f"\nRisk: {result['level']} ({result['risk_score']}/100)\n-> {result['action']}"
        )
        scanned_files = result.get("scanned_files")
        total_scannable = result.get("total_scannable")
        if isinstance(scanned_files, int) and isinstance(total_scannable, int):
            if (
                source.startswith("dir:")
                and max_files > 0
                and scanned_files >= max_files
                and total_scannable > scanned_files
            ):
                coverage_note = (
                    f"Directory scan cap: scanned {scanned_files} of {total_scannable} files "
                    f"(cap {max_files}); raise --max-files to scan all. "
                )
            elif total_scannable > scanned_files:
                coverage_note = (
                    f"Scanned {scanned_files} of {total_scannable} files; "
                    "skipped or unreadable file contents remain UNOBSERVED. "
                )
            else:
                coverage_note = f"Scanned {scanned_files} of {total_scannable} files. "
        else:
            coverage_note = ""
        console.print(
            "[dim]Note: early warning only. Not a full SAST/secret-scan/dependency audit. "
            f"{coverage_note}Default corpus is git diff/status when no path.[/dim]"
        )

        if strict and high_only:
            raise typer.Exit(1)
        raise typer.Exit(0)


@app.command("inspect")
def inspect_cmd(
    path: str = typer.Argument(..., help="Directory to absorb into folder/chunks manifests"),
    ignore: list[str] = typer.Option(  # noqa: B008 - typer repeatable-option pattern;
        # ruff's B006/B008 heuristic fires on any `list[...]`-annotated Option default,
        # but typer.Option's default is read once at CLI parse time, never mutated.
        [],
        "--ignore",
        help=(
            "fnmatch glob (repeatable), tested against the relative path and the "
            "basename. Matching files are still listed with ignored: true, excluded "
            "from chunks and from coverage's expected count. .gitignore is never read."
        ),
    ),
    remote_inventory: list[str] = typer.Option(  # noqa: B008
        [],
        "--remote-inventory",
        help=(
            "Path to a hyodo.remote-inventory/v1 JSON file (repeatable) describing "
            "items a connector (e.g. Drive MCP) declared out-of-band. Recorded as a "
            "claim under folder-manifest 'remote'; never fetched, never chunked, "
            "never counted in coverage. Malformed input exits 1 before any write."
        ),
    ),
    report: str = typer.Option(
        "md", "--report", help="Report format printed to stdout: md (default) or json"
    ),
    root: str = typer.Option(
        ".", "--root", help="Base directory that manifest paths are reported relative to"
    ),
):
    """
    Absorb a directory into `.hyodo/folder-manifest.json` and `.hyodo/chunks-manifest.json`.

    Read-only field-deployment inventory: every file is digested (or explicitly
    listed under `unreadable`), secret-shaped files are excluded from chunking
    and reported by digest and location only, and chunk entries never carry file
    text. Never calls `evaluate_policy` — there is no ASK/exit-3 case here.

    Exit 0: manifests written, coverage complete (every file digested or listed
    in `unreadable`). Exit 1: `<path>` missing/not a directory, or a
    `--remote-inventory` file is malformed (nothing is written). Exit 2: manifest
    write failed (OSError), e.g. `.hyodo` cannot be created or is not writable.
    """
    from hyodo.inspect import (
        RemoteInventoryError,
        render_report_json,
        render_report_md,
        run_inspect,
        write_manifests,
    )

    if report not in ("md", "json"):
        console.print(f"[red]Invalid --report value: {report!r} (expected md or json)[/red]")
        raise typer.Exit(1)

    root_path = Path(root)

    try:
        result = run_inspect(
            path, root=root_path, ignore=ignore, remote_inventory_paths=remote_inventory
        )
    except NotADirectoryError:
        console.print(f"[red]Not a directory (or does not exist): {path}[/red]")
        raise typer.Exit(1) from None
    except RemoteInventoryError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None

    try:
        write_manifests(result, root_path)
    except OSError as exc:
        console.print(f"[red]Failed to write manifests under {root_path / '.hyodo'}: {exc}[/red]")
        raise typer.Exit(2) from None

    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]")

    if report == "json":
        console.print(render_report_json(result), highlight=False, markup=False)
    else:
        console.print(render_report_md(result), highlight=False, markup=False)

    raise typer.Exit(0)


@mcp_app.command("contract")
def mcp_contract(
    root: str = typer.Option(
        ".", "--root", help="Workspace root to measure the local M5-B bridge state for"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Print the machine-readable M5 connector contract"
    ),
):
    """Show the M5 remote-connector contract without claiming it is live."""
    root_path = Path(root).expanduser().resolve()
    contract = build_connector_contract(root_path)
    # Additive only (M5-D): the same continuity receipt `hyodo mcp continuity`
    # measures, folded to the two facts this contract already distinguishes —
    # the local truth store and the still-unprobed remote connector.
    continuity_receipt = measure_continuity(root_path)
    contract["continuity"] = {
        "local": "OBSERVED" if continuity_receipt["status"] == "READY" else "UNOBSERVED",
        "remote": continuity_receipt["remote"]["status"],
    }
    if json_output:
        console.print_json(json.dumps(contract))
        return

    console.print(Panel.fit("HyoDo M5 Connector Contract", style="bold cyan"))
    console.print(f"  status:       {contract['status']}")
    console.print(f"  availability: {contract['availability']}")
    console.print(f"  url:          {contract['connector']['url']}")
    console.print(f"  auth:         {contract['connector']['auth']}")
    console.print(
        f"  bridge:       pairing={contract['bridge']['pairing']} "
        f"listener={contract['bridge']['listener']}"
    )
    console.print("[yellow]Contract only: the remote connector is not live.[/yellow]")


@mcp_app.command("pair")
def mcp_pair(
    root: str = typer.Option(".", "--root", help="Workspace root to pair for the M5-B bridge"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """Create (or replace) a pairing for this workspace and print the bearer token once.

    The token is never written to disk — only its sha256 digest is. This is
    the only time the token is shown; it cannot be recovered later.
    """
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        reason = f"workspace root is not a directory: {root_path}"
        payload = {"ok": False, "reasons": [reason], "exit_code": 2}
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]{reason}[/red]")
        raise typer.Exit(2)

    record, token = create_pairing(root_path)
    pairing_file = root_path / PAIRING_RELATIVE_PATH
    if json_output:
        payload = {
            "ok": True,
            "reasons": [],
            "exit_code": 0,
            "workspace_id": record.workspace_id,
            "device_id": record.device_id,
            "root": record.root,
            "pairing_file": str(pairing_file),
            "token": token,
        }
        console.print_json(json.dumps(payload))
    else:
        console.print("[green]PAIRED[/green]")
        console.print(f"  workspace_id: {record.workspace_id}")
        console.print(f"  root:         {record.root}")
        console.print(f"  pairing_file: {pairing_file}")
        console.print(f"  token:        {token}")
        console.print(
            "[yellow]This token is shown once and is never stored — save it now. "
            "Use it as the bearer token against `hyodo mcp serve --paired`.[/yellow]"
        )
    raise typer.Exit(0)


def _mcp_revoke(
    root: str = typer.Option(".", "--root", help="Workspace root to revoke pairing for"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """Revoke the current pairing; the bridge stops accepting its token immediately."""
    root_path = Path(root).expanduser().resolve()
    state = pairing_state(root_path)
    if state in (PairingState.UNPAIRED, PairingState.UNOBSERVED):
        reason = "pairing_missing" if state is PairingState.UNPAIRED else "pairing_invalid"
        payload = {"ok": False, "reasons": [reason], "state": state.value, "exit_code": 2}
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]{state.value}[/red] — nothing to revoke ({reason})")
        raise typer.Exit(2)

    record = revoke_pairing(root_path)
    assert record is not None  # state was PAIRED or REVOKED, so a valid record exists
    payload = {
        "ok": True,
        "reasons": [],
        "state": "REVOKED",
        "workspace_id": record.workspace_id,
        "revoked_at": record.revoked_at,
        "exit_code": 0,
    }
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        console.print("[green]REVOKED[/green]")
        console.print(f"  workspace_id: {record.workspace_id}")
        console.print(f"  revoked_at:   {record.revoked_at}")
    raise typer.Exit(0)


# Registered under both names: `revoke` is the primary verb used in the M5-B
# receipts, `unpair` is the more familiar counterpart to `pair`. Both run the
# same idempotent revoke.
mcp_app.command("unpair")(_mcp_revoke)
mcp_app.command("revoke")(_mcp_revoke)


@pairing_app.command("show")
def mcp_pairing_show(
    root: str = typer.Option(".", "--root", help="Workspace root to inspect pairing state for"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """Show the current pairing state for this workspace. Never prints the token."""
    root_path = Path(root).expanduser().resolve()
    state = pairing_state(root_path)
    record = load_pairing(root_path)
    payload = {
        "ok": state is PairingState.PAIRED,
        "state": state.value,
        "workspace_id": record.workspace_id if record is not None else None,
        "device_id": record.device_id if record is not None else None,
        "root": record.root if record is not None else None,
        "created_at": record.created_at if record is not None else None,
        "revoked_at": record.revoked_at if record is not None else None,
        "last_seen_at": record.last_seen_at if record is not None else None,
        "pairing_file": str(root_path / PAIRING_RELATIVE_PATH),
        "exit_code": 0 if state is PairingState.PAIRED else 2,
    }
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        color = {"PAIRED": "green", "REVOKED": "yellow", "UNPAIRED": "yellow"}.get(
            state.value, "red"
        )
        console.print(f"[{color}]{state.value}[/{color}]")
        if record is not None:
            console.print(f"  workspace_id: {record.workspace_id}")
            console.print(f"  root:         {record.root}")
            console.print(f"  last_seen_at: {record.last_seen_at}")
    raise typer.Exit(payload["exit_code"])


@mcp_app.command("stdio")
def mcp_stdio(
    root: str = typer.Option(".", "--root", help="Workspace root locked for this MCP process"),
    allow_full_body: bool = typer.Option(
        False,
        "--allow-full-body",
        help=(
            "Operator consent: permit clients to store raw prompt/output text. "
            "Off by default — clients cannot turn this on themselves."
        ),
    ),
):
    """Run the optional local MCP adapter over standard input/output."""
    try:
        from hyodo._mcp_compat import get_mcp_server_class

        # Resolve the installed SDK major (v1 FastMCP / v2 MCPServer) up front so
        # a missing install reports clearly and a v2 install is not misread as
        # a broken one.
        get_mcp_server_class()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.mcp_server import run_stdio

    try:
        run_stdio(Path(root), allow_full_body=allow_full_body)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


@mcp_app.command("serve")
def mcp_serve(
    bind: str = typer.Option("loopback", "--bind", help="loopback or tailscale"),
    bind_ip: str | None = typer.Option(
        None,
        "--bind-ip",
        help="Required Tailscale IPv4 address for --bind tailscale",
    ),
    port: int = typer.Option(8769, "--port", min=1024, max=65535, help="MCP port"),
    root: str = typer.Option(".", "--root", help="Workspace root locked for this MCP server"),
    token: str | None = typer.Option(
        None,
        "--token",
        envvar="HYODO_MCP_TOKEN",
        help="Optional for loopback; required and non-empty for Tailscale (ignored with --paired)",
    ),
    paired: bool = typer.Option(
        False,
        "--paired",
        help=(
            "Verify the caller's bearer token against `.hyodo/pairing.json` instead of a "
            "static --token; every request re-reads the pairing so a revoke takes effect "
            "immediately"
        ),
    ),
):
    """Explicitly serve the optional MCP adapter on loopback or Tailscale."""
    if bind not in {"loopback", "tailscale"}:
        console.print("[red]Only --bind loopback or --bind tailscale is available.[/red]")
        raise typer.Exit(2)
    if bind == "loopback" and bind_ip is not None:
        console.print("[red]--bind-ip is only available with --bind tailscale.[/red]")
        raise typer.Exit(2)
    if port == 8768:
        console.print("[red]Port 8768 is reserved for the HyoDo dashboard.[/red]")
        raise typer.Exit(2)
    if paired and token is not None:
        console.print(
            "[red]--paired verifies the bearer token against `.hyodo/pairing.json`; "
            "do not also pass --token.[/red]"
        )
        raise typer.Exit(2)
    tailscale_ip = None
    if bind == "tailscale":
        if bind_ip is None:
            console.print(
                "[red]--bind tailscale requires --bind-ip with this host's Tailscale address.[/red]"
            )
            raise typer.Exit(2)
        try:
            candidate = ipaddress.ip_address(bind_ip)
        except ValueError:
            candidate = None
        if not isinstance(
            candidate, ipaddress.IPv4Address
        ) or candidate not in ipaddress.ip_network("100.64.0.0/10"):
            console.print("[red]--bind-ip must be a Tailscale 100.64.0.0/10 address.[/red]")
            raise typer.Exit(2)
        if not paired and (token is None or not token.strip()):
            console.print(
                "[red]--bind tailscale requires a non-empty bearer token before listening.[/red]"
            )
            raise typer.Exit(2)
        tailscale_ip = str(candidate)
    try:
        from hyodo._mcp_compat import get_mcp_server_class

        # Same probe as `mcp stdio`: works on both SDK majors.
        get_mcp_server_class()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.mcp_server import run_loopback, run_tailscale

    try:
        root_path = Path(root)
        # Resolve before printing an address so a failed root never resembles a live connector.
        from hyodo.mcp_server import resolve_workspace_root

        resolve_workspace_root(root_path)
        host = tailscale_ip or "127.0.0.1"
        console.print("HyoDo MCP connector ready")
        console.print(f"  transport: {bind}")
        console.print(f"  url:       http://{host}:{port}/mcp")
        console.print(f"  workspace: {root_path.expanduser().resolve()}")
        if paired:
            console.print("  auth:      paired (bearer token verified against pairing record)")
        else:
            console.print(
                "  auth:      bearer token configured"
                if token
                else "  auth:      local process trust"
            )
        if bind == "tailscale":
            run_tailscale(root_path, host=host, port=port, token=token or "", paired=paired)
        else:
            run_loopback(root_path, port=port, token=token, paired=paired)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


@mcp_app.command("doctor")
def mcp_doctor(
    root: str = typer.Option(".", "--root", help="Workspace root to validate"),
    port: int = typer.Option(8769, "--port", min=1024, max=65535, help="MCP port to check"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Diagnose the local MCP setup without starting a server.

    Checks: MCP SDK availability, workspace root, port availability,
    dashboard port conflict, and Tailscale connectivity.  Exits 0
    regardless of problems found — doctor reports, it never blocks.
    """
    import socket as _socket

    from hyodo._mcp_compat import get_mcp_server_class

    # ── MCP SDK availability ──────────────────────────────────────────
    mcp_sdk_available = True
    mcp_sdk_version: str | None = None
    try:
        get_mcp_server_class()
        import mcp  # pyright: ignore[reportMissingImports]

        mcp_sdk_version = getattr(mcp, "__version__", None)
    except ModuleNotFoundError:
        mcp_sdk_available = False

    # ── Workspace root ────────────────────────────────────────────────
    root_path = Path(root).expanduser().resolve()
    workspace_ok = root_path.is_dir()
    workspace_path = str(root_path)

    # ── Port availability ────────────────────────────────────────────
    dashboard_reserved = port == 8768
    port_free = True
    if not dashboard_reserved:
        probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        probe.settimeout(0.5)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            port_free = False
        finally:
            probe.close()

    # ── Tailscale check (best-effort) ────────────────────────────────
    tailscale_up = False
    tailscale_ip: str | None = None
    try:
        ts_result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, OSError):
        ts_result = None
    if ts_result is not None and ts_result.returncode == 0:
        try:
            ts_data = json.loads(ts_result.stdout)
            tailscale_up = ts_data.get("Online", False)
            tailscale_ip = ts_data.get("TailscaleIPs", [None])[0]
        except (json.JSONDecodeError, TypeError):
            pass

    # ── Render ───────────────────────────────────────────────────────
    if json_output:
        payload = {
            "mcp_sdk": {
                "available": mcp_sdk_available,
                "version": mcp_sdk_version,
            },
            "workspace": {
                "path": workspace_path,
                "valid": workspace_ok,
            },
            "port": {
                "number": port,
                "free": port_free,
                "dashboard_reserved": dashboard_reserved,
            },
            "tailscale": {
                "up": tailscale_up,
                "ip": tailscale_ip,
            },
        }
        console.print_json(json.dumps(payload))
    else:
        # MCP SDK
        if mcp_sdk_available:
            label = f"[green]available[/green] ({mcp_sdk_version or 'version unknown'})"
        else:
            label = "[red]missing[/red] — install with: pip install 'hyodo[mcp]'"
        console.print(f"mcp-sdk:    {label}")

        # Workspace
        if workspace_ok:
            console.print(f"workspace:  [green]valid[/green] ({workspace_path})")
        else:
            console.print(f"workspace:  [red]missing[/red] — {workspace_path} is not a directory")

        # Port
        if dashboard_reserved:
            console.print(
                "port:       [red]reserved[/red] — 8768 is reserved for the HyoDo dashboard"
            )
        elif port_free:
            console.print(f"port:       [green]available[/green] (:{port})")
        else:
            console.print(f"port:       [red]in use[/red] (:{port}) — another process is listening")

        # Tailscale
        if tailscale_up:
            console.print(f"tailscale:  [green]up[/green] ({tailscale_ip})")
        else:
            console.print("tailscale:  [dim]not connected or not installed[/dim]")

    raise typer.Exit(0)


@mcp_app.command("config")
def mcp_config_cmd(
    host: str = typer.Argument(
        ...,
        help="MCP host: " + ", ".join(MCP_HOSTS) + " (chatgpt reports UNOBSERVED - not live)",
    ),
    root: str = typer.Option(
        ".", "--root", help="Workspace root the stdio adapter locks to (resolved to absolute)"
    ),
    write: bool = typer.Option(
        False, "--write", help="Merge the entry into the host's config file (default: print only)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """
    Print (or, with ``--write``, merge) the MCP client configuration that
    registers HyoDo's local stdio adapter for one host.

    No bearer token or secret ever appears here - the stdio adapter needs
    none. Default is print-only; ``--write`` merges the entry key-level into
    the host's config file, preserving any other servers already there. A
    file HyoDo did not create itself gets a ``.bak`` alongside it on its
    first write; running ``--write`` twice with no other change makes no
    further edits.

    Exit codes: print-only is always 0 unless the host is unknown or
    ``chatgpt`` (2, UNOBSERVED - the remote connector is not live).
    ``--write``: 0 on success (including "already up to date"), 2 on an
    unknown/unobserved host or a write error.
    """
    root_path = Path(root).expanduser().resolve()

    if host in ALL_HOSTS and host not in MCP_HOSTS:
        # Only member today is "chatgpt"; kept as a set membership check so a
        # future UNOBSERVED host does not need a second code path.
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "ok": False,
                        "reasons": ["remote_not_probed"],
                        "exit_code": 2,
                        "host": host,
                        "message": CHATGPT_UNOBSERVED_MESSAGE,
                    }
                )
            )
        else:
            console.print(f"[yellow]UNOBSERVED[/yellow] {host}: {CHATGPT_UNOBSERVED_MESSAGE}")
        raise typer.Exit(2)

    if host not in MCP_HOSTS:
        message = f"unknown host: {host}. Known hosts: {', '.join(ALL_HOSTS)}"
        if json_output:
            console.print_json(
                json.dumps(
                    {"ok": False, "reasons": ["unknown_host"], "exit_code": 2, "message": message}
                )
            )
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    plan = write_host(host, root_path) if write else plan_host(host, root_path)

    if json_output:
        payload: dict[str, Any] = {
            "ok": True,
            "reasons": [],
            "exit_code": 0,
            "host": host,
            "path": str(plan.path),
            "status": plan.status,
            "write": write,
            "verified": plan.verified,
            "existed_before": plan.existed_before,
            "will_change": plan.will_change,
        }
        if not write:
            payload["content"] = plan.content
        if plan.deep_links:
            payload["deep_links"] = plan.deep_links
            payload["deep_link_label"] = DEEP_LINK_LABEL
        console.print_json(json.dumps(payload))
        raise typer.Exit(0)

    verb = "wrote" if write else "would write"
    if plan.status == "up_to_date":
        console.print(f"[green]up to date[/green] {host}: {plan.message}")
    else:
        scope = " (global, not project-scoped)" if host in {"codex", "claude-desktop"} else ""
        console.print(
            f"[cyan]{rich_escape(str(host))}[/cyan] {verb}: {rich_escape(str(plan.path))}{scope}"
        )
        console.print("  ---")
        for line in plan.content.splitlines():
            # markup=False: raw file content (TOML table headers like
            # "[mcp_servers.hyodo]") must never be parsed as Rich markup -
            # that would silently strip the line from the preview.
            console.print(f"  {line}", markup=False)
        console.print("  ---")
    if not plan.verified:
        console.print(f"[yellow]{UNVERIFIED_FORMAT_LABEL}[/yellow]")
    for name in DEEP_LINK_HOSTS:
        link = plan.deep_links.get(name)
        if link:
            console.print(f"[dim]{name} deep link ({DEEP_LINK_LABEL}):[/dim]\n  {link}")
    raise typer.Exit(0)


@rules_app.command("list")
def rules_list(
    root: str = typer.Option(".", "--root", help="Workspace root directory"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """List active agent rules from .hyodo/agent-rules.toml (or defaults if missing)."""
    from hyodo._mcp_compat import get_mcp_server_class

    try:
        get_mcp_server_class()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.agent_rules import DEFAULT_RULES, load_agent_rules

    root_path = Path(root).expanduser().resolve()
    rules = load_agent_rules(root_path)
    if not rules:
        rules = list(DEFAULT_RULES)

    if json_output:
        console.print_json(json.dumps([r.to_dict() for r in rules]))
    else:
        if not rules:
            console.print("[dim]No agent rules configured.[/dim]")
        for rule in rules:
            status = "[green]on[/green]" if rule.enabled else "[dim]off[/dim]"
            scope_label = rule.scope
            console.print(f"  {rule.name} ({scope_label}, {status})")
            console.print(f"    {rule.description}")
    raise typer.Exit(0)


@rules_app.command("init")
def rules_init(
    root: str = typer.Option(".", "--root", help="Workspace root directory"),
) -> None:
    """Write default agent rules to .hyodo/agent-rules.toml (idempotent, preserves existing)."""
    from hyodo._mcp_compat import get_mcp_server_class

    try:
        get_mcp_server_class()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.agent_rules import AGENT_RULES_PATH, DEFAULT_RULES, save_agent_rules

    root_path = Path(root).expanduser().resolve()
    rules_file = root_path / AGENT_RULES_PATH
    if rules_file.exists():
        console.print(f"[dim]Agent rules already exist at {rules_file} — skipping.[/dim]")
        raise typer.Exit(0)

    save_agent_rules(root_path, list(DEFAULT_RULES))
    console.print(f"[green]Created[/green] {rules_file} with {len(DEFAULT_RULES)} default rules.")
    raise typer.Exit(0)


@mcp_app.command("access-log")
def mcp_access_log(
    root: str = typer.Option(
        ".", "--root", help="Workspace root that owns .hyodo/mcp-access.jsonl"
    ),
    limit: int = typer.Option(100, "--limit", min=1, max=10000, help="Maximum entries to show"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Display the MCP access ledger (audit trail of tool invocations)."""
    try:
        from hyodo._mcp_compat import (
            get_mcp_server_class,  # pyright: ignore[reportAttributeAccessIssue]
        )

        get_mcp_server_class()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.access_ledger import read_access_log

    root_path = Path(root).expanduser().resolve()
    entries = read_access_log(root_path, limit=limit)

    if json_output:
        from dataclasses import asdict

        console.print_json(json.dumps([asdict(e) for e in entries]))
    elif not entries:
        console.print("[dim]No access log entries found.[/dim]")
    else:
        table = Table(title="MCP Access Log", show_lines=True)
        table.add_column("Timestamp", style="dim")
        table.add_column("Tool", style="cyan")
        table.add_column("Root")
        table.add_column("Exit", justify="right")
        table.add_column("Duration (ms)", justify="right")
        table.add_column("Caller", style="dim")
        for entry in entries:
            table.add_row(
                entry.timestamp,
                entry.tool_name,
                entry.root,
                str(entry.exit_code),
                str(entry.duration_ms),
                entry.caller_id or "",
            )
        console.print(table)

    raise typer.Exit(0)


@mcp_app.command("continuity")
def mcp_continuity(
    root: str = typer.Option(
        ".", "--root", help="Workspace root to measure the M5-D continuity receipt for"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit the machine-readable receipt"),
) -> None:
    """Show whether this workspace's local truth stores are one consistent store.

    Read-only: measures the agent-event ledger, the optional policy file, the
    MCP access ledger, and the optional pairing file, plus the distinct
    hosts observed from two sources: MCP callers recorded in the access
    ledger, and hook-recorded actors (``actor_id`` on agent-event ledger
    rows, e.g. from ``hyodo connect claude-code``) — a host wired only
    through hooks counts even though it never touches the access ledger,
    and a shadow-mode event still counts as observed. Remote (ChatGPT/the
    hosted connector) is always reported UNOBSERVED — this command never
    probes it.

    Integrity and coverage are reported separately: ``integrity_status`` is
    READY when every present store parses, CORRUPT otherwise. `coverage_status`
    is OBSERVED when enough hosts were seen and the required stores are
    present and readable, PARTIAL when some but not all of that holds, and
    UNOBSERVED when nothing has been observed yet (an empty workspace).
    Overall `status`/exit code stay READY/0 only when both are satisfied;
    otherwise UNOBSERVED/2 — an empty root is a false negative worth seeing,
    never a silent READY.

    `reasons` drives `status`: once coverage reaches OBSERVED through
    hook-only hosts, store-absence facts stop appearing there so a
    hook-observed root can reach READY. Those facts are never dropped
    though — `notes` always lists every store that is genuinely absent
    (`access_ledger_absent`, `pairing_absent`, `policy_absent`,
    `agent_events_absent`), plus `hook_only_observation` when every
    observed host came from hooks and none from the MCP access ledger.
    """
    root_path = Path(root).expanduser().resolve()
    receipt = measure_continuity(root_path)
    if json_output:
        console.print_json(json.dumps(receipt))
        raise typer.Exit(receipt["exit_code"])

    color = "green" if receipt["status"] == "READY" else "red"
    console.print(f"[{color}]{receipt['status']}[/{color}] continuity: {root_path}")
    console.print(f"  integrity: {receipt['integrity_status']}")
    console.print(f"  coverage:  {receipt['coverage_status']}")
    console.print(f"  {receipt['hosts']['label']}")
    by_source = receipt["hosts"]["by_source"]
    console.print(f"  hosts by source: mcp={by_source['mcp']} hook={by_source['hook']}")
    for store_name, store in receipt["stores"].items():
        state = "present" if store["exists"] else "absent"
        if not store["readable"]:
            state = "unreadable"
        console.print(f"  {store_name}: {state} digest={store['digest']}")
    for caller in receipt["callers"]:
        source = caller.get("source", "mcp")
        if source == "hook":
            console.print(
                f"  caller: {caller['identity']} source=hook calls={caller['calls']} "
                f"shadow={caller['shadow']}"
            )
        else:
            tools = ", ".join(caller["tools"]) or "none"
            console.print(
                f"  caller: {caller['identity']} source=mcp calls={caller['calls']} tools=[{tools}]"
            )
    console.print(
        f"  remote: {receipt['remote']['status']} ({receipt['remote']['reason']})",
        style="yellow",
    )
    if receipt["reasons"]:
        console.print(f"[red]reasons: {', '.join(receipt['reasons'])}[/red]")
    if receipt["notes"]:
        console.print(f"[yellow]notes: {', '.join(receipt['notes'])}[/yellow]")
    raise typer.Exit(receipt["exit_code"])


@schema_app.command("check")
def schema_check(
    schema: str = typer.Option(..., "--schema", help="Path to a JSON Schema document"),
    payload: str = typer.Option(..., "--payload", help="Path to a JSON payload document"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON {ok, reasons, exit_code}",
    ),
):
    """Validate one JSON payload against one JSON Schema document.

    Exit 0 means valid, 1 means a validation failure, and 2 means an input or
    schema observation failure. It never treats an unobserved input as valid.
    """
    ok, exit_code, reasons = validate_schema_payload(Path(schema), Path(payload))
    machine = {"ok": ok, "reasons": reasons, "exit_code": exit_code}
    if json_output:
        console.print_json(json.dumps(machine))
    elif ok:
        console.print("[green]VALID[/green] JSON Schema payload")
    else:
        label = "INVALID" if exit_code == 1 else "UNOBSERVED"
        console.print(f"[red]{label}[/red] JSON Schema validation")
        for reason in reasons:
            console.print(f"  - {reason['code']}: {reason['message']}")
    raise typer.Exit(exit_code)


@app.command("eval")
def eval_command(
    dataset: str = typer.Option(..., "--dataset", help="Path to a golden JSONL dataset"),
    runner: str = typer.Option(..., "--runner", help="Local command run once per dataset case"),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/eval-runs"),
    min_pass_rate: float = typer.Option(
        1.0,
        "--min-pass-rate",
        min=0.0,
        max=1.0,
        help="Minimum passing-case fraction required for exit 0",
    ),
    timeout_seconds: int = typer.Option(
        30,
        "--timeout-seconds",
        min=1,
        max=600,
        help="Maximum runner time for one case",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable run summary"),
):
    """Run a local golden dataset with deterministic built-in scoring.

    The runner receives ``{\"id\": ..., \"input\": ...}`` as JSON on stdin and
    must print JSON, either directly or as ``{\"output\": ...}``. Runner failures
    are recorded as failed eval runs; they are never counted as skips.
    """
    try:
        exit_code, summary = run_evaluation(
            Path(dataset), runner, Path(root).resolve(), min_pass_rate, timeout_seconds
        )
    except EvalInputError as exc:
        summary = {"status": "UNOBSERVED", "reason": str(exc)}
        exit_code = 2
    if json_output:
        console.print_json(json.dumps(summary))
    elif exit_code == 0:
        console.print(f"[green]PASS[/green] eval ({summary['pass_rate']:.1%})")
    elif exit_code == 1:
        console.print("[red]FAIL[/red] eval")
        failure = summary.get("runner_failure")
        if isinstance(failure, dict) and isinstance(failure.get("code"), str):
            console.print(f"  runner: {failure['code']}")
    else:
        console.print(f"[red]UNOBSERVED[/red] eval: {summary['reason']}")
    raise typer.Exit(exit_code)


@app.command("report")
def report_command(
    report_format: str = typer.Option(
        "md", "--format", help="Local report format: md, html, sarif, or graph"
    ),
    root: str = typer.Option(".", "--root", help="Project root that owns local evidence"),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable report summary"
    ),
):
    """Render a local FDE sign-off report from observed evidence only."""
    if report_format not in {"md", "html", "sarif", "graph"}:
        console.print("[red]--format must be md, html, sarif, or graph[/red]")
        raise typer.Exit(2)
    exit_code, summary = write_report(Path(root).resolve(), report_format)
    if json_output:
        console.print_json(json.dumps(summary))
    elif exit_code == 0:
        console.print(f"[green]READY[/green] report: {summary['result_path']}")
        console.print(f"  hash: {summary['report_hash']}")
    else:
        console.print(f"[red]UNOBSERVED[/red] report: {summary['reason']}")
    raise typer.Exit(exit_code)


def _load_event_payload(
    file: Path | None,
    stdin_flag: bool,
) -> tuple[object | None, str | None]:
    """Load event JSON from --file or stdin. Returns (data, error_code)."""
    if stdin_flag and file is not None:
        return None, "file_and_stdin"
    if stdin_flag:
        text = sys.stdin.read()
        return load_event_from_text(text)
    if file is None:
        return None, "missing_input"
    return load_event_from_path(file)


_NATIVE_HOOKS = frozenset({"claude-code", "cursor", "codex"})


def _map_hook_payload(
    payload: object, root: Path, hook: str
) -> tuple[MappedHookEvent | None, str | None]:
    """Select the host adapter without duplicating event-recording logic."""
    if hook == "claude-code":
        return map_claude_code_hook_payload(payload, root)
    if hook == "cursor":
        return map_cursor_hook_payload(payload, root)
    if hook == "codex":
        return map_codex_hook_payload(payload, root)
    return None, "unsupported_hook"


def _unobserved_policy_decision(
    event: dict[str, Any],
    policy_err: str | None,
    *,
    hook: str | None,
    observed_steps: int | None,
    root: Path | None,
) -> PolicyDecision:
    """Build the UNOBSERVED decision for a policy.toml that failed to load.

    Fail-closed is unchanged here: the decision is always UNOBSERVED, never a
    silent ALLOW. Under ``--hook claude-code`` with a *missing* (not invalid)
    policy file, the event is first evaluated against the same permissive
    all-defaults ``PolicyConfig`` that ``skills ingest`` and ``eye capture``
    already fall back to -- so ``coverage``/``trust_level`` reflect a real
    evaluation -- but the decision label itself is forced back to UNOBSERVED
    with reason ``policy_missing``: an absent policy file is not the same
    thing as an explicit permissive policy, so it must still be recorded as
    unobserved rather than crash before anything is recorded.
    """
    if hook in _NATIVE_HOOKS and policy_err == "policy_missing":
        default_cfg = PolicyConfig(
            schema=POLICY_SCHEMA_ID,
            max_steps=None,
            allowed_tools=None,
            blocked_path_globs=(),
        )
        probe = evaluate_policy(event, default_cfg, observed_steps=observed_steps, root=root)
        return replace(probe, decision="UNOBSERVED", reason="policy_missing")
    return PolicyDecision(
        decision="UNOBSERVED",
        rule_id=None,
        reason=policy_err or "policy_unobserved",
    )


@event_app.command("validate")
def event_validate(
    file: str | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to a JSON agent event (hyodo.agent-event/v1)",
    ),
    stdin_flag: bool = typer.Option(
        False,
        "--stdin",
        help="Read event JSON from stdin instead of --file",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON {ok, reasons}",
    ),
):
    """
    Validate one agent event against hyodo.agent-event/v1.

    Exit: 0 valid · 1 invalid · 2 unreadable / missing input.
    Does not write the ledger.
    """
    file_path = Path(file) if file else None
    data, err = _load_event_payload(file_path, stdin_flag)
    if err == "file_and_stdin":
        msg = "Use either --file or --stdin, not both."
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": [err], "exit_code": 2}))
        else:
            console.print(f"[red]{msg}[/red]")
        raise typer.Exit(2)
    if err == "missing_input":
        msg = "Provide --file PATH or --stdin."
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": [err], "exit_code": 2}))
        else:
            console.print(f"[red]{msg}[/red]")
        raise typer.Exit(2)
    if err is not None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": [err], "exit_code": 2}))
        else:
            console.print(f"[red]Cannot load event: {err}[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2)

    ok, reasons, _normalized = validate_event(data)
    if json_output:
        console.print_json(json.dumps({"ok": ok, "reasons": reasons, "exit_code": 0 if ok else 1}))
    elif ok:
        console.print("[green]VALID[/green] hyodo.agent-event/v1")
    else:
        console.print("[red]INVALID[/red] event")
        for reason in reasons:
            console.print(f"  - {reason}")
    raise typer.Exit(0 if ok else 1)


@observation_app.command("record")
def observation_record(
    file: str | None = typer.Option(
        None, "--file", "-f", help="Path to a JSON orchestration observation"
    ),
    stdin_flag: bool = typer.Option(
        False, "--stdin", help="Read observation JSON from stdin instead of --file"
    ),
    root: str = typer.Option(".", "--root", help="Project root holding .hyodo/"),
    json_out: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
) -> None:
    """Record one sidecar orchestration observation.

    An observation describes how execution was shaped -- serial or parallel,
    what a node waited for -- without becoming an event. It lands in its own
    file beside the agent ledger and never inside it, so a dependency can
    never be mistaken for something that happened.

    Refused rather than stored when it does not validate: a sidecar that
    accepts anything would make the dependency graph unfalsifiable.
    """
    if file and stdin_flag:
        typer.echo("ERROR: use either --file or --stdin, not both", err=True)
        raise typer.Exit(2)
    try:
        if stdin_flag:
            payload_text = sys.stdin.read()
        elif file:
            payload_text = Path(file).read_text(encoding="utf-8")
        else:
            typer.echo("ERROR: one of --file or --stdin is required", err=True)
            raise typer.Exit(2)
    except OSError:
        typer.echo("ERROR: observation input could not be read", err=True)
        raise typer.Exit(2) from None

    try:
        raw = json.loads(payload_text)
    except json.JSONDecodeError:
        typer.echo("ERROR: observation is not valid JSON", err=True)
        raise typer.Exit(2) from None

    ok, reasons, normalized = validate_orchestration_observation(raw)
    if not ok or normalized is None:
        if json_out:
            typer.echo(json.dumps({"recorded": False, "reasons": reasons}, sort_keys=True))
        else:
            typer.echo(f"ERROR: observation rejected: {', '.join(reasons)}", err=True)
        raise typer.Exit(2)

    if not append_orchestration_observation(Path(root), normalized):
        typer.echo("ERROR: observation could not be written", err=True)
        raise typer.Exit(2)

    if json_out:
        typer.echo(
            json.dumps(
                {"recorded": True, "observation_id": normalized["observation_id"]},
                sort_keys=True,
            )
        )
    else:
        typer.echo(f"RECORDED {normalized['observation_id']}")


@event_app.command("record")
def event_record(
    file: str | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to a JSON agent event (hyodo.agent-event/v1)",
    ),
    stdin_flag: bool = typer.Option(
        False,
        "--stdin",
        help="Read event JSON from stdin instead of --file",
    ),
    root: str = typer.Option(
        ".",
        "--root",
        help="Project root that owns .hyodo/agent-events.jsonl",
    ),
    policy: str | None = typer.Option(
        None,
        "--policy",
        help="Optional policy.toml; when set, DENY is recorded and exit 1",
    ),
    full_body: bool = typer.Option(
        False,
        "--full-body",
        help="Keep io.input_text/output_text when present (default: digest-only)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON receipt",
    ),
    hook: str | None = typer.Option(
        None,
        "--hook",
        help="Adapt stdin from a harness-native hook JSON shape instead of "
        "hyodo.agent-event/v1 (claude-code, cursor, or codex)",
    ),
    native_response: bool = typer.Option(
        False,
        "--native-response",
        help="Emit the host-native response envelope for Cursor or Codex.",
    ),
    shadow: bool = typer.Option(
        False,
        "--shadow",
        help="Stamp policy.shadow=true on the recorded event (shadow-mode "
        "on-ramp installed by `hyodo connect --shadow`)",
    ),
    actor_id: str | None = typer.Option(
        None,
        "--actor-id",
        help="Opaque label (session id, seat name, model alias) for this "
        "actor; sets actor_id when the event JSON does not already carry "
        "one. HyoDo never derives identity from it.",
    ),
    audience: str | None = _audience_option(),
):
    """
    Validate and append one agent event to .hyodo/agent-events.jsonl.

    Default storage is digest-only (strips full text bodies). Use --full-body
    only when the operator accepts retaining raw payloads.

    With --policy: evaluate policy, stamp policy.* on the event, always try to
    append (including DENY) for audit continuity. Exit 1 on DENY or invalid
    event; exit 2 when input/policy path is unreadable or policy is unobserved;
    exit 3 on ASK (operator decision required). With ``--hook claude-code``
    this command plays the fire-and-forget PostToolUse role: it always exits 0
    once the event is appended (regardless of the recorded decision), and
    non-zero only when the ledger append itself fails. ``--shadow`` requires
    ``--policy`` (there is no decision to shadow-stamp without one) and stamps
    ``policy.shadow: true`` instead of changing the exit code — the honest exit
    for a fire-and-forget hook is already 0.

    HyoDo is a gate, not an agent runtime — callers must enforce DENY.
    """
    if shadow and policy is None:
        message = "--shadow requires --policy (nothing to shadow-stamp without a decision)"
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": [message], "exit_code": 2}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    root_path = Path(root).resolve()
    profile = _resolve_audience_or_exit(root_path, audience, "event record --policy", json_output)
    file_path = Path(file) if file else None
    data, err = _load_event_payload(file_path, stdin_flag)
    if err in {"file_and_stdin", "missing_input"} or err is not None:
        if policy is not None and not json_output:
            typer.echo(
                render_verdict_line(
                    "UNOBSERVED",
                    0,
                    0,
                    "surfaces",
                    "trust=UNOBSERVED, event UNOBSERVED",
                    audience=profile.profile,
                )
            )
        code = 2
        reasons = [err or "load_failed"]
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": code}))
        else:
            console.print(f"[red]Cannot load event: {err}[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(code)

    if hook is not None:
        if hook not in _NATIVE_HOOKS:
            message = f"unsupported --hook value: {hook}"
            if json_output:
                console.print_json(json.dumps({"ok": False, "reasons": [message], "exit_code": 2}))
            else:
                console.print(f"[red]{message}[/red]")
            raise typer.Exit(2)
        mapped, map_err = _map_hook_payload(data, root_path, hook)
        if mapped is None:
            mapping_exit = 0 if shadow else 2
            if json_output:
                console.print_json(
                    json.dumps(
                        {
                            "ok": False,
                            "reasons": [map_err],
                            "exit_code": mapping_exit,
                            "shadow": shadow,
                        }
                    )
                )
            else:
                console.print(f"[red]Cannot map {hook} hook payload: {map_err}[/red]")
            stderr_prefix = "[SHADOW, not blocking] " if shadow else ""
            typer.echo(
                f"{stderr_prefix}HYODO UNOBSERVED: malformed hook payload; treating as "
                "blocked, not allowed.",
                err=True,
            )
            raise typer.Exit(mapping_exit)
        data = mapped.raw
        root_path = mapped.root

    if actor_id is not None and isinstance(data, dict) and not data.get("actor_id"):
        data["actor_id"] = actor_id

    ok, reasons, normalized = validate_event(data)
    if not ok or normalized is None:
        if policy is not None and not json_output:
            typer.echo(
                render_verdict_line(
                    "UNOBSERVED",
                    0,
                    0,
                    "surfaces",
                    "trust=UNOBSERVED, valid event UNOBSERVED",
                    audience=profile.profile,
                )
            )
        # A PostToolUse hook is fire-and-forget: it can never block, so an
        # unrecordable event exits 0 there and is reported as UNOBSERVED.
        code = 0 if hook in _NATIVE_HOOKS else 1
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": code}))
        else:
            console.print("[red]INVALID[/red] event — not recorded")
            for reason in reasons:
                console.print(f"  - {reason}")
            if hook in _NATIVE_HOOKS:
                console.print("HYODO UNOBSERVED: event not recorded (fire-and-forget hook)")
        raise typer.Exit(code)

    if not full_body:
        normalized = strip_full_bodies(normalized)

    decision_label = None
    ledger_obligation: dict[str, bool] = {}
    if policy is not None:
        cfg, policy_err = try_load_policy(Path(policy))
        if cfg is None:
            # Fail-closed: missing/invalid policy is unobserved, never ALLOW. When
            # neither --shadow nor --hook claude-code is set, this remains the
            # honest crash-before-recording it always was (no event to fall back
            # to for a caller that isn't fire-and-forget and isn't asking to be
            # non-blocking). Under --shadow or --hook claude-code, though, the
            # event must still be recorded (fire-and-forget/shadow never blocks),
            # so build an UNOBSERVED decision and fall through to the normal
            # stamp-and-append path below instead of exiting here.
            if not (shadow or hook == "claude-code"):
                if not json_output:
                    typer.echo(
                        render_verdict_line(
                            "UNOBSERVED",
                            0,
                            0,
                            "surfaces",
                            "trust=UNOBSERVED, policy UNOBSERVED",
                            audience=profile.profile,
                        )
                    )
                if json_output:
                    console.print_json(
                        json.dumps(
                            {
                                "ok": False,
                                "reasons": [policy_err or "policy_unobserved"],
                                "exit_code": 2,
                            }
                        )
                    )
                else:
                    console.print(
                        f"[red]Policy unobserved ({policy_err}).[/red] "
                        "Not ALLOW. Fix --policy path or TOML."
                    )
                raise typer.Exit(2)
            observed = count_run_events(root_path, normalized["run_id"])
            decision = _unobserved_policy_decision(
                normalized, policy_err, hook=hook, observed_steps=observed, root=root_path
            )
            stderr_prefix = "[SHADOW, not blocking] " if shadow else ""
            typer.echo(
                f"{stderr_prefix}Policy unobserved ({policy_err}). Not ALLOW.",
                err=True,
            )
            if not json_output:
                typer.echo(
                    render_verdict_line(
                        "UNOBSERVED",
                        decision.coverage[0],
                        decision.coverage[1],
                        "surfaces",
                        f"trust=UNOBSERVED, policy UNOBSERVED ({policy_err})",
                        audience=profile.profile,
                    )
                )
            normalized = apply_decision_to_event(normalized, decision)
            if shadow:
                normalized["policy"] = {**normalized["policy"], "shadow": True}
            decision_label = decision.decision
            if decision.trust_level >= 2:
                ledger_obligation = {"ledger_write_required": True, "ledger_written": False}
        else:
            observed = count_run_events(root_path, normalized["run_id"])
            decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
            if not json_output:
                state = _policy_verdict_state(decision)
                typer.echo(
                    render_verdict_line(
                        decision.decision,
                        decision.coverage[0],
                        decision.coverage[1],
                        "surfaces",
                        state["detail"],
                        audience=profile.profile,
                    )
                )
            normalized = apply_decision_to_event(normalized, decision)
            if shadow:
                normalized["policy"] = {**normalized["policy"], "shadow": True}
            decision_label = decision.decision
            if decision.trust_level >= 2:
                ledger_obligation = {"ledger_write_required": True, "ledger_written": False}

    # Idempotency on event_id, checked against the *final* event so a genuine replay
    # (same id, same content incl. the policy stamp) is a no-op, while reusing an id
    # with different content is refused — otherwise an agent could rewrite its history.
    id_state = check_event_id(root_path, normalized)
    if id_state == EVENT_ID_NEW:
        existing_events, corrupt = read_agent_events(root_path)
        if existing_events is None:
            id_state = EVENT_ID_UNOBSERVED
        elif corrupt:
            id_state = "ledger_corrupt"
        else:
            edge_issues = [
                issue
                for issue in validate_event_edges([*existing_events, normalized])
                if issue.get("event_id") == normalized["event_id"]
            ]
            if edge_issues:
                reasons = list(
                    dict.fromkeys(
                        f"unknown_edge_target:{issue['field']}"
                        if issue["reason"] == "unresolved_ref"
                        else "edge_validation_failed:"
                        f"{issue['field']}:{issue['reason']}:{issue.get('ref') or 'none'}"
                        for issue in edge_issues
                    )
                )
                if json_output:
                    console.print_json(
                        json.dumps(
                            {
                                "ok": False,
                                "reasons": reasons,
                                "edge_issues": edge_issues,
                                "exit_code": 1,
                                "ledger": str(root_path / AGENT_EVENTS_RELATIVE_PATH),
                                **ledger_obligation,
                            }
                        )
                    )
                else:
                    console.print("[red]INVALID[/red] event edges — not recorded")
                    for reason in reasons:
                        console.print(f"  - {reason}")
                raise typer.Exit(1)
    if id_state == EVENT_ID_NEW and not append_agent_event(root_path, normalized):
        id_state = "append_failed"
    if id_state in (EVENT_ID_CONFLICT, EVENT_ID_UNOBSERVED, "ledger_corrupt", "append_failed"):
        reason = {
            EVENT_ID_CONFLICT: "event_id_conflict",
            EVENT_ID_UNOBSERVED: "ledger_unobserved",
            "ledger_corrupt": "ledger_corrupt",
        }.get(id_state, "append_failed")
        # A ledger write failure means there is nothing to record the shadow
        # decision onto, but shadow's guarantee is still "never a blocking
        # exit code" -- so it still forces exit 0 here, same as every other
        # early-exit path, even though (unlike those) no event was appended.
        ledger_exit = 0 if shadow else 2
        plain_message = {
            EVENT_ID_CONFLICT: "event_id already recorded with different content. Not recorded.",
            EVENT_ID_UNOBSERVED: "Ledger unreadable — cannot check event_id. Not recorded.",
        }.get(id_state, "Failed to append agent event ledger. Not recorded.")
        # The stderr diagnostic must reach stderr regardless of --json: a
        # caller monitoring stderr for shadow diagnostics (per docs/CONNECT.md's
        # unconditional guarantee) must see this failure mode too, not only
        # the "ok": false buried inside a --json blob that itself goes to
        # stdout.
        if shadow:
            typer.echo(f"[SHADOW, not blocking] {plain_message}", err=True)
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "ok": False,
                        "reasons": [reason],
                        "exit_code": ledger_exit,
                        "shadow": shadow,
                        "recorded": False,
                        "ledger": str(root_path / AGENT_EVENTS_RELATIVE_PATH),
                        **ledger_obligation,
                    }
                )
            )
        else:
            stderr_prefix = "[SHADOW, not blocking] " if shadow else ""
            if id_state == EVENT_ID_CONFLICT:
                console.print(
                    f"{stderr_prefix}[red]event_id already recorded with different "
                    "content.[/red] Not recorded."
                )
            elif id_state == EVENT_ID_UNOBSERVED:
                console.print(
                    f"{stderr_prefix}[red]Ledger unreadable — cannot check event_id.[/red] "
                    "Not recorded."
                )
            else:
                console.print(f"{stderr_prefix}[red]Failed to append agent event ledger.[/red]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(ledger_exit)

    exit_code = {None: 0, "ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}[decision_label]
    # The event is already durably appended by this point (every append-failure
    # path above returned earlier). Under --hook claude-code this call plays
    # PostToolUse, which cannot block — fire-and-forget always exits 0 once the
    # ledger write itself succeeded. --shadow carries the same "recorded, not
    # enforced" honesty rule regardless of --hook.
    final_exit_code = 0 if (hook in _NATIVE_HOOKS or shadow) else exit_code
    ledger = str(root_path / AGENT_EVENTS_RELATIVE_PATH)
    if ledger_obligation:
        ledger_obligation["ledger_written"] = True
    if json_output:
        console.print_json(
            json.dumps(
                {
                    "ok": final_exit_code == 0,
                    "exit_code": final_exit_code,
                    "event_id": normalized["event_id"],
                    "decision": decision_label,
                    "reason": normalized.get("policy", {}).get("reason")
                    if isinstance(normalized.get("policy"), dict)
                    else None,
                    "shadow": shadow,
                    "ledger": ledger,
                    "full_body": full_body,
                    **ledger_obligation,
                }
            )
        )
    else:
        console.print(f"[green]RECORDED[/green] {normalized['event_id']}")
        console.print(f"ledger: {ledger}")
        if decision_label is not None:
            color = {"ALLOW": "green", "DENY": "red"}.get(decision_label, "yellow")
            console.print(f"policy: [{color}]{decision_label}[/{color}]")
            if shadow:
                console.print("[dim]shadow: true (recorded, not enforced)[/dim]")
            if decision_label == "DENY" and not (hook in _NATIVE_HOOKS or shadow):
                console.print(
                    "[yellow]DENY is recorded for audit; the caller must stop "
                    "the agent. HyoDo is not a runtime interceptor.[/yellow]"
                )
    raise typer.Exit(final_exit_code)


@trust_app.command("grant")
def policy_trust_grant(
    level: int = typer.Option(..., "--level", min=0, max=3, help="Trust level to grant (0-3)"),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/policy-trust.json"),
    by: str | None = typer.Option(
        None, "--by", help="Human or system identity recorded in the ledger"
    ),
    yes: bool = typer.Option(False, "--yes", help="Confirm an explicitly approved grant"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """Record an explicit operator policy trust grant.

    Grants are untracked local state and are refused in non-interactive runs
    unless ``HYODO_POLICY_TRUST_ALL=1`` is explicitly set.
    """
    root_path = Path(root).resolve()
    granted_by = by or default_granted_by()
    decision = resolve_policy_trust_grant(level, by=granted_by, yes=yes)
    if not decision.approved:
        payload = {
            "ok": False,
            "reason": decision.reason,
            "via": decision.via,
            "exit_code": 2,
        }
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]Trust grant refused:[/red] {decision.reason}")
        raise typer.Exit(2)
    try:
        state = grant_policy_trust(root_path, level, by=granted_by)
    except (OSError, ValueError) as exc:
        print(f"policy trust grant failed: {exc}", file=sys.stderr)
        raise typer.Exit(2) from exc
    payload = {
        "ok": True,
        "granted_level": state.level,
        "granted_by": state.granted_by,
        "granted_at": state.granted_at,
        "ledger": str(root_path / POLICY_TRUST_RELATIVE_PATH),
        "via": decision.via,
        "exit_code": 0,
    }
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        console.print(f"[green]GRANTED[/green] policy trust level {state.level}")
        console.print(f"ledger: {payload['ledger']}")
    raise typer.Exit(0)


@trust_app.command("show")
def policy_trust_show(
    root: str = typer.Option(".", "--root", help="Project root that owns local policy state"),
    json_output: bool = typer.Option(False, "--json", help="Emit a machine-readable receipt"),
):
    """Show the current local trust grant and its policy cap."""
    root_path = Path(root).resolve()
    state, trust_error = load_policy_trust(root_path)
    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_error = try_load_policy(policy_path)
    if policy_error is not None and policy_path.exists():
        payload = {"ok": False, "reason": policy_error, "exit_code": 2}
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]Policy unobserved ({policy_error}).[/red]")
        raise typer.Exit(2)
    cap = cfg.trust.max_level if cfg is not None and cfg.trust is not None else 3
    effective = effective_trust_level(cap, state)
    payload = {
        "ok": state is not None,
        "granted_level": state.level if state is not None else None,
        "granted_by": state.granted_by if state is not None else None,
        "granted_at": state.granted_at if state is not None else None,
        "history": [
            {"level": item.level, "granted_at": item.granted_at, "granted_by": item.granted_by}
            for item in (state.history if state is not None else ())
        ],
        "trust_file": str(root_path / POLICY_TRUST_RELATIVE_PATH),
        "trust_error": trust_error,
        "cap": cap,
        "effective_level": effective,
        "exit_code": 0 if state is not None else 2,
    }
    if json_output:
        console.print_json(json.dumps(payload))
    elif state is None:
        console.print(f"[yellow]UNOBSERVED[/yellow] {trust_error}; effective level: {effective}")
    else:
        console.print(f"[green]TRUST[/green] granted={state.level} cap={cap} effective={effective}")
        console.print(f"ledger: {payload['trust_file']}")
    raise typer.Exit(payload["exit_code"])


@policy_app.command("check")
def policy_check(
    file: str | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to a JSON agent event",
    ),
    stdin_flag: bool = typer.Option(
        False,
        "--stdin",
        help="Read event JSON from stdin",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="policy.toml path (default: <root>/.hyodo/policy.toml)",
    ),
    root: str = typer.Option(
        ".",
        "--root",
        help="Project root used for ledger counting and trust state",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable decision JSON",
    ),
    quiet: bool = typer.Option(False, "--quiet", help="Print only the verdict line"),
    explain: bool = typer.Option(False, "--explain", help="Print a stored explanation"),
    hook: str | None = typer.Option(
        None,
        "--hook",
        help="Adapt stdin from a harness-native hook JSON shape instead of "
        "hyodo.agent-event/v1 (claude-code, cursor, or codex)",
    ),
    native_response: bool = typer.Option(
        False,
        "--native-response",
        help="Emit the host-native response envelope (currently Cursor only).",
    ),
    shadow: bool = typer.Option(
        False,
        "--shadow",
        help="Evaluate and print the real decision, but always exit 0 "
        "(shadow-mode on-ramp installed by `hyodo connect --shadow`)",
    ),
    audience: str | None = _audience_option(),
):
    """
    Evaluate one event against a local policy.toml.

    Exit: 0 ALLOW · 1 DENY · 2 unobserved (missing/invalid policy or event) ·
    3 ASK (operator decision required). ``--shadow`` forces exit 0 regardless
    of the decision (the decision itself is still printed/returned, never
    hidden). Does not write the ledger (use ``hyodo event record --policy``
    for that).
    """

    if native_response and hook not in {"cursor", "codex"}:
        raise typer.BadParameter("--native-response requires --hook cursor or codex")
    if native_response and not json_output:
        raise typer.BadParameter("--native-response requires --json")
    profile = _resolve_audience_or_exit(Path(root).resolve(), audience, "policy check", json_output)
    verdict_state: dict[str, Any] = {"unit": "surfaces"}
    verdict_state.update(
        decision="UNOBSERVED", detail="trust=UNOBSERVED, required evidence UNOBSERVED"
    )
    with _verdict_output(
        "policy check",
        verdict_state,
        quiet,
        explain,
        json_output,
        profile,
        native_response,
    ):
        root_path = Path(root).resolve()
        file_path = Path(file) if file else None
        data, err = _load_event_payload(file_path, stdin_flag)
        if err is not None:
            if json_output:
                console.print_json(
                    json.dumps(
                        {
                            "decision": "UNOBSERVED",
                            "rule_id": None,
                            "reason": err,
                            "exit_code": 2,
                        }
                    )
                )
            else:
                console.print(f"[red]Cannot load event: {err}[/red]")
                console.print("[yellow]This is not a validation pass.[/yellow]")
            raise typer.Exit(2)

        native_event_name: str | None = None
        if hook is not None:
            if hook not in _NATIVE_HOOKS:
                message = f"unsupported --hook value: {hook}"
                if json_output:
                    console.print_json(
                        json.dumps(
                            {
                                "decision": "UNOBSERVED",
                                "rule_id": None,
                                "reason": message,
                                "exit_code": 2,
                            }
                        )
                    )
                else:
                    console.print(f"[red]{message}[/red]")
                typer.echo(f"HYODO UNOBSERVED: {message}.", err=True)
                raise typer.Exit(2)
            if native_response and isinstance(data, dict):
                native_event_name = data.get("hook_event_name")
            mapped, map_err = _map_hook_payload(data, root_path, hook)
            if mapped is None:
                mapping_exit = 0 if shadow else 2
                if json_output:
                    console.print_json(
                        json.dumps(
                            {
                                "decision": "UNOBSERVED",
                                "rule_id": None,
                                "reason": map_err,
                                "exit_code": mapping_exit,
                                "shadow": shadow,
                            }
                        )
                    )
                else:
                    console.print(f"[red]Cannot map {hook} hook payload: {map_err}[/red]")
                stderr_prefix = "[SHADOW, not blocking] " if shadow else ""
                typer.echo(
                    f"{stderr_prefix}HYODO UNOBSERVED: malformed hook payload; treating as "
                    "blocked, not allowed.",
                    err=True,
                )
                raise typer.Exit(mapping_exit)
            data = mapped.raw
            root_path = mapped.root

        ok, reasons, normalized = validate_event(data)
        if not ok or normalized is None:
            if json_output:
                console.print_json(
                    json.dumps(
                        {
                            "decision": "UNOBSERVED",
                            "rule_id": None,
                            "reason": ";".join(reasons),
                            "exit_code": 2,
                        }
                    )
                )
            else:
                console.print("[red]INVALID event — policy not evaluated.[/red]")
                for reason in reasons:
                    console.print(f"  - {reason}")
            raise typer.Exit(2)

        policy_path = (
            Path(config).resolve() if config else (root_path / POLICY_RELATIVE_PATH).resolve()
        )
        cfg, policy_err = try_load_policy(policy_path)
        # Step budget is counted from the working-tree ledger, never from the
        # caller-supplied step_index. (Same root basis as the default policy lookup.)
        observed = count_run_events(root_path, normalized["run_id"])
        if cfg is None:
            # Fail-closed: a missing/invalid policy is UNOBSERVED, never ALLOW --
            # unchanged. It now flows through the same decision object as every
            # other outcome (rather than a bespoke exit-2 branch) so --shadow's
            # "never a blocking exit" guarantee applies here too, and so a
            # missing policy under --hook claude-code is a real evaluated
            # decision (reason policy_missing) instead of a crash.
            decision = _unobserved_policy_decision(
                normalized, policy_err, hook=hook, observed_steps=observed, root=root_path
            )
        else:
            decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
        verdict_state.update(_policy_verdict_state(decision))
        # 0 = ALLOW, 1 = DENY, 2 = UNOBSERVED, 3 = ASK.
        exit_code = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}[decision.decision]
        # The diagnostic text is built once regardless of --hook: --shadow's
        # "never blocking, but never silent either" guarantee has to hold for
        # a plain `policy check --shadow` (no --hook at all) just as much as
        # for the claude-code hook contract below.
        if decision.decision == "DENY":
            stderr_message = f"{decision.rule_id or 'rule'}: {decision.reason or ''}".strip()
        elif decision.decision == "ASK":
            stderr_message = (
                f"HYODO ASK: {decision.reason or 'operator decision required'}. "
                "Stop and ask the human before retrying this tool call."
            )
        elif decision.decision == "UNOBSERVED":
            stderr_message = (
                f"HYODO UNOBSERVED: {decision.reason or 'insufficient evidence'}. "
                "Not a green light — stop and ask the human."
            )
        else:
            stderr_message = None
        if hook == "claude-code":
            # Claude Code's PreToolUse contract has only two outcomes (proceed or
            # block); ASK and UNOBSERVED are enforced as a hard block here — this
            # is a real behavior change, called out under Open questions in the
            # spec, not silently smoothed over.
            hook_exit_code = 0 if decision.decision == "ALLOW" else 2
        else:
            hook_exit_code = exit_code
        # Under --hook claude-code the diagnostic is always relevant (it's the
        # only signal for a hard block); without --hook it's only relevant
        # under --shadow, where it's the only place the real decision surfaces
        # outside the exit code.
        if stderr_message and (hook == "claude-code" or shadow):
            if shadow:
                stderr_message = "[SHADOW, not blocking] " + stderr_message
            typer.echo(stderr_message, err=True)
        final_exit_code = 0 if shadow else hook_exit_code
        if json_output:
            if native_response:
                if not isinstance(native_event_name, str):
                    raise typer.BadParameter("Cursor payload is missing hook_event_name")
                if hook == "cursor":
                    payload = map_cursor_permission_response(
                        decision,
                        event_name=native_event_name,
                    )
                else:
                    payload = map_codex_permission_response(
                        decision,
                        event_name=native_event_name,
                    )
            else:
                payload = decision.as_dict()
                payload["exit_code"] = final_exit_code
                payload["shadow"] = shadow
                if decision.trust_level >= 2:
                    payload["ledger_write_required"] = True
                    payload["ledger_written"] = False
            console.print_json(json.dumps(payload))
        else:
            color = "green" if decision.decision == "ALLOW" else "red"
            console.print(f"[{color}]{decision.decision}[/{color}]")
            if decision.rule_id:
                console.print(f"rule_id: {decision.rule_id}")
            if decision.reason:
                console.print(f"reason: {decision.reason}")
            if shadow:
                console.print("[dim]shadow: true (recorded, not enforced)[/dim]")
            if decision.trust_level >= 2:
                console.print(
                    "[yellow]trust level 2+ requires the decision to be recorded — "
                    "use `hyodo event record --policy`[/yellow]"
                )
        raise typer.Exit(final_exit_code)


@app.command()
def connect(
    target: str | None = typer.Argument(
        None,
        help="Harness to wire: claude-code, pre-commit, github-actions "
        "(cursor, codex report UNOBSERVED — no verified hook contract)",
    ),
    write: bool = typer.Option(
        False, "--write", help="Perform the writes (default: dry run, writes nothing)"
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the per-target confirmation prompt"),
    shadow: bool = typer.Option(
        False,
        "--shadow",
        help="Install the Claude Code hook in shadow mode: evaluates and records "
        "policy.shadow=true but always exits 0 (nothing is blocked)",
    ),
    status: bool = typer.Option(
        False, "--status", help="Report drift between what was written and what is on disk"
    ),
    root: str = typer.Option(".", "--root", help="Project root to detect/write into"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """
    Wire a coding harness to HyoDo's gates (Claude Code hooks, pre-commit,
    GitHub Actions) instead of re-implementing one.

    With no target: detect harnesses present in this checkout, write nothing.
    Default is dry run — prints the exact files a target would create or
    modify. ``--write`` performs the writes; a file `connect` did not create
    itself gets a ``.bak`` alongside it on its first write. Running
    ``--write`` twice with no other change makes no further edits.

    Exit: dry run always 0. ``--write``: 0 on success (including "already up
    to date"), 1 if a confirmation was declined without ``--yes``, 2 on an
    unknown/unsupported target or a write error. ``--status``: 0 in sync, 2
    when a written file has drifted from its recorded digest (UNOBSERVED).
    """
    root_path = Path(root).resolve()

    if status:
        reports = check_status(root_path)
        drifted = [r for r in reports if r.status != "ok"]
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "targets": [
                            {
                                "target": r.target,
                                "path": r.path,
                                "status": r.status,
                                "reason": r.reason,
                            }
                            for r in reports
                        ],
                        "drift": bool(drifted),
                        "exit_code": 2 if drifted else 0,
                    }
                )
            )
        else:
            if not reports:
                console.print(
                    "[yellow]No targets connected yet (.hyodo/connect.json not found).[/yellow]"
                )
            for r in reports:
                color = "green" if r.status == "ok" else "red"
                detail = f" ({r.reason})" if r.reason else ""
                console.print(f"[{color}]{r.status}[/{color}] {r.target}: {r.path}{detail}")
        raise typer.Exit(2 if drifted else 0)

    if target is None:
        detected = detect_connect_targets(root_path)
        if json_output:
            payload: dict[str, Any] = {name: detected[name] for name in WRITABLE_TARGETS}
            payload.update(dict.fromkeys(UNOBSERVED_TARGETS, False))
            console.print_json(
                json.dumps({"detected": payload, "unobserved": list(UNOBSERVED_TARGETS)})
            )
        else:
            table = Table(title="hyodo connect - detected harnesses", show_header=True)
            table.add_column("Harness", style="cyan")
            table.add_column("Status")
            for name in WRITABLE_TARGETS:
                label = "[green]detected[/green]" if detected[name] else "[dim]not detected[/dim]"
                table.add_row(name, label)
            for name in UNOBSERVED_TARGETS:
                table.add_row(name, "[yellow]UNOBSERVED[/yellow] (hook contract not verified)")
            console.print(table)
            console.print(
                "\nRun `hyodo connect <harness>` to preview what would be written "
                "(add --write to act)."
            )
        raise typer.Exit(0)

    if target in UNOBSERVED_TARGETS:
        message = f"{target}: {UNOBSERVED_MESSAGE}"
        if json_output:
            console.print_json(
                json.dumps(
                    {"target": target, "status": "unobserved", "message": message, "exit_code": 2}
                )
            )
        else:
            console.print(f"[yellow]UNOBSERVED[/yellow] {message}")
        raise typer.Exit(2)

    if target not in WRITABLE_TARGETS:
        message = f"unknown target: {target}. Known targets: {', '.join(ALL_TARGETS)}"
        if json_output:
            console.print_json(
                json.dumps(
                    {"target": target, "status": "unknown", "message": message, "exit_code": 2}
                )
            )
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    plan = plan_target(target, root_path, shadow=shadow)

    if not write:
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "target": target,
                        "status": plan.status,
                        "write": False,
                        "shadow": shadow and not plan.shadow_ignored,
                        "files": [
                            {
                                "path": str(f.path),
                                "existed_before": f.existed_before,
                                "will_change": f.will_change,
                                "content": f.content,
                            }
                            for f in plan.files
                        ],
                        "exit_code": 0,
                    }
                )
            )
        else:
            console.print(
                f"[cyan]dry run[/cyan] {rich_escape(str(target))}: {rich_escape(str(plan.message))}"
            )
            if shadow and plan.shadow_ignored:
                console.print("[dim]--shadow has no effect on this target (always enforced).[/dim]")
            for f in plan.files:
                verb = "create" if not f.existed_before else "update"
                console.print(f"  would {verb}: {f.path}")
                console.print("  ---")
                for line in f.content.splitlines():
                    console.print(f"  {line}", markup=False)
                console.print("  ---")
        raise typer.Exit(0)

    if not yes and plan.status == "would_write":
        if sys.stdin.isatty() and not json_output:
            proceed = typer.confirm(f"Write {len(plan.files)} file(s) for {target}?")
            if not proceed:
                console.print("[yellow]Declined - nothing written.[/yellow]")
                raise typer.Exit(1)
        else:
            # Non-interactive callers must say --yes; silence is not consent.
            reason = "confirmation_required: pass --yes to write without a prompt"
            if json_output:
                console.print_json(json.dumps({"ok": False, "reasons": [reason], "exit_code": 1}))
            else:
                console.print(f"[yellow]{reason} - nothing written.[/yellow]")
            raise typer.Exit(1)

    state = load_connect_state(root_path)
    try:
        plan = write_target(target, root_path, shadow=shadow, state=state)
        save_connect_state(root_path, state)
    except OSError as exc:
        if json_output:
            console.print_json(
                json.dumps(
                    {"target": target, "status": "error", "message": str(exc), "exit_code": 2}
                )
            )
        else:
            console.print(f"[red]Write failed: {exc}[/red]")
        raise typer.Exit(2) from exc

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "target": target,
                    "status": plan.status,
                    "write": True,
                    "shadow": shadow and not plan.shadow_ignored,
                    "files": [
                        {
                            "path": str(f.path),
                            "existed_before": f.existed_before,
                            "will_change": f.will_change,
                        }
                        for f in plan.files
                    ],
                    "exit_code": 0,
                }
            )
        )
    else:
        console.print(f"[green]{plan.status}[/green] {target}: {plan.message}")
        if shadow and plan.shadow_ignored:
            console.print("[dim]--shadow has no effect on this target (always enforced).[/dim]")
    raise typer.Exit(0)


#: Onboarding guide text for the non-interactive path (existing docs/tests
#: quote keywords here). Interactive callers see the four-step flow below
#: instead of this block. Hook vs MCP wording is load-bearing (#204 item 31).
_START_GUIDE = """
[bold blue]HyoDo quick start[/bold blue]

[b]HyoDo is a model-agnostic quality-gate kit for AI-assisted development.[/b]
Model-agnostic means independent of the AI model or agent UI — not language-agnostic.

Any caller can record events and evaluate policy. Hook wiring
(`hyodo connect`) is Claude Code, pre-commit, and GitHub Actions.
`cursor` and `codex` stay UNOBSERVED until a verified hook contract
exists. MCP config (`hyodo mcp config`) is a separate surface and
includes Cursor.

[bold cyan]Core commands:[/bold cyan]
  • [bold]check[/bold]  - HyoDo checkout release gates (ruff/pyright/pytest)
  • [bold]score[/bold]  - HyoDo Integrity Score, Six-Virtue Model (not auto-approval)
  • [bold]safe[/bold]   - lightweight safety early-warning scan
  • [bold]safe --strict[/bold] - exit 1 on high-severity findings
  • [bold]event[/bold]  - agent event ledger (opt-in FDE evidence spine)
  • [bold]policy[/bold] - local agent policy gate (ALLOW|DENY)
  • [bold]trinity[/bold] - structured review checklist

[bold cyan]Examples:[/bold cyan]
  $ hyodo check
  $ hyodo score -t 0.9 -g 0.9 -b 0.9 -i 0.9 -c 0.9
  $ hyodo safe --strict
  $ hyodo event record --file step.json --policy .hyodo/policy.toml

[bold cyan]Boundary:[/bold cyan]
  Scores and scans support review. Human approval remains required.
  Event/policy are gates and evidence — not an agent runtime interceptor.
    """

#: Order hosts are shown/asked about in - claude-code first because this
#: process is most often itself running inside a Claude Code-family harness.
_ONBOARDING_HOST_ORDER: tuple[str, ...] = (
    "claude-code",
    "claude-desktop",
    "cursor",
    "vscode",
    "codex",
)
_FIRST_PROMPT = "Check this project"
_STARTER_COMMANDS: tuple[str, ...] = (
    "hyodo check",
    "hyodo safe",
    "hyodo score -t 0.9 -g 0.9 -b 0.9 -i 0.9 -c 0.9",
)


def _onboarding_detected_hosts(root: Path) -> dict[str, bool]:
    """Merge ``connect``'s harness detection with MCP host detection.

    ``claude-code`` is detected by either signal (a coding-agent hook target
    in ``connect`` and an MCP host in ``mcp config`` are the same product).
    """
    hook_detected = detect_connect_targets(root)
    mcp_detected = detect_mcp_hosts(root)
    detected = dict(mcp_detected)
    detected["claude-code"] = hook_detected.get("claude-code", False) or mcp_detected.get(
        "claude-code", False
    )
    return detected


def _onboarding_host_candidates(detected: dict[str, bool]) -> list[str]:
    """At most two detected hosts, so the step-3 question stays a 1-3 choice."""
    candidates = [host for host in _ONBOARDING_HOST_ORDER if detected.get(host)][:2]
    return candidates or ["claude-code"]


def _print_step1_workspace(root: Path, detected: dict[str, bool]) -> None:
    console.print(f"\n[bold]1. Workspace:[/bold] {root}")
    console.print("[bold]   Detected hosts:[/bold]")
    for host in _ONBOARDING_HOST_ORDER:
        label = "[green]detected[/green]" if detected.get(host) else "[dim]not detected[/dim]"
        console.print(f"     {host}: {label}")


def _print_step4_first_prompt() -> None:
    commands = "\n".join(f"  $ {command}" for command in _STARTER_COMMANDS)
    console.print(
        "\n[bold]4. Try this prompt in your connected host:[/bold]\n"
        f'  "{_FIRST_PROMPT}"\n'
        "\n[bold]Or run these by hand:[/bold]\n" + commands
    )


def _ask_audience_question(root: Path) -> str | None:
    """Step 2: today's single audience question, unchanged."""
    console.print(
        "\n[bold]2. Who is reading these results?[/bold]\n"
        "  1) vibe coder\n"
        "  2) engineer\n"
        "  3) professional (law/accounting)"
    )
    answer = input("> ").strip()
    chosen = {"1": "vibe", "2": "engineer", "3": "professional"}.get(answer)
    if chosen is None:
        console.print("[yellow]No changes made — unrecognized answer.[/yellow]")
        return None
    config_path = write_audience_config(root, chosen)
    console.print(f"[green]Wrote {config_path} with audience profile '{chosen}'.[/green]")
    return chosen


@graph_app.command("export")
def graph_export_cmd(
    out: str = typer.Option(
        ".hyodo/graph.json", "--out", help="Path (relative to --root) to write the export to"
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt"),
    root: str = typer.Option(".", "--root", help="Project root to read the ledger from"),
):
    """
    Write the `hyodo.graph-export/v1` bridge artifact (Package 2-C).

    Nodes/edges mirror `hyodo report --format graph`'s own
    `hyodo.evidence-graph/v1` shape; `backlinks` reverse-indexes every
    non-broken `evidence_refs` entry; `clusters` groups decision events by
    pillar. A pre-1-B ledger (no `parent_event_id`/`evidence_refs`
    anywhere) still exports successfully, with empty `edges`/`backlinks` —
    an honestly empty graph is not an error.

    Mirrors `connect`'s consent pattern: default is an interactive
    confirmation before writing; `--yes` skips it for non-interactive
    callers, which must say so explicitly (silence is not consent).

    Exit: 0 written, 1 confirmation declined without `--yes`, 2 the
    ledger could not be read at all or the write itself failed.
    """
    root_path = Path(root).resolve()
    graph = build_report_graph(root_path)
    if graph.get("reason") == "ledger_unreadable":
        console.print(
            "[red]The agent-event ledger exists but could not be read — nothing exported.[/red]"
        )
        raise typer.Exit(2)

    export = build_graph_export(graph)

    if not yes:
        if sys.stdin.isatty():
            proceed = typer.confirm(f"Write graph export to {out}?")
            if not proceed:
                console.print("[yellow]Declined - nothing written.[/yellow]")
                raise typer.Exit(1)
        else:
            console.print(
                "[yellow]confirmation_required: pass --yes to write without a prompt - "
                "nothing written.[/yellow]"
            )
            raise typer.Exit(1)

    out_path = root_path / out
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        console.print(f"[red]Write failed: {exc}[/red]")
        raise typer.Exit(2) from exc

    console.print(f"[green]Wrote {out_path}[/green]")
    raise typer.Exit(0)


def _connect_host_with_confirm(root: Path, host: str) -> None:
    """Preview, then a single yes/no confirm, then perform the write(s) for *host*.

    ``claude-code`` runs both code paths (it is both a ``connect`` hook
    target and an MCP host); every other candidate only ever reaches
    ``mcp config`` here (``connect``'s other targets - pre-commit,
    github-actions - are not "hosts" and stay in the advanced `hyodo connect`
    path).
    """
    console.print(f"\n[bold]Preview for '{host}':[/bold]")
    connect_plan = plan_target("claude-code", root, shadow=False) if host == "claude-code" else None
    if connect_plan is not None:
        console.print(f"  connect claude-code: {rich_escape(str(connect_plan.message))}")
        for planned_file in connect_plan.files:
            console.print(f"    {rich_escape(str(planned_file.path))}")
    mcp_plan = plan_host(host, root)
    console.print(f"  mcp config {rich_escape(str(host))}: {rich_escape(str(mcp_plan.message))}")
    if mcp_plan.path is not None:
        scope = " (global, not project-scoped)" if host in {"codex", "claude-desktop"} else ""
        console.print(f"    {rich_escape(str(mcp_plan.path))}{scope}")
    if not mcp_plan.verified:
        console.print(f"  [yellow]{UNVERIFIED_FORMAT_LABEL}[/yellow]")

    answer = input("Write this now? [y/N] > ").strip().lower()
    if answer not in ("y", "yes"):
        console.print("[yellow]Declined — nothing written.[/yellow]")
        return

    if connect_plan is not None:
        state = load_connect_state(root)
        write_target("claude-code", root, shadow=False, state=state)
        save_connect_state(root, state)
    write_host(host, root)
    console.print(f"[green]Connected {host}.[/green]")


def _ask_connect_host_question(root: Path, candidates: list[str]) -> None:
    """Step 3: one question, at most three choices (candidates + 'skip')."""
    options = [*candidates, "skip"]
    listing = "\n".join(f"  {index + 1}) {name}" for index, name in enumerate(options))
    console.print(f"\n[bold]3. Connect which host now?[/bold]\n{listing}")
    answer = input("> ").strip()
    chosen: str | None = None
    if answer.isdigit():
        index = int(answer) - 1
        if 0 <= index < len(options):
            chosen = options[index]
    elif answer in options:
        chosen = answer
    if chosen is None:
        console.print("[yellow]No changes made — unrecognized answer.[/yellow]")
        return
    if chosen == "skip":
        console.print("[yellow]Skipped — nothing written.[/yellow]")
        return
    _connect_host_with_confirm(root, chosen)


def _print_noninteractive_steps(
    root: Path, detected: dict[str, bool], candidates: list[str]
) -> None:
    """Non-interactive: the same four steps as plain text. Asks nothing, writes nothing."""
    _print_step1_workspace(root, detected)
    console.print(
        "\n[bold]2. Audience[/bold] (vibe / engineer / professional): set with "
        "--audience, HYODO_AUDIENCE, or \\[audience] profile in "
        ".hyodo/config.toml. Nothing is written automatically."
    )
    console.print(
        "\n[bold]3. Connect a host[/bold] (writes nothing unless you pass --write, "
        "and for `connect`, --yes):\n"
        "  $ hyodo connect claude-code --write --yes\n"
        f"  $ hyodo mcp config {candidates[0]} --write"
    )
    _print_step4_first_prompt()


@app.command()
def start():
    """
    HyoDo's first-use onboarding flow.

    Interactive: step 1 shows the workspace root and detected hosts; step 2
    asks one audience question; step 3 asks one "connect which host now?"
    question (at most three choices, including "skip") and, on a real
    choice, previews the exact write(s) and asks one yes/no confirm before
    doing anything; step 4 prints a first prompt to try and three commands
    to run by hand. At most three questions in the whole flow; nothing is
    written without an explicit yes.

    Non-interactive (``not sys.stdin.isatty()``): prints the same four steps
    as plain text with exact commands, asks nothing, writes nothing. The
    guide text names the hook vs MCP split; it does not claim Cursor or
    Codex hook coverage.
    """
    root = Path.cwd()
    detected = _onboarding_detected_hosts(root)
    candidates = _onboarding_host_candidates(detected)

    if not sys.stdin.isatty():
        console.print(_START_GUIDE)
        console.print(
            "\n[dim]Set an audience profile (vibe / engineer / professional) "
            "non-interactively with the --audience flag on any command, the "
            'HYODO_AUDIENCE env var, or by adding \\[audience] / profile = "..." '
            "to .hyodo/config.toml.[/dim]"
        )
        _print_noninteractive_steps(root, detected, candidates)
        return

    _print_step1_workspace(root, detected)
    _ask_audience_question(root)
    _ask_connect_host_question(root, candidates)
    _print_step4_first_prompt()


@app.command(name="trinity")
def trinity_analysis(
    task: str = typer.Argument(..., help="Task description to review"),
):
    """
    Structured Trinity review checklist.

    Review prompts only — not an automated pass verdict.
    """
    console.print(Panel.fit(f"Trinity review checklist: {task}", style="bold magenta"))
    console.print("\nTruth - technical accuracy")
    console.print("  - Types, contracts, and failure modes checked?")
    console.print("\nGoodness - security and stability")
    console.print("  - Secrets, destructive commands, production impact reviewed?")
    console.print("\nBeauty - clarity")
    console.print("  - Diff readable? Naming/structure understandable?")
    console.print("\n[bold yellow]Checklist only — no automatic approval[/bold yellow]")
    console.print("Next: hyodo check && hyodo safe, then human review.")


def _new_agent_event(
    *,
    kind: str,
    actor: str,
    tool: dict[str, Any] | None = None,
    run_id: str,
    step_index: int = 0,
) -> dict[str, Any]:
    """Build a minimal, unvalidated ``hyodo.agent-event/v1`` shell for HyoDo-synthesized events."""
    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "step_index": step_index,
        "actor": actor,
    }
    if tool is not None:
        raw["tool"] = tool
    return raw


_SKILLS_EXIT_CODES = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}


def _skills_ingest_from_node(
    *,
    from_node: str,
    root: str,
    yes: bool,
    json_output: bool,
) -> None:
    """``hyodo skills ingest --from-node <file>``: BYOM research-node hand-off.

    The node owns embeddings/vectors and never sends them; this only accepts
    a ``hyodo.skill-retrieval/v1`` file of rule text + digests + an ordinal
    rank. A malformed file (bad JSON, missing/invalid field, or any
    float score/probability/percentage field) exits 1 and writes nothing.
    The same ``skills.ingest`` policy gate applies, keyed on
    ``skill_ingest:node:<label>`` -- ASK unless trust level 3 or ``--yes``,
    identical to a path/url source.
    """
    root_path = Path(root).resolve()
    data, parse_reasons = parse_node_retrieval_file(Path(from_node))
    if data is None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": parse_reasons, "exit_code": 1}))
        else:
            console.print(f"[red]malformed retrieval file: {', '.join(parse_reasons)}[/red]")
        raise typer.Exit(1)

    retrieval, reasons = validate_node_retrieval(data)
    if retrieval is None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": 1}))
        else:
            console.print(f"[red]malformed retrieval file: {', '.join(reasons)}[/red]")
        raise typer.Exit(1)

    tool = build_node_ingest_tool(retrieval.node)
    run_id = str(uuid.uuid4())
    raw_event = _new_agent_event(kind="tool_call", actor="hyodo", tool=tool, run_id=run_id)
    ok, event_reasons, normalized = validate_event(raw_event)
    if not ok or normalized is None:  # pragma: no cover - internal construction guard
        message = f"internal error building node ingest event: {event_reasons}"
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": event_reasons, "exit_code": 2}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)
    normalized["meta"]["tags"] = ["skills-ingest", "node"]

    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is None:
        if policy_err == "policy_missing":
            cfg = PolicyConfig(
                schema=POLICY_SCHEMA_ID,
                max_steps=None,
                allowed_tools=None,
                blocked_path_globs=(),
            )
        else:
            message = f"policy unobserved ({policy_err}); not ALLOW"
            if json_output:
                console.print_json(
                    json.dumps({"ok": False, "reasons": [policy_err], "exit_code": 2})
                )
            else:
                console.print(f"[red]{message}[/red]")
            raise typer.Exit(2)

    observed = count_run_events(root_path, run_id)
    decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
    stamped = apply_decision_to_event(normalized, decision)
    append_agent_event(root_path, stamped)

    effective_decision = decision.decision
    approval_event_id: str | None = None
    if decision.decision == "ASK" and yes:
        approval_claim = {
            "decision": "ALLOW",
            "rule_id": "operator_approval",
            "reason": "operator approved via --yes",
        }
        approval_raw = _new_agent_event(kind="decision", actor="human", run_id=run_id, step_index=1)
        ok2, _reasons2, approval_normalized = validate_event(approval_raw)
        if ok2 and approval_normalized is not None:
            approval_normalized["policy"] = unevaluated_policy(claimed=approval_claim)
            if append_agent_event(root_path, approval_normalized):
                approval_event_id = approval_normalized["event_id"]
                effective_decision = "ALLOW"

    manifest_data, manifest_status = load_manifest(root_path)
    existing_skills = (
        list(manifest_data.get("skills", []))
        if manifest_data is not None and manifest_status == "ok"
        else []
    )

    compiled_rule_count = 0
    if effective_decision == "ALLOW":
        rules = node_rules_for(retrieval)
        compiled_rule_count = sum(1 for rule in rules if rule.compiled is not None)
        entry = node_manifest_entry(retrieval, rules, ingested_at=stamped["event_id"])
        existing_skills = [
            row for row in existing_skills if row.get("source") != entry["source"]
        ] + [entry]
        save_manifest(root_path, existing_skills)

    exit_code = _SKILLS_EXIT_CODES[decision.decision]
    if effective_decision == "ALLOW" and decision.decision == "ASK":
        exit_code = 0

    result = {
        "decision": decision.decision,
        "effective_decision": effective_decision,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "trust_level": decision.trust_level,
        "source": f"node:{retrieval.node}",
        "readable": True,
        "content_digest": None,
        "compiled_rule_count": compiled_rule_count,
        "manifest": str(root_path / SKILLS_MANIFEST_RELATIVE_PATH),
        "event_id": stamped["event_id"],
        "approval_event_id": approval_event_id,
        "exit_code": exit_code,
    }
    if json_output:
        console.print_json(json.dumps(result))
    else:
        console.print(f"[bold]{decision.decision}[/bold] node:{retrieval.node}")
        console.print(f"  reason: {decision.reason}")
        if effective_decision == "ALLOW" and decision.decision == "ASK":
            console.print("  approved via --yes; manifest compiled")
        elif effective_decision == "ALLOW":
            console.print(f"  compiled {compiled_rule_count} mechanical rule(s)")
        elif decision.decision == "ASK":
            console.print("  re-run with --yes, or grant trust level 3, to compile")
    raise typer.Exit(exit_code)


@skills_app.command("ingest")
def skills_ingest(
    source: str | None = typer.Argument(
        None, help="Local path or http(s) URL to a skill Markdown file"
    ),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    from_node: str | None = typer.Option(
        None,
        "--from-node",
        help=(
            "Path to a hyodo.skill-retrieval/v1 JSON file from an external research "
            "node (BYOM); mutually exclusive with SOURCE"
        ),
    ),
    store_body: bool = typer.Option(
        False,
        "--store-body",
        help="Persist the skill body at .hyodo/skills/bodies/<digest>.md (default: not stored)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Approve an ASK decision now; records a human_response approval event, then proceeds",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """
    Ingest one skill source as a lens: record it, evaluate policy, compile its
    rules into ``.hyodo/skills/manifest.json`` on a proceeding decision.

    Ingesting a skill is treated as an external variable exactly like a web
    fetch — never silently ALLOW. Exit 0 ALLOW, 1 DENY, 2 UNOBSERVED, 3 ASK
    (re-run with ``--yes`` or after granting trust level 3 to proceed).
    A ``url:`` source is never fetched in this package: only its domain is
    recorded, with ``content_digest: null`` and ``status: "unreadable"``.

    ``--from-node <file>`` takes a research node's ``hyodo.skill-retrieval/v1``
    hand-off instead of SOURCE: the node owns embeddings/vectors and never
    sends them, HyoDo stores only rule text (<= 512 chars), digests, and an
    ordinal rank. A malformed file exits 1 and writes nothing.
    """
    if from_node is not None:
        if source is not None:
            console.print("[red]pass either SOURCE or --from-node, not both[/red]")
            raise typer.Exit(1)
        _skills_ingest_from_node(from_node=from_node, root=root, yes=yes, json_output=json_output)
        return
    if source is None:
        console.print("[red]missing SOURCE (or pass --from-node)[/red]")
        raise typer.Exit(1)

    root_path = Path(root).resolve()
    parsed = resolve_source(root_path, source)
    tool = build_ingest_tool(parsed)
    run_id = str(uuid.uuid4())
    raw_event = _new_agent_event(kind="tool_call", actor="hyodo", tool=tool, run_id=run_id)
    ok, reasons, normalized = validate_event(raw_event)
    if not ok or normalized is None:  # pragma: no cover - internal construction guard
        message = f"internal error building ingest event: {reasons}"
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": 2}))
        else:
            console.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is None:
        if policy_err == "policy_missing":
            # No policy.toml: ingestion is unconditionally discretionary regardless,
            # so fall back to the all-defaults policy rather than refusing to run.
            cfg = PolicyConfig(
                schema=POLICY_SCHEMA_ID,
                max_steps=None,
                allowed_tools=None,
                blocked_path_globs=(),
            )
        else:
            message = f"policy unobserved ({policy_err}); not ALLOW"
            if json_output:
                console.print_json(
                    json.dumps({"ok": False, "reasons": [policy_err], "exit_code": 2})
                )
            else:
                console.print(f"[red]{message}[/red]")
            raise typer.Exit(2)

    observed = count_run_events(root_path, run_id)
    decision = evaluate_policy(normalized, cfg, observed_steps=observed, root=root_path)
    stamped = apply_decision_to_event(normalized, decision)
    append_agent_event(root_path, stamped)

    effective_decision = decision.decision
    approval_event_id: str | None = None
    if decision.decision == "ASK" and yes:
        approval_claim = {
            "decision": "ALLOW",
            "rule_id": "operator_approval",
            "reason": "operator approved via --yes",
        }
        approval_raw = _new_agent_event(kind="decision", actor="human", run_id=run_id, step_index=1)
        ok2, _reasons2, approval_normalized = validate_event(approval_raw)
        if ok2 and approval_normalized is not None:
            approval_normalized["policy"] = unevaluated_policy(claimed=approval_claim)
            if append_agent_event(root_path, approval_normalized):
                approval_event_id = approval_normalized["event_id"]
                effective_decision = "ALLOW"

    manifest_data, manifest_status = load_manifest(root_path)
    existing_skills = (
        list(manifest_data.get("skills", []))
        if manifest_data is not None and manifest_status == "ok"
        else []
    )

    compiled_rule_count = 0
    if effective_decision == "ALLOW":
        rules = []
        if parsed.readable and parsed.content is not None:
            skill_name = skill_name_for(parsed.resolved_path) if parsed.resolved_path else "skill"
            rules = parse_skill_rules(skill_name, parsed.content)
            compiled_rule_count = sum(1 for rule in rules if rule.compiled is not None)
            if store_body and parsed.content_digest_value is not None:
                store_skill_body(root_path, parsed.content_digest_value, parsed.content)
        entry = manifest_entry(
            parsed,
            rules,
            ingested_at=stamped["event_id"],
            body_stored=bool(store_body and parsed.readable),
        )
        existing_skills = [
            row for row in existing_skills if row.get("source") != entry["source"]
        ] + [entry]
        save_manifest(root_path, existing_skills)

    exit_code = _SKILLS_EXIT_CODES[decision.decision]
    if effective_decision == "ALLOW" and decision.decision == "ASK":
        exit_code = 0

    result = {
        "decision": decision.decision,
        "effective_decision": effective_decision,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "trust_level": decision.trust_level,
        "source": parsed.manifest_source,
        "readable": parsed.readable,
        "content_digest": parsed.content_digest_value,
        "compiled_rule_count": compiled_rule_count,
        "manifest": str(root_path / SKILLS_MANIFEST_RELATIVE_PATH),
        "event_id": stamped["event_id"],
        "approval_event_id": approval_event_id,
        "exit_code": exit_code,
    }
    if json_output:
        console.print_json(json.dumps(result))
    else:
        console.print(f"[bold]{decision.decision}[/bold] {parsed.manifest_source}")
        console.print(f"  reason: {decision.reason}")
        if effective_decision == "ALLOW" and decision.decision == "ASK":
            console.print("  approved via --yes; manifest compiled")
        elif effective_decision == "ALLOW":
            console.print(f"  compiled {compiled_rule_count} mechanical rule(s)")
        elif decision.decision == "ASK":
            console.print("  re-run with --yes, or grant trust level 3, to compile")
    raise typer.Exit(exit_code)


@skills_app.command("lens")
def skills_lens(
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """
    Print per-pillar coverage/coherence from ingested skills, with provenance.

    Numbers are always integer ``observed/expected`` and ``passed/observed``
    pairs — never a percentage or a probability. A malformed manifest is
    reported and treated as empty (exit 2); an absent manifest (nothing
    ingested yet) reports 0/0 everywhere and exits 0.
    """
    root_path = Path(root).resolve()
    result = compute_lens(root_path)

    if result.manifest_status == "malformed":
        typer.echo("manifest.json is malformed; treating as empty", err=True)

    if json_output:
        payload = {
            "manifest_status": result.manifest_status,
            "pillars": [
                {
                    "pillar": pillar.pillar,
                    "expected": pillar.expected,
                    "observed": pillar.observed,
                    "passed": pillar.passed,
                    "provenance": [
                        {"rule_id": rid, "skill": skill, "status": status}
                        for rid, skill, status in pillar.provenance
                    ],
                }
                for pillar in result.pillars
            ],
            "unclassified": {
                "pillar": result.unclassified.pillar,
                "expected": result.unclassified.expected,
                "observed": result.unclassified.observed,
                "passed": result.unclassified.passed,
                "provenance": [
                    {"rule_id": rid, "skill": skill, "status": status}
                    for rid, skill, status in result.unclassified.provenance
                ],
            },
            "unobserved": result.unobserved,
        }
        console.print_json(json.dumps(payload))
    else:
        for pillar in [*result.pillars, result.unclassified]:
            console.print(
                f"[bold]{pillar.pillar}[/bold]: "
                f"{pillar.observed}/{pillar.expected} observed, "
                f"{pillar.passed}/{pillar.observed} passed"
            )
            for rid, skill, status in pillar.provenance:
                console.print(f"    [{status}] {rid} ({skill})")
        console.print(f"unobserved: {len(result.unobserved)}")
        for item in result.unobserved:
            console.print(
                f"    {item['rule_id']} ({item['skill']}) digest={item['rule_text_digest']}"
            )

    exit_code = 2 if result.manifest_status == "malformed" else 0
    raise typer.Exit(exit_code)


@skills_app.command("propose")
def skills_propose(
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/skills/"),
    accept: bool = typer.Option(
        False,
        "--accept",
        help="Write .hyodo/skills/proposed.md and record one ledger event",
    ),
):
    """
    Print a tailored custom skill made of every currently-passing compiled
    rule from ingested skills. Without --accept nothing is written and no
    event is recorded; --accept writes exactly one file and records exactly
    one ledger event. Never calls evaluate_policy — nothing external is
    contacted at proposal time, only sources already judged at ingest time.
    """
    root_path = Path(root).resolve()
    project_name = root_path.name or "project"
    result = render_proposal(root_path, project_name)

    if result.manifest_status == "malformed":
        typer.echo("manifest.json is malformed; proposal sections are empty", err=True)

    console.print(result.markdown, end="")

    if accept:
        save_proposal(root_path, result.markdown)
        run_id = str(uuid.uuid4())
        raw_event = _new_agent_event(
            kind="tool_call",
            actor="hyodo",
            tool={
                "name": "skills.propose",
                "paths": [str(SKILLS_MANIFEST_RELATIVE_PATH)],
                "urls": [],
            },
            run_id=run_id,
        )
        ok, _reasons, normalized = validate_event(raw_event)
        if ok and normalized is not None:
            decision = PolicyDecision(
                decision="ALLOW",
                rule_id=None,
                reason="skills propose: local render, no external variable; evaluate_policy not called",
                coverage=(0, 0),
                external_variables=(),
                trust_level=1,
            )
            stamped = apply_decision_to_event(normalized, decision)
            append_agent_event(root_path, stamped)

    raise typer.Exit(0)


_EYE_EXIT_CODES = {"ALLOW": 0, "DENY": 1, "UNOBSERVED": 2, "ASK": 3}


def _load_eye_policy(root_path: Path) -> PolicyConfig:
    """Load ``.hyodo/policy.toml``, falling back to all-defaults when absent.

    ``eye.capture`` is unconditionally discretionary regardless of policy
    presence (like ``skills.ingest``), so a missing policy file must not
    refuse the command outright -- only an unreadable/invalid one does.
    """
    policy_path = root_path / POLICY_RELATIVE_PATH
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is not None:
        return cfg
    if policy_err == "policy_missing":
        return PolicyConfig(
            schema=POLICY_SCHEMA_ID,
            max_steps=None,
            allowed_tools=None,
            blocked_path_globs=(),
        )
    raise typer.Exit(2)


def _print_eye_result(result: CaptureResult, source: str, *, json_output: bool) -> None:
    payload = result.as_dict()
    if json_output:
        console.print_json(json.dumps(payload))
        return
    console.print(f"[bold]{result.decision}[/bold] {source}")
    if result.reason:
        console.print(f"  reason: {result.reason}")
    if result.rule_id:
        console.print(f"  rule_id: {result.rule_id}")
    if result.digest is not None:
        console.print(f"  digest: {result.digest}")
    if result.phash is not None:
        console.print(f"  phash: {result.phash}")
    console.print(f"  destroyed_at: {result.destroyed_at}  kept: {result.kept}")
    if result.decision == "ASK":
        console.print("  re-run with --yes, or grant trust level 3, to capture")
    if result.ledger_write_required:
        console.print("  ledger_write_required: true")


@eye_app.command("capture")
def eye_capture(
    ttl: int = typer.Option(DEFAULT_TTL_S, "--ttl", help="Seconds before the capture is deleted"),
    keep: bool = typer.Option(
        False, "--keep", help="Retain the file instead of deleting it (requires trust level >= 2)"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Approve an ASK decision now; records a human decision event, then proceeds",
    ),
    open_after: bool = typer.Option(
        False, "--open", help="Best-effort open the capture with the OS viewer before destroying it"
    ),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """
    Capture one screen via a BYOM tool (``.hyodo/config.toml``'s ``[eye]
    command`` or ``HYODO_EYE_COMMAND``), record its digest and perceptual
    hash, show it with a countdown, then delete it and record proof of
    destruction. No pixels ever reach the ledger.

    Exit 0 ALLOW, 1 DENY, 2 UNOBSERVED (no tool configured, capture failed,
    unsupported image format, or destruction could not be proven), 3 ASK.
    """
    root_path = Path(root).resolve()
    policy = _load_eye_policy(root_path)
    result = run_eye_capture(
        root_path, policy, ttl_s=ttl, keep=keep, yes=yes, open_after=open_after
    )
    _print_eye_result(result, "eye.capture", json_output=json_output)
    raise typer.Exit(result.exit_code)


@eye_app.command("verify")
def eye_verify(
    against: str = typer.Option(..., "--against", help="event_id of a prior eye-capture event"),
    phash_threshold: int | None = typer.Option(
        None,
        "--phash-threshold",
        help="Hamming distance (0-64) at/below which two captures are 'the same screen'",
    ),
    root: str = typer.Option(".", "--root", help="Project root that owns .hyodo/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """
    Re-capture now (through the same policy gate) and report the Hamming
    distance between the fresh perceptual hash and the referenced event's
    stored hash: "same screen" or "different screen", plus the raw
    distance out of 64 -- never a percentage or a probability. The
    re-capture is itself ephemeral: it is deleted and both its events are
    recorded, exactly like ``eye capture``.
    """
    root_path = Path(root).resolve()
    events, _corrupt = read_agent_events(root_path)
    target: dict[str, Any] | None = None
    if events is not None:
        for event in events:
            if isinstance(event, dict) and event.get("event_id") == against:
                target = event
                break

    if target is None:
        payload = {
            "decision": "UNOBSERVED",
            "reason": f"event {against!r} not found",
            "exit_code": 1,
        }
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]event {against!r} not found[/red]")
        raise typer.Exit(1)

    target_ephemeral = (
        target.get("meta", {}).get("ephemeral") if isinstance(target.get("meta"), dict) else None
    )
    target_phash = target_ephemeral.get("phash") if isinstance(target_ephemeral, dict) else None
    target_algo = target_ephemeral.get("phash_algo") if isinstance(target_ephemeral, dict) else None

    if target_phash is None:
        payload = {
            "decision": "UNOBSERVED",
            "reason": f"event {against!r} has no meta.ephemeral.phash to compare against",
            "exit_code": 1,
        }
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]event {against!r} has no phash to compare against[/red]")
        raise typer.Exit(1)

    if target_algo != "dct64":
        payload = {"decision": "UNOBSERVED", "reason": "phash_algo_mismatch", "exit_code": 1}
        if json_output:
            console.print_json(json.dumps(payload))
        else:
            console.print("phash_algo_mismatch")
        raise typer.Exit(1)

    policy = _load_eye_policy(root_path)
    result = run_eye_capture(root_path, policy, ttl_s=DEFAULT_TTL_S)

    if result.decision != "ALLOW" or result.phash is None:
        _print_eye_result(result, f"eye.verify --against {against}", json_output=json_output)
        raise typer.Exit(result.exit_code)

    threshold = phash_threshold
    if threshold is None:
        threshold = (
            policy.ephemeral.phash_distance_threshold if policy.ephemeral is not None else 10
        )
    distance = phash_distance(target_phash, result.phash)
    same = distance <= threshold
    verdict = "same screen" if same else "different screen"

    payload = {
        **result.as_dict(),
        "against_event_id": against,
        "against_phash": target_phash,
        "distance": distance,
        "threshold": threshold,
        "verdict": verdict,
    }
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        console.print(f"{verdict} (distance {distance} of 64)")
        console.print(f"  new capture digest: {result.digest}")
        console.print(f"  new capture event: {result.capture_event_id}")
    raise typer.Exit(0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version_flag: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """HyoDo - model-agnostic quality gates for AI-assisted development."""
    if version_flag:
        console.print(f"HyoDo v{__version__} - model-agnostic quality gates")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
