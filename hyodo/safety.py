"""Lightweight safety scan helpers for the public HyoDo CLI.

These checks are early-warning signals only. They do not replace secret scanning,
SAST, dependency audit, tests, or human security review.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from hyodo.exceptions import (
    ScanExceptionsConfig,
    ScanExceptionsConfigError,
    load_scan_exceptions,
    safety_exception_reason,
)

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

# Build/test caches: machine-written, never reviewed, and they crowd real
# sources out of the file cap. Matched by directory name so the guard also
# holds outside a git checkout.
_SKIPPED_DIR_NAMES = frozenset(
    {
        ".hypothesis",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
    }
)

# A suffix blocklist can only exclude what it already lists. `.coverage`
# (a SQLite database) has no suffix at all, so it slipped through, was decoded
# with errors="replace", and its internal `CREATE TABLE` text matched the
# schema_change pattern. Sniff content instead, the way git does.
_BINARY_SNIFF_BYTES = 8_000

#: Substring of an ``error:`` source string meaning the scanner binary was never found.
#: Distinguishes "you don't have this tool" (a known gap) from "the tool ran and broke"
#: (an unobserved scan) — the two deserve different severities. Deliberately the same
#: wording humans already read in the message, so there is one string and not two.
NOT_INSTALLED = "not installed"

#: Default ceiling on how many files a corpus sweep reads. Anything past it, in sorted
#: order, is never examined — so the number is a coverage statement, not a detail.
_DEFAULT_SCAN_CAP = 40


def _looks_binary(path: Path, sniff_bytes: int = _BINARY_SNIFF_BYTES) -> bool:
    """Return True when *path* holds binary data (a NUL byte in its head).

    Unreadable files are reported as non-binary so the caller's own OSError
    handling still runs — a read failure must not be silently swallowed here.
    """
    try:
        with path.open("rb") as handle:
            return b"\x00" in handle.read(sniff_bytes)
    except OSError:
        return False


def is_scannable_file(path: Path) -> bool:
    """Single decision point for "does this file belong in the corpus?".

    Both corpus builders call this, so the rule cannot drift between them.

    Deliberately absent: any use of .gitignore. Ignored files are where live
    credentials actually sit (`.env` is the canonical example), so skipping
    them would blind the scanner precisely where it matters most. Narrow by
    content and by build-cache name, never by "git does not track it".
    """
    if not path.is_file():
        return False
    if any(part.startswith(".git") for part in path.parts):
        return False
    if any(part in _SKIPPED_DIR_NAMES for part in path.parts):
        return False
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return False
    return not _looks_binary(path)


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
                if not is_scannable_file(file_path):
                    continue
                try:
                    chunks.append(_read_text_file(file_path))
                except OSError:
                    return "", f"error:read:{file_path}"
                count += 1
                if count >= _DEFAULT_SCAN_CAP:
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
            listing = status.stdout or ""
            bodies, read_count = _read_working_tree_files(root, listing)
            source = "git status (no diff against HEAD)"
            if read_count:
                source += f" + {read_count} working-tree file(s)"
            return listing + ("\n" + bodies if bodies else ""), source
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return "", "empty-corpus"


def _porcelain_paths(listing: str) -> list[str]:
    """Extract the paths from ``git status --porcelain`` output.

    Handles the ``XY path`` shape and the ``XY orig -> new`` rename shape, taking the
    destination for renames since that is the file present on disk.
    """
    paths: list[str] = []
    for line in listing.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:].strip()
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        entry = entry.strip().strip('"')
        if entry:
            paths.append(entry)
    return paths


def _read_working_tree_files(root: Path, listing: str) -> tuple[str, int]:
    """Read the contents of files named in *listing*. Returns ``(text, files_read)``.

    ``git diff HEAD`` is empty exactly when the only changes are untracked files, so
    without this the default corpus saw ``?? .env.local`` and never the key inside it —
    the most dangerous case got the shallowest look.
    """
    chunks: list[str] = []
    count = 0
    resolved_root = root.resolve()
    for entry in _porcelain_paths(listing):
        if count >= _DEFAULT_SCAN_CAP:
            break
        candidate = (root / entry).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            continue  # never follow a path out of the workspace
        # git collapses a wholly untracked directory into one "?? dir/" line, so
        # expanding it is what reaches the files inside a newly created folder.
        targets = sorted(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for target in targets:
            if count >= _DEFAULT_SCAN_CAP:
                break
            if not is_scannable_file(target):
                continue
            try:
                chunks.append(_read_text_file(target))
            except OSError:
                continue
            count += 1
    return "\n".join(chunks), count


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
    external = [f for f in findings if f.category == "external_scan"]

    def status(items: list[Finding], empty_ok: str = "✅") -> tuple[str, str]:
        """Return the display icon and color for a group of findings."""
        if not items:
            return empty_ok, "green"
        worst = max(items, key=lambda f: {"high": 3, "medium": 2, "low": 1, "info": 0}[f.severity])
        if worst.severity == "high":
            return "❌", "red"
        if worst.severity == "medium":
            return "⚠️", "yellow"
        if worst.severity == "info":
            return empty_ok, "green"
        return "⚠️", "yellow"

    secret_icon, secret_color = status(secrets)
    danger_icon, danger_color = status(dangerous)
    prod_icon, prod_color = status(production, empty_ok="✅")

    rollback_icon, rollback_color = "✅", "green"
    if rollback and rollback[0].label == "rollback_hint_missing" and production:
        rollback_icon, rollback_color = "⚠️", "yellow"

    rows = [
        ("Secrets exposure", secret_icon, secret_color),
        ("Dangerous commands", danger_icon, danger_color),
        ("Production impact", prod_icon, prod_color),
        ("Rollback signal", rollback_icon, rollback_color),
    ]
    if external:
        ext_icon, ext_color = status(external)
        rows.append(("External scan", ext_icon, ext_color))
    return rows


def _run_external_scanner(
    tool: str, cwd: Path, path: str | None = None
) -> tuple[list[Finding], str]:
    """Run gitleaks or trufflehog as an external secret scanner.

    Returns (findings, source_description). On tool-not-found or execution
    failure, returns ([], "error:<detail>").

    Note: trufflehog performs live verification (candidate secrets are sent to
    the issuing service's API to test validity). Verified hits are reported as
    high severity; unverified hits as medium (frequent false positives).
    """
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
        return [], f"error:{config['binary']} {NOT_INSTALLED} (brew install {config['binary']})"

    scan_cmd = [binary] + config["scan_args"]
    if path:
        if tool == "trufflehog":
            scan_cmd = [binary, "git", f"file://{path}", "--json", "--no-update"]
        else:
            scan_cmd = [
                binary,
                "detect",
                "--source",
                str(path),
                "--no-banner",
                "--format",
                "json",
                "--no-git",
            ]

    try:
        result = subprocess.run(
            scan_cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(cwd),
        )
    except subprocess.TimeoutExpired:
        return [], f"error:{tool} scan timed out (>120s)"
    except OSError as e:
        return [], f"error:{tool} execution failed: {e}"

    findings: list[Finding] = []
    source = f"{tool}:scan"
    raw = result.stdout.strip()

    if not raw:
        # No output is only "clean" when the process actually succeeded. A scanner that
        # crashed, was killed, or refused to start also prints nothing — reporting that
        # as clean is the exact failure-to-observe-as-healthy trap this tool exists to
        # catch. Severity must be high: --strict only blocks on high.
        if result.returncode != 0:
            findings.append(
                Finding(
                    category="external_scan",
                    severity="high",
                    label=f"{tool}_failed",
                    detail=(
                        f"{tool} exited {result.returncode} with no output — "
                        "scan did not run; this is not a clean result"
                    ),
                    path=None,
                    line=None,
                )
            )
            return findings, f"error:{tool} exited {result.returncode} without output"
        findings.append(
            Finding(
                category="external_scan",
                severity="info",
                label=f"{tool}_clean",
                detail=f"{tool} found no secrets",
                path=None,
                line=None,
            )
        )
        return findings, source

    try:
        if raw.startswith("["):
            items = json.loads(raw)
        else:
            items = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except json.JSONDecodeError:
        # Unparseable output means we do not know what the scanner saw. That is an
        # unobserved scan, not an informational note. Only the byte count is reported —
        # the payload itself may contain the very secrets we are scanning for.
        findings.append(
            Finding(
                category="external_scan",
                severity="high",
                label=f"{tool}_unparseable",
                detail=(
                    f"{tool} produced non-JSON output ({len(raw)} bytes, "
                    f"exit {result.returncode}) — results could not be read"
                ),
                path=None,
                line=None,
            )
        )
        return findings, f"error:{tool} output could not be parsed"

    for item in items:
        desc = (
            item.get("Description")
            or item.get("DetectorName")
            or item.get("Reason", "secret detected")
        )
        file_path = item.get("File") or item.get("SourceMetadata", {}).get("data", {}).get(
            "filesystem", {}
        ).get("file", "")
        line_num = item.get("StartLine") or item.get("SourceMetadata", {}).get("data", {}).get(
            "filesystem", {}
        ).get("line")
        # trufflehog live-verifies candidates; unverified hits are common false
        # positives, so only verified ones carry high severity.
        severity = "high"
        if tool == "trufflehog" and not item.get("Verified", False):
            severity = "medium"
        findings.append(
            Finding(
                category="external_scan",
                severity=severity,
                label=f"{tool}_finding",
                detail=f"{tool}: {desc}",
                path=file_path if file_path else None,
                line=line_num if isinstance(line_num, int) else None,
            )
        )

    return findings, source


def _apply_safety_exceptions(
    findings: list[Finding], root: Path, config: ScanExceptionsConfig
) -> tuple[list[Finding], int]:
    """Suppress only findings covered by an audited path-and-rule exception."""
    kept: list[Finding] = []
    suppressed = 0
    for finding in findings:
        rule = f"{finding.category}/{finding.label}"
        if safety_exception_reason(finding.path, rule, root, config) is not None:
            suppressed += 1
        else:
            kept.append(finding)
    return kept, suppressed


def _scan_directory(
    target: Path, root: Path, config: ScanExceptionsConfig, max_files: int = 40
) -> tuple[list[Finding], str, str, int]:
    """Per-file scan for directories (path attached).

    Caps at *max_files* files; ``max_files <= 0`` means unlimited.
    """
    findings: list[Finding] = []
    chunks: list[str] = []
    count = 0
    suppressed_count = 0
    for file_path in sorted(target.rglob("*")):
        if not is_scannable_file(file_path):
            continue
        try:
            text = _read_text_file(file_path)
        except OSError:
            return [], "", f"error:read:{file_path}", 0
        scanned, suppressed = _apply_safety_exceptions(
            scan_text(text, path=str(file_path)), root, config
        )
        findings.extend(scanned)
        suppressed_count += suppressed
        chunks.append(text)
        count += 1
        if max_files > 0 and count >= max_files:
            break
    corpus = "\n".join(chunks)
    findings.append(assess_rollback_signal(corpus))
    source = f"dir:{target} ({count} files)"
    return findings, corpus, source, suppressed_count


def _risk_level_action(score: int) -> tuple[str, str]:
    """Map a risk score to its (level, action) verdict — single source of truth."""
    if score >= 31:
        return "high", "Review required — do not proceed without human approval"
    if score >= 11:
        return "caution", "Caution — explicit human review before any proceed decision"
    return "low", "Low early-warning risk — final approval remains human"


def _result_payload(
    source: str, findings: list[Finding], strict: bool, exceptions_applied: int = 0
) -> dict:
    """Assemble the scan result dict from findings — single source of truth."""
    score = risk_score(findings)
    level, action = _risk_level_action(score)
    return {
        "source": source,
        "findings": findings,
        "rows": summarize_checks(findings, strict=strict),
        "risk_score": score,
        "level": level,
        "action": action,
        "exceptions_applied": exceptions_applied,
    }


def _run_merged_external_scan(root: Path, path: str | None, strict: bool) -> dict:
    """Run gitleaks + trufflehog and merge results.

    A scanner that fails to run is surfaced as a medium `*_unavailable` finding
    (failure to observe is never reported as healthy). If neither scanner runs,
    the source is an ``error:`` value so callers treat it as a failed scan.
    """
    merged: list[Finding] = []
    sources: list[str] = []
    errors: list[str] = []
    for tool in ("gitleaks", "trufflehog"):
        tool_findings, tool_source = _run_external_scanner(tool, root, path)
        if tool_source.startswith("error:"):
            errors.append(tool_source)
            # A tool that is simply absent is a known gap, not a broken observation —
            # medium keeps --scan all usable for people who installed only one scanner.
            # A tool that *is* installed and still failed means we ran a scan and cannot
            # trust the outcome, so it must be high or --strict (high-only) sails past it.
            absent = NOT_INSTALLED in tool_source
            merged.append(
                Finding(
                    category="external_scan",
                    severity="medium" if absent else "high",
                    label=f"{tool}_unavailable" if absent else f"{tool}_failed",
                    detail=f"{tool} did not run — {tool_source.removeprefix('error:')}",
                    path=None,
                    line=None,
                )
            )
        else:
            merged.extend(tool_findings)
            sources.append(tool_source)
    if not sources:
        return _result_payload(
            "error:external scanners unavailable (" + "; ".join(errors) + ")", merged, strict
        )
    label = "+".join(sources) + f" ({len(merged)} findings)"
    if errors:
        label += " [partial: " + "; ".join(errors) + "]"
    return _result_payload(label, merged, strict)


def run_safety_scan(
    path: str | None = None,
    strict: bool = False,
    cwd: Path | None = None,
    max_files: int = 40,
    scan_tool: str | None = None,
) -> dict:
    """Scan a target and return findings, display rows, and risk metadata.

    ``scan_tool`` may be ``gitleaks``, ``trufflehog``, or ``all`` (runs both
    and merges findings). ``max_files <= 0`` disables the directory scan cap.
    """
    root = (cwd or Path.cwd()).resolve()
    findings: list[Finding]
    source: str

    # External scanner integration (gitleaks/trufflehog)
    if scan_tool == "all":
        return _run_merged_external_scan(root, path, strict)
    if scan_tool:
        ext_findings, ext_source = _run_external_scanner(scan_tool, root, path)
        return _result_payload(ext_source, ext_findings, strict)

    try:
        exceptions = load_scan_exceptions(root)
    except ScanExceptionsConfigError as exc:
        return _result_payload(f"error:scan-exceptions:{exc}", [], strict)

    exceptions_applied = 0

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
                findings, exceptions_applied = _apply_safety_exceptions(
                    scan_text(text, path=str(target)), root, exceptions
                )
                findings.append(assess_rollback_signal(text, path=str(target)))
                source = f"file:{target}"
        elif target.is_dir():
            findings, _corpus, source, exceptions_applied = _scan_directory(
                target, root, exceptions, max_files=max_files
            )
        else:
            findings = []
            source = f"missing:{target}"
    else:
        corpus, source = collect_scan_corpus(path=None, cwd=root)
        findings = scan_text(corpus)
        findings.append(assess_rollback_signal(corpus))

    return _result_payload(source, findings, strict, exceptions_applied)
