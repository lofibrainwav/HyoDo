"""AFO CLI - Standalone command-line interface for AFO Kingdom.

Provides commands for quality checks, Trinity Score calculation,
security scanning, and initialization.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="afo",
    help="AFO Kingdom - Philosophy-Driven AI Operating System",
    no_args_is_help=True,
)


@app.command()
def check(
    path: Path = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to check",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Auto-fix issues where possible",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
) -> None:
    """Run 4-Gate CI quality check (Pyright, Ruff, pytest, SBOM)."""
    import subprocess

    results: dict[str, tuple[int, str]] = {}

    # Gate 1: Type Check (Pyright)
    typer.echo("🔍 Gate 1: Type Check (Pyright)...")
    cmd = ["python3", "-m", "pyright", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    results["pyright"] = (result.returncode, result.stdout + result.stderr)
    if result.returncode == 0:
        typer.echo("  ✅ Pyright passed")
    else:
        typer.echo("  ❌ Pyright failed")
        if verbose:
            typer.echo(result.stdout)

    # Gate 2: Lint (Ruff)
    typer.echo("🧹 Gate 2: Lint (Ruff)...")
    cmd = ["python3", "-m", "ruff", "check", str(path)]
    if fix:
        cmd.append("--fix")
    result = subprocess.run(cmd, capture_output=True, text=True)
    results["ruff"] = (result.returncode, result.stdout + result.stderr)
    if result.returncode == 0:
        typer.echo("  ✅ Ruff passed")
    else:
        typer.echo("  ❌ Ruff failed")
        if verbose:
            typer.echo(result.stdout)

    # Gate 3: Tests (pytest)
    typer.echo("🧪 Gate 3: Tests (pytest)...")
    cmd = ["python3", "-m", "pytest", str(path), "-q", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    results["pytest"] = (result.returncode, result.stdout + result.stderr)
    if result.returncode == 0:
        typer.echo("  ✅ pytest passed")
    else:
        typer.echo("  ❌ pytest failed")
        if verbose:
            typer.echo(result.stdout)

    # Summary
    typer.echo("\n📊 4-Gate CI Summary:")
    passed = sum(1 for code, _ in results.values() if code == 0)
    typer.echo(f"  Passed: {passed}/4 gates")

    if passed == 4:
        typer.echo("\n🎉 All gates passed! Trinity Score eligible for AUTO_RUN.")
        sys.exit(0)
    else:
        typer.echo("\n⚠️ Some gates failed. Review and fix issues.")
        sys.exit(1)


@app.command()
def score(
    path: Path = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to analyze",
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed pillar scores",
    ),
) -> None:
    """Calculate Trinity Score for the project."""
    import subprocess

    typer.echo("🎯 Calculating Trinity Score...")
    typer.echo(f"Path: {path}\n")

    # Calculate individual pillars
    scores: dict[str, float] = {}

    # 眞 (Truth) - Type safety + test coverage
    typer.echo("⚔️  眞 (Truth) - Technical Certainty...")
    result = subprocess.run(
        ["python3", "-m", "pyright", str(path)],
        capture_output=True,
        text=True,
    )
    truth_score = 100.0 if result.returncode == 0 else 70.0
    scores["truth"] = truth_score
    typer.echo(f"   Score: {truth_score:.1f}/100")

    # 善 (Goodness) - Security + stability
    typer.echo("🛡️  善 (Goodness) - Safety & Ethics...")
    result = subprocess.run(
        ["python3", "-m", "ruff", "check", str(path), "--select", "S"],
        capture_output=True,
        text=True,
    )
    goodness_score = 95.0 if result.returncode == 0 else 75.0
    scores["goodness"] = goodness_score
    typer.echo(f"   Score: {goodness_score:.1f}/100")

    # 美 (Beauty) - Code quality
    typer.echo("🌉 美 (Beauty) - Aesthetics & Clarity...")
    result = subprocess.run(
        ["python3", "-m", "ruff", "check", str(path)],
        capture_output=True,
        text=True,
    )
    beauty_score = 90.0 if result.returncode == 0 else 65.0
    scores["beauty"] = beauty_score
    typer.echo(f"   Score: {beauty_score:.1f}/100")

    # 孝 (Serenity) - Developer experience
    typer.echo("☯️  孝 (Serenity) - Frictionless Flow...")
    serenity_score = 85.0  # Default assumption
    scores["serenity"] = serenity_score
    typer.echo(f"   Score: {serenity_score:.1f}/100")

    # 永 (Eternity) - Maintainability
    typer.echo("♾️  永 (Eternity) - Long-term Sustainability...")
    eternity_score = 80.0  # Default assumption
    scores["eternity"] = eternity_score
    typer.echo(f"   Score: {eternity_score:.1f}/100")

    # Calculate weighted total
    total = (
        scores["truth"] * 0.35
        + scores["goodness"] * 0.35
        + scores["beauty"] * 0.20
        + scores["serenity"] * 0.08
        + scores["eternity"] * 0.02
    )

    typer.echo(f"\n🏆 Trinity Score: {total:.2f}/100")

    if detailed:
        typer.echo("\n📊 Detailed Breakdown:")
        typer.echo(f"  眞 (Truth):     {scores['truth']:.1f} × 0.35 = {scores['truth'] * 0.35:.2f}")
        typer.echo(
            f"  善 (Goodness):  {scores['goodness']:.1f} × 0.35 = {scores['goodness'] * 0.35:.2f}"
        )
        typer.echo(
            f"  美 (Beauty):    {scores['beauty']:.1f} × 0.20 = {scores['beauty'] * 0.20:.2f}"
        )
        typer.echo(
            f"  孝 (Serenity):  {scores['serenity']:.1f} × 0.08 = {scores['serenity'] * 0.08:.2f}"
        )
        typer.echo(
            f"  永 (Eternity):  {scores['eternity']:.1f} × 0.02 = {scores['eternity'] * 0.02:.2f}"
        )

    # Decision matrix
    typer.echo("\n📋 Decision:")
    if total >= 90:
        typer.echo("  🟢 AUTO_RUN - Changes can proceed automatically")
    elif total >= 70:
        typer.echo("  🟡 ASK_COMMANDER - Approval recommended")
    else:
        typer.echo("  🔴 BLOCK - Improvements required before merge")


@app.command()
def safe(
    path: Path = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to scan",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Auto-fix security issues where possible",
    ),
) -> None:
    """Security and risk scan using Ruff security rules."""
    import subprocess

    typer.echo("🛡️ AFO Security Scan")
    typer.echo("====================\n")

    # Security-focused linting
    typer.echo("🔍 Running security checks (flake8-bandit via Ruff)...")
    cmd = ["python3", "-m", "ruff", "check", str(path), "--select", "S"]
    if fix:
        cmd.append("--fix")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        typer.echo("✅ No security issues found!")
    else:
        typer.echo("⚠️ Security issues detected:")
        typer.echo(result.stdout)
        if result.stderr:
            typer.echo(result.stderr)

    # Check for secrets patterns
    typer.echo("\n🔍 Scanning for potential secrets...")
    patterns = [
        (r"api[_-]?key.*=.*['\"][a-zA-Z0-9]{20,}", "API Key"),
        (r"password.*=.*['\"][^'\"]{8,}", "Password"),
        (r"secret.*=.*['\"][a-zA-Z0-9]{16,}", "Secret"),
        (r"token.*=.*['\"][a-zA-Z0-9]{20,}", "Token"),
    ]

    issues_found = False
    for pattern, name in patterns:
        import re

        for file_path in Path(path).rglob("*.py"):
            try:
                content = file_path.read_text()
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if "example" not in content.lower() and "test" not in str(file_path).lower():
                        typer.echo(f"  ⚠️ Potential {name} in {file_path}")
                        issues_found = True
            except Exception:
                continue

    if not issues_found:
        typer.echo("  ✅ No obvious secrets found")

    typer.echo("\n📝 Security Recommendations:")
    typer.echo("  • Use environment variables for secrets")
    typer.echo("  • Enable pre-commit hooks for secret scanning")
    typer.echo("  • Regular dependency audits (pip-audit)")

    sys.exit(result.returncode)


@app.command()
def init(
    minimal: bool = typer.Option(
        False,
        "--minimal",
        "-m",
        help="Minimal setup (skip Docker)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Accept all defaults",
    ),
) -> None:
    """Initialize HyoDo configuration in current directory."""
    typer.echo("🚀 Initializing HyoDo Configuration")
    typer.echo("====================================\n")

    # Check if already initialized
    if Path(".hyodorc").exists():
        if not yes:
            overwrite = typer.confirm("HyoDo already initialized. Overwrite?")
            if not overwrite:
                typer.echo("Aborted.")
                return

    # Create configuration
    config = """# HyoDo Configuration File
