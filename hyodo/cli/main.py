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
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import compare_digest, token_urlsafe
from urllib.parse import parse_qs

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hyodo import __version__
from hyodo.dashboard import PILLAR_SPECS, POLL_SCRIPT_SHA256, render_dashboard_html
from hyodo.eval import EvalInputError, run_evaluation
from hyodo.events import (
    AGENT_EVENTS_RELATIVE_PATH,
    append_agent_event,
    count_run_events,
    load_event_from_path,
    load_event_from_text,
    strip_full_bodies,
    validate_event,
)
from hyodo.exceptions import (
    ScanExceptionsConfig,
    ScanExceptionsConfigError,
    is_general_path_excluded,
    load_scan_exceptions,
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
from hyodo.pillars import (
    append_history_receipt,
    collect_hyo_evidence,
    collect_in_evidence,
    collect_yeong_evidence,
)
from hyodo.policy import (
    POLICY_RELATIVE_PATH,
    apply_decision_to_event,
    evaluate_policy,
    try_load_policy,
)
from hyodo.report import write_report
from hyodo.safety import run_safety_scan
from hyodo.schema import validate_schema_payload

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
policy_app = typer.Typer(
    name="policy",
    help="Local policy gate for agent events (ALLOW|DENY; unobserved ≠ ALLOW)",
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
app.add_typer(event_app, name="event")
app.add_typer(policy_app, name="policy")
app.add_typer(schema_app, name="schema")
app.add_typer(mcp_app, name="mcp")
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
    safety_risk: int | None = (
        safety["risk_score"]
        if "empty" not in safety_source and "no diff" not in safety_source
        else None
    )
    evidence: dict[str, object] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "target": str(root),
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "gates": {name: asdict(result) for name, result in gates.items()},
        "safety": {
            "risk_score": safety_risk,
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


DASHBOARD_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; "
    f"script-src 'sha256-{POLL_SCRIPT_SHA256}'; connect-src 'self'"
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
# page at "/" is never a CORS target (a cross-origin page can only read
# response bodies from these two JSON endpoints when the browser lets it).
_CORS_ELIGIBLE_PATHS = frozenset({"/api/evidence", "/api/status"})


def make_dashboard_handler(
    state: DashboardState,
    refresh: Callable[[], dict[str, object]] | None = None,
    refresh_token: str = "",
    allow_origins: tuple[str, ...] = (),
) -> type[BaseHTTPRequestHandler]:
    """Build the loopback request handler serving the current snapshot.

    ``allow_origins`` is an opt-in exact-match CORS allow-list (empty by
    default, matching prior behaviour byte-for-byte: no CORS headers at
    all). No wildcard support — an origin must match one of the configured
    values exactly before ``Access-Control-Allow-Origin`` is echoed back.
    """
    allowed_origins = frozenset(allow_origins)

    class DashboardHandler(BaseHTTPRequestHandler):
        """Serve the dashboard's current loopback snapshot over HTTP."""

        def _resolve(self) -> tuple[bytes, str] | None:
            page, evidence_json = state.snapshot()
            if self.path == "/":
                return page, "text/html; charset=utf-8"
            if self.path == "/api/evidence":
                return evidence_json, "application/json"
            if self.path == "/api/status":
                return state.status(), "application/json"
            return None

        def _cors_headers(self) -> list[tuple[str, str]]:
            """Return (name, value) CORS header pairs for the current request.

            Empty unless: the path is CORS-eligible, an `Origin` request
            header was sent, and it exactly matches a configured allowed
            origin. No wildcard, no partial/prefix/suffix match.
            """
            if self.path not in _CORS_ELIGIBLE_PATHS or not allowed_origins:
                return []
            origin = self.headers.get("Origin")
            if not origin or origin not in allowed_origins:
                return []
            return [("Access-Control-Allow-Origin", origin), ("Vary", "Origin")]

        def _send_headers(self, body: bytes, content_type: str) -> None:
            self.send_response(200)
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
            body, content_type = resolved
            self._send_headers(body, content_type)
            self.wfile.write(body)

        def do_HEAD(self) -> None:
            """Serve headers for a current page or evidence JSON request."""
            resolved = self._resolve()
            if resolved is None:
                self.send_error(404, "Not found")
                return
            body, content_type = resolved
            self._send_headers(body, content_type)

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
):
    """Serve a local, evidence-only Jin-Seon-Mi-In-Hyo-Yeong dashboard."""
    try:
        target = resolve_check_target(path)
    except FileNotFoundError as exc:
        console.print(f"[red]Path not found: {exc}[/red]")
        raise typer.Exit(2) from exc
    root = find_repo_root(target)
    if root is None:
        console.print("[red]dashboard requires a HyoDo checkout (pyproject.toml + hyodo/).[/red]")
        raise typer.Exit(2)
    refresh_token = token_urlsafe(32)
    refresh_lock = threading.Lock()

    def _refresh_evidence() -> dict[str, object]:
        """Collect one serialized local measurement without concurrent gate runs."""
        with refresh_lock:
            return collect_dashboard_evidence(root)

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
            make_dashboard_handler(state, _refresh_evidence, refresh_token, tuple(allow_origin)),
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
    tsconfig = root / "tsconfig.json"
    if tsconfig.exists() and (ts_files or js_files):
        tsc = shutil.which("tsc")
        if tsc:
            results.append(
                _run_general_cmd(
                    "TypeScript",
                    "tsc",
                    [tsc, "--noEmit", "-p", str(tsconfig)],
                    root,
                    verbose,
                    "tsc --noEmit clean",
                )
            )
        else:
            results.append(_skip_missing_tool("TypeScript", "tsc"))
    elif js_files:
        node = shutil.which("node")
        if node:
            results.append(
                _run_per_file_general_cmd("JavaScript", "node --check", node, "--check", js_files)
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


@app.command()
def check(
    path: str | None = typer.Argument(None, help="Path to file or directory"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply auto-fixes where supported"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    general: bool = typer.Option(
        False, "--general", help="Run language-agnostic gates (auto-detect Python/JS/Go/Rust/Shell)"
    ),
):
    """
    Run HyoDo checkout release gates (4-Gate CI).

    Model-agnostic means independent of the AI model or agent UI.
    It does not currently mean language-agnostic or any-repo universal.

    Resolution order: --general (explicit opt-in) -> .hyodo/gates.toml
    (Bring-Your-Own-Gates, if present -- see `hyodo init`) -> HyoDo checkout
    preset (Pyright -> Ruff -> pytest -> SBOM) -> guidance.

    --general instead runs bounded language-agnostic syntax gates
    (Python/TS/JS/Go/Rust/Shell auto-detected, up to 50 files per language).
    """
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
        console.print(
            "[yellow]Not a HyoDo package checkout "
            "(requires pyproject.toml + hyodo/ at project root).[/yellow]"
        )
        console.print(
            "[dim]Model-agnostic ≠ language-agnostic. "
            "General Python project gates are not claimed in this version.[/dim]"
        )
        console.print(
            "[dim]Tip: run 'hyodo init' to absorb this project's own tools as gates "
            "(Bring-Your-Own-Gates).[/dim]"
        )
    else:
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

    executed = [r for r in results if r.status in {GateStatus.PASS, GateStatus.FAIL}]
    failed = [r for r in results if r.status is GateStatus.FAIL]
    ran, total = len(executed), len(results)

    console.print("\n" + "=" * 50)
    if not executed:
        console.print("[bold yellow]No project gates were executed[/bold yellow]")
        console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2)

    if failed:
        console.print(f"[bold red]Some gates failed[/bold red] ({ran}/{total} gates ran)")
        console.print("[yellow]Fix failures, then re-run hyodo check[/yellow]")
        raise typer.Exit(1)

    console.print(f"[bold green]All executed gates passed ({ran}/{total} gates ran)[/bold green]")
    console.print("[green]Gates support review readiness. Human approval still required.[/green]")
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
    partial: bool = typer.Option(
        False, "--partial", help="Allow missing pillars (defaults to 0.5, WEAK signal)"
    ),
):
    """
    Compute HYOGOOK F-score review signal (philosophy V6).

    F = sum(five pillars on 1–10 scale) + geometric_mean
    S = geometric_mean

    All five pillars must be provided explicitly (no silent 1.0 defaults).
    Use --partial to allow missing pillars (filled with 0.5, WEAK signal).
    Legacy --serenity/--eternity may substitute for benevolence/hyo, but
    primary and legacy flags for the same pillar cannot be combined.
    Review emphasis labels are philosophical only — not F-score weights.
    Output is a review signal only — not automatic approval.
    """
    from hyodo import calculate_hygook_v5_score

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

    table = Table(
        title="HYOGOOK F-score Review Signal (philosophy V6)",
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
        "(F = sum(1–10 pillars) + geometric mean). Formula lineage V5 · philosophy V6.[/dim]"
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
    result = run_safety_scan(
        path=path, strict=strict, cwd=Path.cwd(), max_files=max_files, scan_tool=scan
    )
    source = str(result["source"])
    high_only = [f for f in result["findings"] if f.severity == "high"]

    if json_output:
        exit_code = (
            2 if source.startswith(("missing:", "error:")) else (1 if strict and high_only else 0)
        )
        payload = {
            "source": source,
            "risk_score": result["risk_score"],
            "level": result["level"],
            "action": result["action"],
            "strict": strict,
            "exit_code": exit_code,
            "findings": [asdict(f) for f in result["findings"]],
            "exceptions_applied": int(result.get("exceptions_applied", 0)),
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(exit_code)

    console.print(Panel.fit("HyoDo Safety Check (early warning)", style="bold yellow"))
    console.print(f"source: {source}")
    exceptions_applied = int(result.get("exceptions_applied", 0))
    if exceptions_applied:
        console.print(f"[yellow]Audited safety exceptions applied: {exceptions_applied}[/yellow]")

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

    console.print(f"\nRisk: {result['level']} ({result['risk_score']}/100)\n-> {result['action']}")
    cap_note = "unlimited" if max_files <= 0 else f"{max_files} files"
    console.print(
        "[dim]Note: early warning only. Not a full SAST/secret-scan/dependency audit. "
        f"Directory scan cap: {cap_note}; default corpus is git diff/status when no path.[/dim]"
    )

    if strict and high_only:
        raise typer.Exit(1)
    raise typer.Exit(0)


@mcp_app.command("stdio")
def mcp_stdio(
    root: str = typer.Option(".", "--root", help="Workspace root locked for this MCP process"),
):
    """Run the optional local MCP adapter over standard input/output."""
    try:
        import mcp.server.fastmcp  # pyright: ignore[reportMissingImports]  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mcp"):
            console.print("[red]MCP support is not installed.[/red]")
            console.print("Install it with: pip install 'hyodo[mcp]'", style="yellow", markup=False)
            raise typer.Exit(2) from exc
        raise

    from hyodo.mcp_server import run_stdio

    try:
        run_stdio(Path(root))
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
        help="Optional for loopback; required and non-empty for Tailscale",
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
        if token is None or not token.strip():
            console.print(
                "[red]--bind tailscale requires a non-empty bearer token before listening.[/red]"
            )
            raise typer.Exit(2)
        assert token is not None
        tailscale_ip = str(candidate)
    try:
        import mcp.server.fastmcp  # pyright: ignore[reportMissingImports]  # noqa: F401
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
        console.print(
            "  auth:      bearer token configured" if token else "  auth:      local process trust"
        )
        if bind == "tailscale":
            run_tailscale(root_path, host=host, port=port, token=token or "")
        else:
            run_loopback(root_path, port=port, token=token)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


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
    report_format: str = typer.Option("md", "--format", help="Local report format: md or html"),
    root: str = typer.Option(".", "--root", help="Project root that owns local evidence"),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable report summary"
    ),
):
    """Render a local FDE sign-off report from observed evidence only."""
    if report_format not in {"md", "html"}:
        console.print("[red]--format must be md or html[/red]")
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
):
    """
    Validate and append one agent event to .hyodo/agent-events.jsonl.

    Default storage is digest-only (strips full text bodies). Use --full-body
    only when the operator accepts retaining raw payloads.

    With --policy: evaluate policy, stamp policy.* on the event, always try to
    append (including DENY) for audit continuity. Exit 1 on DENY or invalid
    event; exit 2 when input/policy path is unreadable or policy is unobserved.

    HyoDo is a gate, not an agent runtime — callers must enforce DENY.
    """
    root_path = Path(root).resolve()
    file_path = Path(file) if file else None
    data, err = _load_event_payload(file_path, stdin_flag)
    if err in {"file_and_stdin", "missing_input"} or err is not None:
        code = 2
        reasons = [err or "load_failed"]
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": code}))
        else:
            console.print(f"[red]Cannot load event: {err}[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(code)

    ok, reasons, normalized = validate_event(data)
    if not ok or normalized is None:
        if json_output:
            console.print_json(json.dumps({"ok": False, "reasons": reasons, "exit_code": 1}))
        else:
            console.print("[red]INVALID[/red] event — not recorded")
            for reason in reasons:
                console.print(f"  - {reason}")
        raise typer.Exit(1)

    if not full_body:
        normalized = strip_full_bodies(normalized)

    decision_label = None
    if policy is not None:
        cfg, policy_err = try_load_policy(Path(policy))
        if cfg is None:
            # Fail-closed: missing/invalid policy is unobserved, never ALLOW.
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
        decision = evaluate_policy(normalized, cfg, observed_steps=observed)
        normalized = apply_decision_to_event(normalized, decision)
        decision_label = decision.decision

    if not append_agent_event(root_path, normalized):
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "ok": False,
                        "reasons": ["append_failed"],
                        "exit_code": 2,
                        "ledger": str(root_path / AGENT_EVENTS_RELATIVE_PATH),
                    }
                )
            )
        else:
            console.print("[red]Failed to append agent event ledger.[/red]")
            console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2)

    exit_code = 1 if decision_label == "DENY" else 0
    ledger = str(root_path / AGENT_EVENTS_RELATIVE_PATH)
    if json_output:
        console.print_json(
            json.dumps(
                {
                    "ok": exit_code == 0,
                    "exit_code": exit_code,
                    "event_id": normalized["event_id"],
                    "decision": decision_label,
                    "ledger": ledger,
                    "full_body": full_body,
                }
            )
        )
    else:
        console.print(f"[green]RECORDED[/green] {normalized['event_id']}")
        console.print(f"ledger: {ledger}")
        if decision_label is not None:
            color = "red" if decision_label == "DENY" else "green"
            console.print(f"policy: [{color}]{decision_label}[/{color}]")
            if decision_label == "DENY":
                console.print(
                    "[yellow]DENY is recorded for audit; the caller must stop "
                    "the agent. HyoDo is not a runtime interceptor.[/yellow]"
                )
    raise typer.Exit(exit_code)


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
        help="policy.toml path (default: ./.hyodo/policy.toml)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable decision JSON",
    ),
):
    """
    Evaluate one event against a local policy.toml.

    Exit: 0 ALLOW · 1 DENY · 2 unobserved (missing/invalid policy or event).
    Does not write the ledger (use ``hyodo event record --policy`` for that).
    """
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
        Path(config).resolve() if config else (Path.cwd() / POLICY_RELATIVE_PATH).resolve()
    )
    cfg, policy_err = try_load_policy(policy_path)
    if cfg is None:
        if json_output:
            console.print_json(
                json.dumps(
                    {
                        "decision": "UNOBSERVED",
                        "rule_id": None,
                        "reason": policy_err,
                        "exit_code": 2,
                    }
                )
            )
        else:
            console.print(f"[red]Policy unobserved ({policy_err}).[/red] Not ALLOW.")
        raise typer.Exit(2)

    # Step budget is counted from the working-tree ledger, never from the
    # caller-supplied step_index. (Same cwd basis as the default policy lookup.)
    observed = count_run_events(Path.cwd(), normalized["run_id"])
    decision = evaluate_policy(normalized, cfg, observed_steps=observed)
    # 0 = ALLOW, 1 = DENY, 2 = unobserved. UNOBSERVED must not exit like a plain DENY.
    exit_code = (
        0 if decision.decision == "ALLOW" else (2 if decision.decision == "UNOBSERVED" else 1)
    )
    if json_output:
        payload = decision.as_dict()
        payload["exit_code"] = exit_code
        console.print_json(json.dumps(payload))
    else:
        color = "green" if decision.decision == "ALLOW" else "red"
        console.print(f"[{color}]{decision.decision}[/{color}]")
        if decision.rule_id:
            console.print(f"rule_id: {decision.rule_id}")
        if decision.reason:
            console.print(f"reason: {decision.reason}")
    raise typer.Exit(exit_code)


@app.command()
def start():
    """Print HyoDo onboarding guide and basic usage."""
    guide = """
[bold blue]HyoDo quick start[/bold blue]

[b]HyoDo is a model-agnostic quality-gate kit for AI-assisted development.[/b]
Model-agnostic means independent of the AI model or agent UI — not language-agnostic.

Works with Claude Code, Codex, Grok, Gemini CLI, Cursor, or plain terminal.

[bold cyan]Core commands:[/bold cyan]
  • [bold]check[/bold]  - HyoDo checkout release gates (ruff/pyright/pytest)
  • [bold]score[/bold]  - HYOGOOK F-score review signal, philosophy V6 (not auto-approval)
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
    console.print(guide)


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
