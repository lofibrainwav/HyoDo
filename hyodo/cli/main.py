#!/usr/bin/env python3
"""
HyoDo CLI Main Entry Point

Model-agnostic quality-gate CLI. Works with or without any specific agent UI.
"Model-agnostic" means independent of the AI model or agent UI.
It does not currently mean language-agnostic.

Usage: hyodo [COMMAND] [OPTIONS]

Examples:
    hyodo check              # HyoDo checkout release gates
    hyodo score              # HYOGOOK V5 review signal
    hyodo safe               # lightweight safety scan
    hyodo safe --strict      # block on high-severity findings
    hyodo trinity "task"     # detailed review checklist
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hyodo import __version__
from hyodo.safety import run_safety_scan

app = typer.Typer(
    name="hyodo",
    help="HyoDo - model-agnostic AI code quality gates",
    add_completion=True,
)
console = Console()


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class GateResult:
    status: GateStatus
    message: str


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


def afo_core_path(root: Path | None = None) -> Path | None:
    """Return the extended AFO core path when available in a repository checkout."""
    repo = root if root is not None else find_repo_root()
    if not repo:
        return None

    candidates = [
        repo / "packages" / "afo-core",
        repo / "afo_core",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


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

    cmd = _tool_cmd("pyright", "hyodo")
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(root))
        if result.returncode == 0:
            return GateResult(GateStatus.PASS, "SBOM generated successfully")
        error_msg = result.stderr.strip() or result.stdout.strip()
        msg = error_msg[:200] if len(error_msg) > 200 else error_msg
        return GateResult(GateStatus.FAIL, msg or "SBOM failed")
    except FileNotFoundError:
        return GateResult(GateStatus.FAIL, "python executable not found")
    except subprocess.TimeoutExpired:
        return GateResult(GateStatus.FAIL, "timeout (>60s)")
    except Exception as e:
        return GateResult(GateStatus.FAIL, f"exception: {e}")


def _print_gate_result(result: GateResult) -> None:
    if result.status is GateStatus.PASS:
        console.print(f"  [green]PASS {result.message}[/green]")
    elif result.status is GateStatus.FAIL:
        console.print(f"  [red]FAIL {result.message}[/red]")
    elif result.status is GateStatus.SKIP:
        console.print(f"  [yellow]SKIP {result.message}[/yellow]")
    else:
        console.print(f"  [yellow]UNSUPPORTED {result.message}[/yellow]")


@app.command()
def version():
    """Print HyoDo version."""
    console.print(f"HyoDo v{__version__} - model-agnostic quality gates")


@app.command()
def check(
    path: str | None = typer.Argument(None, help="Path to file or directory"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply auto-fixes where supported"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Run HyoDo checkout release gates (4-Gate CI).

    Model-agnostic means independent of the AI model or agent UI.
    It does not currently mean language-agnostic or any-repo universal.

    Order: Pyright -> Ruff -> pytest -> SBOM
    """
    console.print(Panel.fit("HyoDo Code Quality Check", style="bold blue"))

    try:
        target = resolve_check_target(path)
    except FileNotFoundError as exc:
        console.print(f"[red]Path not found: {exc}[/red]")
        console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2) from exc

    console.print(f"Target: {target}")
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

    console.print("\n" + "=" * 50)
    if not executed:
        console.print("[bold yellow]No project gates were executed[/bold yellow]")
        console.print("[yellow]This is not a validation pass.[/yellow]")
        raise typer.Exit(2)

    if failed:
        console.print("[bold red]Some gates failed[/bold red]")
        console.print("[yellow]Fix failures, then re-run hyodo check[/yellow]")
        raise typer.Exit(1)

    console.print("[bold green]All executed gates passed[/bold green]")
    console.print("[green]Gates support review readiness. Human approval still required.[/green]")
    raise typer.Exit(0)


@app.command()
def score(
    benevolence: float = typer.Option(1.0, "--benevolence", "-i", help="Benevolence score (0-1)"),
    truth: float = typer.Option(1.0, "--truth", "-t", help="Truth score (0-1)"),
    goodness: float = typer.Option(1.0, "--goodness", "-g", help="Goodness score (0-1)"),
    loyalty: float = typer.Option(1.0, "--loyalty", "-c", help="Loyalty score (0-1)"),
    beauty: float = typer.Option(1.0, "--beauty", "-b", help="Beauty score (0-1)"),
    serenity: float = typer.Option(
        1.0, "--serenity", "-s", help="[Legacy] maps to benevolence (0-1)"
    ),
    eternity: float = typer.Option(1.0, "--eternity", "-e", help="[Legacy] maps to loyalty (0-1)"),
):
    """
    Compute HYOGOOK V5 review signal.

    F = sum(five pillars on 1–10 scale) + geometric_mean
    S = geometric_mean

    Review emphasis labels are philosophical emphasis only — not F-score weights.
    Output is a review signal only — not automatic approval.
    """
    from hyodo import calculate_hygook_v5_score

    effective_benevolence = benevolence if serenity == 1.0 else serenity
    effective_loyalty = loyalty if eternity == 1.0 else eternity

    F, S = calculate_hygook_v5_score(
        effective_benevolence, truth, goodness, effective_loyalty, beauty
    )
    score_value = ((F - 6) / (60 - 6)) * 100

    table = Table(title="HYOGOOK V5 Review Signal", show_header=True)
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
        "Loyalty",
        f"{effective_loyalty * 100:.0f}",
        "15% (not in F)",
        f"{effective_loyalty:.2f}",
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
        "(F = sum(1–10 pillars) + geometric mean).[/dim]"
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


@app.command()
def safe(
    path: str | None = typer.Argument(None, help="Path to scan"),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit 1 when any high-severity finding is present (CI gate)",
    ),
):
    """
    Safety early-warning scan.

    Default mode always exits 0 after printing findings (early warning).
    --strict exits 1 on high-severity findings; medium/caution alone stays 0.
    Missing path / scan failure exits 2.

    Limits: directory scans read at most 40 files; default mode prefers git diff
    HEAD, else git status text (not full working tree contents).
    Not a full SAST / secret-scan / dependency audit.
    """
    console.print(Panel.fit("HyoDo Safety Check (early warning)", style="bold yellow"))

    result = run_safety_scan(path=path, strict=strict, cwd=Path.cwd())
    source = str(result["source"])
    console.print(f"source: {source}")

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
            console.print(
                f"  - [{finding.severity}] {finding.category}/{finding.label}: {finding.detail}"
            )

    console.print(f"\nRisk: {result['level']} ({result['risk_score']}/100)\n-> {result['action']}")
    console.print(
        "[dim]Note: early warning only. Not a full SAST/secret-scan/dependency audit. "
        "Directory scan cap: 40 files; default corpus is git diff/status when no path.[/dim]"
    )

    high_only = [f for f in result["findings"] if f.severity == "high"]
    if strict and high_only:
        raise typer.Exit(1)
    raise typer.Exit(0)


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
  • [bold]score[/bold]  - HYOGOOK V5 review signal (not auto-approval)
  • [bold]safe[/bold]   - lightweight safety early-warning scan
  • [bold]safe --strict[/bold] - exit 1 on high-severity findings
  • [bold]trinity[/bold] - structured review checklist

[bold cyan]Examples:[/bold cyan]
  $ hyodo check
  $ hyodo score -t 0.9 -g 0.8
  $ hyodo safe --strict

[bold cyan]Boundary:[/bold cyan]
  Scores and scans support review. Human approval remains required.
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