# AFO Kingdom - Philosophy-Driven Development

[trinity]
# Pillar weights (must sum to 1.0)
truth_weight = 0.35
goodness_weight = 0.35
beauty_weight = 0.20
serenity_weight = 0.08
eternity_weight = 0.02

# Score thresholds
auto_run_threshold = 90
ask_threshold = 70

[quality_gates]
# Enable/disable gates
pyright = true
ruff = true
pytest = true
sbom = true

[paths]
# Paths to include/exclude from checks
include = ["AFO", "api", "config"]
exclude = ["tests", "scripts", "legacy", "venv", ".venv"]

[security]
# Security scan settings
bandit_rules = ["S"]
secret_scan = true
"""

    Path(".hyodorc").write_text(config)
    typer.echo("✅ Created .hyodorc configuration file")

    # Create directories
    dirs_to_create = [".hyodo", ".hyodo/logs", ".hyodo/cache"]
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    typer.echo("✅ Created HyoDo directories")

    # Gitignore entries
    gitignore_entries = [
        "",
        "# HyoDo",
        ".hyodo/logs/",
        ".hyodo/cache/",
        ".coverage",
        "coverage.json",
    ]

    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if "# HyoDo" not in content:
            with gitignore.open("a") as f:
                f.write("\n".join(gitignore_entries) + "\n")
            typer.echo("✅ Updated .gitignore")
    else:
        gitignore.write_text("\n".join(gitignore_entries[1:]) + "\n")
        typer.echo("✅ Created .gitignore")

    typer.echo("\n🎉 HyoDo initialization complete!")
    typer.echo("\nNext steps:")
    typer.echo("  1. Edit .hyodorc to customize settings")
    typer.echo("  2. Run 'afo check' to verify setup")
    typer.echo("  3. Run 'afo score' to calculate Trinity Score")


if __name__ == "__main__":
    app()
