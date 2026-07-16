#!/usr/bin/env python3
"""
HyoDo CLI Main Entry Point

Model-agnostic quality-gate CLI. Works with or without any specific agent UI.
Usage: hyodo [COMMAND] [OPTIONS]

Examples:
    hyodo check              # code quality gates
    hyodo score              # HYOGOOK V5 review signal
    hyodo safe               # lightweight safety scan
    hyodo trinity "task"     # detailed review checklist
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple

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


def find_repo_root(start: Optional[Path] = None) -> Optional[Path]:
    """Find a HyoDo repository checkout root, if the CLI is running inside one."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "hyodo").exists():
            return candidate
    return None


def afo_core_path() -> Optional[Path]:
    """Return the extended AFO core path when available in a repository checkout."""
    root = find_repo_root()
    if not root:
        return None

    candidates = [
        root / "packages" / "afo-core",
        root / "afo_core",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def run_pyright_check(verbose: bool = False) -> Tuple[bool, str]:
    """Gate 1: Pyright ( - Truth) - Type checking."""
    # Public package is the release gate. Extended afo_core is advisory only.
    cmd = ["pyright", "hyodo"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return True, "0 errors, 0 warnings"

        error_count = result.stdout.count("error:") + result.stderr.count("error:")
        warning_count = result.stdout.count("warning:") + result.stderr.count("warning:")

        return False, f"{error_count} errors, {warning_count} warnings"

    except FileNotFoundError:
        return False, "pyright not found (install: pip install pyright)"
    except subprocess.TimeoutExpired:
        return False, "timeout (>120s)"
    except Exception as e:
        return False, f"exception: {e}"


def run_ruff_check(fix: bool = False, verbose: bool = False) -> Tuple[bool, str]:
    """Gate 2: Ruff ( - Beauty) - Lint & Format."""
    root = find_repo_root()
    cwd = root or Path.cwd()
    target = "hyodo" if root else "."

    cmd = ["ruff", "check", target]
    if fix:
        cmd.append("--fix")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(cwd))

        if result.returncode == 0:
            return True, "All checks passed!"

        violations = result.stdout.strip() if result.stdout else result.stderr.strip()
        return False, violations[:200] + "..." if len(violations) > 200 else violations

    except FileNotFoundError:
        return False, "ruff not found (install: pip install ruff)"
    except subprocess.TimeoutExpired:
        return False, "timeout (>60s)"
    except Exception as e:
        return False, f"exception: {e}"


def run_pytest_check(verbose: bool = False) -> Tuple[bool, str]:
    """Gate 3: pytest ( - Goodness) - Test coverage."""
    root = find_repo_root()

    # Public package tests first. afo_core remains optional/advisory.
    if root and (root / "tests").exists():
        cmd = ["pytest", str(root / "tests"), "-q", "--tb=short"]
    else:
        return True, "No repository test suite found; package smoke checks only"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "passed" in line.lower():
                    return True, line.strip()
            return True, "All tests passed!"

        return False, f"exit code {result.returncode}"

    except FileNotFoundError:
        return False, "pytest not found (install: pip install pytest)"
    except subprocess.TimeoutExpired:
        return False, "timeout (>300s)"
    except Exception as e:
        return False, f"exception: {e}"


def run_sbom_check(verbose: bool = False) -> Tuple[bool, str]:
    """Gate 4: SBOM ( - Eternity) - Security seal."""
    root = find_repo_root()
    if not root:
        return True, "No repository checkout found; SBOM skipped in package mode"

    sbom_script = root / "scripts" / "generate_sbom.py"
    if not sbom_script.exists():
        return True, "SBOM script not found; skipped"

    cmd = ["python", str(sbom_script)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            return True, "SBOM generated successfully"

        error_msg = result.stderr.strip() or result.stdout.strip()
        return False, error_msg[:200] if len(error_msg) > 200 else error_msg

    except FileNotFoundError:
        return False, "python executable not found"
    except subprocess.TimeoutExpired:
        return False, "timeout (>60s)"
    except Exception as e:
        return False, f"exception: {e}"


@app.command()
def version():
    """Print HyoDo version."""
    console.print(f"HyoDo v{__version__} - model-agnostic quality gates")


@app.command()
def check(
    path: Optional[str] = typer.Argument(None, help="Path to file or directory"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply auto-fixes where supported"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Run code quality gates (4-Gate CI).

    Order: Pyright -> Ruff -> pytest -> SBOM
    """
    console.print(Panel.fit("HyoDo Code Quality Check", style="bold blue"))

    target = path or "."
    console.print(f"Target: {target}")

    all_passed = True

    console.print("\n[1/4] Truth - Type checking...")
    pyright_ok, pyright_msg = run_pyright_check(verbose)
    if pyright_ok:
        console.print(f"  [green]PASS {pyright_msg}[/green]")
    else:
        console.print(f"  [red]FAIL {pyright_msg}[/red]")
        all_passed = False

    console.print("\n[2/4] Beauty - Lint & Format...")
    ruff_ok, ruff_msg = run_ruff_check(fix, verbose)
    if ruff_ok:
        console.print(f"  [green]PASS {ruff_msg}[/green]")
    else:
        console.print(f"  [red]FAIL {ruff_msg}[/red]")
        if "not found" not in ruff_msg and fix:
            console.print("  [yellow]   Try running with --fix to auto-fix issues[/yellow]")
        all_passed = False

    console.print("\n[3/4] Goodness - Tests...")
    pytest_ok, pytest_msg = run_pytest_check(verbose)
    if pytest_ok:
        console.print(f"  [green]PASS {pytest_msg}[/green]")
    else:
        console.print(f"  [red]FAIL {pytest_msg}[/red]")
        all_passed = False

    console.print("\n[4/4] Eternity - Security seal...")
    sbom_ok, sbom_msg = run_sbom_check(verbose)
    if sbom_ok:
        console.print(f"  [green]PASS {sbom_msg}[/green]")
    else:
        console.print(f"  [red]FAIL {sbom_msg}[/red]")
        all_passed = False

    console.print("\n" + "=" * 50)
    if all_passed:
        console.print("[bold green]All gates passed[/bold green]")
        console.print(
            "[green]Gates support review readiness. Human approval still required.[/green]"
        )
    else:
        console.print("[bold red]Some gates failed[/bold red]")
        console.print("[yellow]Fix failures, then re-run hyodo check[/yellow]")


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

    Weights: Benevolence 25%, Truth 22%, Goodness 18%, Loyalty 15%, Beauty 15%.
    Eternity is the geometric mean of the five pillars.

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
    table.add_column("Weight", justify="right")
    table.add_column("Value", justify="right")

    table.add_row(
        "Benevolence",
        f"{effective_benevolence * 100:.0f}",
        "25%",
        f"{effective_benevolence:.2f}",
    )
    table.add_row("Truth", f"{truth * 100:.0f}", "22%", f"{truth:.2f}")
    table.add_row("Goodness", f"{goodness * 100:.0f}", "18%", f"{goodness:.2f}")
    table.add_row("Loyalty", f"{effective_loyalty * 100:.0f}", "15%", f"{effective_loyalty:.2f}")
    table.add_row("Beauty", f"{beauty * 100:.0f}", "15%", f"{beauty:.2f}")
    table.add_row("", "", "", "")
    table.add_row("Eternity (S)", "", "derived", f"{S:.4f}")
    table.add_row("F Score", "", "", f"{F:.2f}")
    table.add_row("", "", "", "")
    table.add_row("[bold]TOTAL", "", "", f"[bold]{score_value:.1f}%[/bold]")

    console.print(table)

    if score_value >= 90:
        console.print("\n[bold green]REVIEW_SIGNAL_STRONG (90+)[/bold green]")
        console.print(
            "[green]Candidate for approval after tests, security checks, and human review.[/green]"
        )
    elif score_value >= 70:
        console.print("\n[bold yellow]REVIEW_SIGNAL_CAUTION (70-89)[/bold yellow]")
        console.print("[yellow]Review recommended before proceed.[/yellow]")
    else:
        console.print("\n[bold red]REVIEW_SIGNAL_BLOCK (<70)[/bold red]")
        console.print(
            "[red]Improve before merge. Score is not a substitute for human judgment.[/red]"
        )


@app.command()
def safe(
    path: Optional[str] = typer.Argument(None, help="Path to scan"),
    strict: bool = typer.Option(False, "--strict", help="Strict mode"),
):
    """
    Safety early-warning scan.

    Scans for secret-like patterns, dangerous commands, and production-impact signals.
    Does not replace a full security scanner.
    """
    console.print(Panel.fit("HyoDo Safety Check (early warning)", style="bold yellow"))

    result = run_safety_scan(path=path, strict=strict, cwd=Path.cwd())
    console.print(f"source: {result['source']}")

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
        "[dim]Note: early warning only. Not a full SAST/secret-scan/dependency audit.[/dim]"
    )


@app.command()
def start():
    """Print HyoDo onboarding guide and basic usage."""
    guide = """
[bold blue]HyoDo quick start[/bold blue]

[b]HyoDo is a model-agnostic quality-gate kit for AI-assisted development.[/b]

Works with Claude Code, Codex, Grok, Gemini CLI, Cursor, or plain terminal.

[bold cyan]Core commands:[/bold cyan]
  • [bold]check[/bold]  - quality gates (ruff/pyright/pytest)
  • [bold]score[/bold]  - HYOGOOK V5 review signal (not auto-approval)
  • [bold]safe[/bold]   - lightweight safety early-warning scan
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
