"""Lightweight safety scan helpers for the public HyoDo CLI.

These checks are early-warning signals only. They do not replace secret scanning,
SAST, dependency audit, tests, or human security review.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# Secret-like patterns (high signal, intentionally narrow to limit false positives).
SECRET_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    (
        "generic_api_key_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
)

DANGEROUS_COMMAND_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    # Target must begin with `/` (root/absolute) or `~` (home). `\S*` consumes the
    # rest of the token, so bare `rm -rf /`, `rm -rf /*` and `rm -rf ~` at end of
    # line are detected (the previous trailing `\b` missed non-word-ending targets).
    # Relative targets (`./build`, `build/`) never start with `/` or `~`, so they
    # stay undetected.
    ("rm_rf_root", re.compile(r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|--force\s+)*[/~]\S*")),
    ("git_reset_hard", re.compile(r"\bgit\s+reset\s+--hard\b")),
    ("git_push_force", re.compile(r"\bgit\s+push\b[^\n]*\s--force\b")),
    ("drop_database", re.compile(r"(?i)\bDROP\s+(DATABASE|SCHEMA)\b")),
    ("drop_table", re.compile(r"(?i)\bDROP\s+TABLE\b")),
    ("chmod_777", re.compile(r"\bchmod\s+(-R\s+)?777\b")),
)

PRODUCTION_IMPACT_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    ("migration", re.compile(r"(?i)\b(alembic|django\.db\.migrations|flyway|liquibase)\b")),
    (
        "production_env",
        re.compile(r"(?i)\b(NODE_ENV|ENV|ENVIRONMENT)\b\s*[:=]\s*['\"]?prod(uction)?['\"]?"),
    ),
    ("deploy_keyword", re.compile(r"(?i)\b(kubectl\s+apply|terraform\s+apply|helm\s+upgrade)\b")),
    ("schema_change", re.compile(r"(?i)\b(ALTER\s+TABLE|CREATE\s+TABLE|DROP\s+COLUMN)\b")),
)

ROLLBACK_HINT_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"(?i)\balembic\b"),
    re.compile(r"(?i)\bmigration(s)?\b"),
    re.compile(r"(?i)\brollback\b"),
    re.compile(r"(?i)\brevert\b"),
)

_BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".gz",
    ".whl",
    ".so",
    ".dylib",
}


@dataclass(frozen=True)
class Finding:
    """Describe one immutable finding produced by a safety scan."""

    category: str
    severity: str  # high | medium | low | info
    label: str
    detail: str
    path: str | None = None
    line: int | None = None


def _line_at(text: str, index: int) -> int:
    """1-based line number for a character offset into *text*."""
    return text.count("\n", 0, index) + 1


def _read_text_file(path: Path, max_bytes: int = 200_000) -> str:
    """Read file text. Propagates OSError so scan failures are not silent."""
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def collect_scan_corpus(path: str | None = None, cwd: Path | None = None) -> tuple[str, str]:
    """Return (corpus_text, source_description).

    source prefixes:
      - ``file:`` / ``dir:`` / ``git ...`` / ``empty-corpus`` — success paths
      - ``missing:`` — path does not exist
      - ``error:read:`` — path exists but could not be read (permission/IO)
    """
    root = (cwd or Path.cwd()).resolve()

    if path:
        target = Path(path)
        if not target.is_absolute():
            target = (root / target).resolve()
        if target.is_file():
            try:
                return _read_text_file(target), f"file:{target}"
            except OSError:
                return "", f"error:read:{target}"
        if target.is_dir():
            chunks: list[str] = []
            count = 0
            for file_path in sorted(target.rglob("*")):
                if not file_path.is_file():
                    continue
                if any(part.startswith(".git") for part in file_path.parts):
                    continue
                if file_path.suffix.lower() in _BINARY_SUFFIXES:
                    continue
                try:
                    chunks.append(_read_text_file(file_path))
                except OSError:
                    return "", f"error:read:{file_path}"
                count += 1
                if count >= 40:
                    break
            return "\n".join(chunks), f"dir:{target} ({count} files)"
        return "", f"missing:{target}"

    # Default: prefer unstaged+staged git diff, fall back to working tree snapshot.
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(root),
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout, "git diff HEAD"
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(root),
            check=False,
        )
        if status.returncode == 0:
            return status.stdout or "", "git status (no diff against HEAD)"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return "", "empty-corpus"


def scan_text(text: str, *, path: str | None = None) -> list[Finding]:
    """Scan *text* for early-warning patterns.

    When *path* is provided it is attached to each finding. Line numbers are
    always set for pattern matches (1-based). Empty input yields a single
    info finding without a line.
    """
    findings: list[Finding] = []
    if not text:
        findings.append(
            Finding(
                category="corpus",
                severity="info",
                label="empty_input",
                detail="No file content or git diff available to scan",
                path=path,
                line=None,
            )
        )
        return findings

    for label, pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(
                Finding(
                    category="secret",
                    severity="high",
                    label=label,
                    detail="Possible credential or secret material matched",
                    path=path,
                    line=_line_at(text, match.start()),
                )
            )

    for label, pattern in DANGEROUS_COMMAND_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(
                Finding(
                    category="dangerous_command",
                    severity="high",
                    label=label,
                    detail="Destructive or high-risk command pattern matched",
                    path=path,
                    line=_line_at(text, match.start()),
                )
            )

    for label, pattern in PRODUCTION_IMPACT_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(
                Finding(
                    category="production_impact",
                    severity="medium",
                    label=label,
                    detail="Production/schema/deploy impact pattern matched",
                    path=path,
                    line=_line_at(text, match.start()),
                )
            )

    return findings


def assess_rollback_signal(text: str, *, path: str | None = None) -> Finding:
    """Return a finding that describes whether rollback wording is present."""
    if any(p.search(text) for p in ROLLBACK_HINT_PATTERNS):
        return Finding(
            category="rollback",
            severity="info",
            label="rollback_hint_present",
            detail="Migration/rollback wording found (not proof of safe rollback)",
            path=path,
            line=None,
        )
    return Finding(
        category="rollback",
        severity="low",
        label="rollback_hint_missing",
        detail="No explicit rollback/migration hint found in scan corpus",
        path=path,
        line=None,
    )


def risk_score(findings: Iterable[Finding]) -> int:
    """Calculate the capped early-warning risk score for scan findings."""
    score = 0
    for finding in findings:
        if finding.severity == "high":
            score += 40
        elif finding.severity == "medium":
            score += 15
        elif finding.severity == "low":
            score += 5
    return min(score, 100)


def summarize_checks(findings: list[Finding], strict: bool = False) -> list[tuple[str, str, str]]:
    """Return display rows: (name, status_icon, color).

    *strict* is retained for call-site compatibility; empty production impact
    is always shown as OK so non-strict mode no longer invents a caution icon.
    """
    del strict  # display contract is mode-independent for empty rows
    secrets = [f for f in findings if f.category == "secret"]
    dangerous = [f for f in findings if f.category == "dangerous_command"]
    production = [f for f in findings if f.category == "production_impact"]
    rollback = [f for f in findings if f.category == "rollback"]

    def status(items: list[Finding], empty_ok: str = "✅") -> tuple[str, str]:
        """Return the display icon and color for a group of findings."""
        if not items:
            return empty_ok, "green"
        worst = max(items, key=lambda f: {"high": 3, "medium": 2, "low": 1, "info": 0}[f.severity])
        if worst.severity == "high":
            return "❌", "red"
        if worst.severity == "medium":
            return "⚠️", "yellow"
        return "⚠️", "yellow"

    secret_icon, secret_color = status(secrets)
    danger_icon, danger_color = status(dangerous)
    prod_icon, prod_color = status(production, empty_ok="✅")

    rollback_icon, rollback_color = "✅", "green"
    if rollback and rollback[0].label == "rollback_hint_missing" and production:
        rollback_icon, rollback_color = "⚠️", "yellow"

    return [
        ("Secrets exposure", secret_icon, secret_color),
        ("Dangerous commands", danger_icon, danger_color),
        ("Production impact", prod_icon, prod_color),
        ("Rollback signal", rollback_icon, rollback_color),
    ]


def _run_external_scanner(
    tool: str, cwd: Path, path: str | None = None
) -> tuple[list[Finding], str]:
    """Run gitleaks or trufflehog as an external secret scanner.

    Returns (findings, source_description). On tool-not-found or execution
    failure, returns ([], "error:<detail>").
    """
    import shutil

    tool_map = {
        "gitleaks": {
            "binary": "gitleaks",
            "scan_args": ["detect", "--source", ".", "--no-banner", "--format", "json", "--no-git"],
        },
        "trufflehog": {
            "binary": "trufflehog",
            "scan_args": ["git", "file://.", "--json", "--no-update"],
        },
    }

    config = tool_map.get(tool)
    if not config:
        return [], f"error:unknown scanner '{tool}' (use gitleaks or trufflehog)"

    binary = shutil.which(config["binary"])
    if not binary:
        return [], f"error:{config['binary']} not installed (brew install {config['binary']})"

    scan_cmd = [binary] + config["scan_args"]
    if path:
        if tool == "trufflehog":
            scan_cmd = [binary, "git", f"file://{path}", "--json", "--no-update"]
        else:
            scan_cmd = [binary, "detect", "--source", str(path), "--no-banner", "--format", "json", "--no-git"]

    try:
        result = subprocess.run(
            scan_cmd, capture_output=True, text=True, timeout=120, cwd=str(cwd),
        )
    except subprocess.TimeoutExpired:
        return [], f"error:{tool} scan timed out (>120s)"
    except OSError as e:
        return [], f"error:{tool} execution failed: {e}"

    findings: list[Finding] = []
    source = f"{tool}:scan"
    raw = result.stdout.strip()

    if not raw:
        findings.append(Finding(
            category="external_scan", severity="info",
            label=f"{tool}_clean", detail=f"{tool} found no secrets",
            path=None, line=None,
        ))
        return findings, source

    import json as _json
    try:
        items = _json.loads(raw) if raw.startswith("[") else [_json.loads(line) for line in raw.splitlines() if line.strip()]
    except _json.JSONDecodeError:
        findings.append(Finding(
            category="external_scan", severity="info",
            label=f"{tool}_output", detail=f"{tool} produced non-JSON output ({len(raw)} bytes)",
            path=None, line=None,
        ))
        return findings, source

    for item in items:
        desc = item.get("Description") or item.get("DetectorName") or item.get("Reason", "secret detected")
        file_path = item.get("File") or item.get("SourceMetadata", {}).get("data", {}).get("filesystem", {}).get("file", "")
        line_num = item.get("StartLine") or item.get("SourceMetadata", {}).get("data", {}).get("filesystem", {}).get("line")
        findings.append(Finding(
            category="external_scan", severity="high",
            label=f"{tool}_finding", detail=f"{tool}: {desc}",
            path=file_path if file_path else None,
            line=line_num if isinstance(line_num, int) else None,
        ))

    return findings, source


def _scan_directory(target: Path, max_files: int = 40) -> tuple[list[Finding], str, str]:
    """Per-file scan for directories (path attached). Caps at *max_files* files."""
    findings: list[Finding] = []
    chunks: list[str] = []
    count = 0
    for file_path in sorted(target.rglob("*")):
        if not file_path.is_file():
            continue
        if any(part.startswith(".git") for part in file_path.parts):
            continue
        if file_path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            text = _read_text_file(file_path)
        except OSError:
            return [], "", f"error:read:{file_path}"
        findings.extend(scan_text(text, path=str(file_path)))
        chunks.append(text)
        count += 1
        if count >= max_files:
            break
    corpus = "\n".join(chunks)
    findings.append(assess_rollback_signal(corpus))
    source = f"dir:{target} ({count} files)"
    return findings, corpus, source


def run_safety_scan(
    path: str | None = None,
    strict: bool = False,
    cwd: Path | None = None,
    max_files: int = 40,
    scan_tool: str | None = None,
) -> dict:
    """Scan a target and return findings, display rows, and risk metadata."""
    root = (cwd or Path.cwd()).resolve()
    findings: list[Finding]
    source: str

    # External scanner integration (gitleaks/trufflehog)
    if scan_tool:
        ext_findings, ext_source = _run_external_scanner(scan_tool, root, path)
        if ext_findings or ext_source.startswith("error:"):
            score = risk_score(ext_findings)
            rows = summarize_checks(ext_findings, strict=strict)
            if score >= 31:
                level = "high"
                action = "Review required — do not proceed without human approval"
            elif score >= 11:
                level = "caution"
                action = "Caution — explicit human review before any proceed decision"
            else:
                level = "low"
                action = "Low early-warning risk — final approval remains human"
            return {
                "source": ext_source,
                "findings": ext_findings,
                "rows": rows,
                "risk_score": score,
                "level": level,
                "action": action,
            }

    if path:
        target = Path(path)
        if not target.is_absolute():
            target = (root / target).resolve()
        if target.is_file():
            try:
                text = _read_text_file(target)
            except OSError:
                findings = []
                source = f"error:read:{target}"
            else:
                findings = scan_text(text, path=str(target))
                findings.append(assess_rollback_signal(text, path=str(target)))
                source = f"file:{target}"
        elif target.is_dir():
            findings, _corpus, source = _scan_directory(target, max_files=max_files)
        else:
            findings = []
            source = f"missing:{target}"
    else:
        corpus, source = collect_scan_corpus(path=None, cwd=root)
        findings = scan_text(corpus)
        findings.append(assess_rollback_signal(corpus))

    score = risk_score(findings)
    rows = summarize_checks(findings, strict=strict)
    if score >= 31:
        level = "high"
        action = "Review required — do not proceed without human approval"
    elif score >= 11:
        level = "caution"
        action = "Caution — explicit human review before any proceed decision"
    else:
        level = "low"
        action = "Low early-warning risk — final approval remains human"
    return {
        "source": source,
        "findings": findings,
        "rows": rows,
        "risk_score": score,
        "level": level,
        "action": action,
    }
