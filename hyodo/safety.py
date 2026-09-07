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


def collect_scan_corpus(
    path: str | None = None,
    cwd: Path | None = None,
    *,
    coverage: dict[str, int] | None = None,
) -> tuple[str, str]:
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
            if coverage is not None:
                sections = re.split(r"(?m)^diff --git ", result.stdout)[1:]
                coverage.update(
                    total=len(sections),
                    scanned=sum(bool(re.search(r"(?m)^@@ ", section)) for section in sections),
                )
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
            bodies, read_count = _read_working_tree_files(root, listing, coverage=coverage)
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


def _read_working_tree_files(
    root: Path, listing: str, *, coverage: dict[str, int] | None = None
) -> tuple[str, int]:
    """Read the contents of files named in *listing*. Returns ``(text, files_read)``.

    ``git diff HEAD`` is empty exactly when the only changes are untracked files, so
    without this the default corpus saw ``?? .env.local`` and never the key inside it —
    the most dangerous case got the shallowest look.
    """
    chunks: list[str] = []
    count = 0
    resolved_root = root.resolve()
    total = 0
    for entry in _porcelain_paths(listing):
        candidate = (root / entry).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            continue  # never follow a path out of the workspace
        # git collapses a wholly untracked directory into one "?? dir/" line, so
        # expanding it is what reaches the files inside a newly created folder.
        targets = sorted(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for target in targets:
            if target.is_dir():
                continue
            total += 1
            if count >= _DEFAULT_SCAN_CAP:
                continue
            if not is_scannable_file(target):
                continue
            try:
                chunks.append(_read_text_file(target))
            except OSError:
                continue
            count += 1
    if coverage is not None:
        coverage.update(scanned=count, total=total)
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
            # gitleaks 8.x has no `--format` flag; the report is emitted with
            # `--report-format`/`--report-path` (`-` streams the report to stdout).
            "version_args": ["version"],
        },
        "trufflehog": {
            "binary": "trufflehog",
            # trufflehog prints its version on stdout or stderr depending on
            # release; the shared positive-control check below accepts either.
            "version_args": ["--version"],
        },
    }

    config = tool_map.get(tool)
    if not config:
        return [], f"error:unknown scanner '{tool}' (use gitleaks or trufflehog)"

    binary = shutil.which(config["binary"])
    if not binary:
        return [], f"error:{config['binary']} {NOT_INSTALLED} (brew install {config['binary']})"

    source_target = str(path) if path else "."
    if tool == "gitleaks":
        scan_cmd = [
            binary,
            "detect",
            "--source",
            source_target,
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            "-",
            "--no-git",
        ]
    else:
        scan_cmd = [binary, "git", f"file://{source_target}", "--json", "--no-update"]

    version_suffix = ""
    version_args = config.get("version_args")
    if version_args:
        version_error: str | None = None
        version_output = ""
        try:
            version_result = subprocess.run(
                [binary, *version_args],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(cwd),
            )
        except subprocess.TimeoutExpired:
            version_error = f"{tool} version check timed out (>10s)"
        except OSError as e:
            version_error = f"{tool} version check failed to execute: {e}"
        else:
            version_output = version_result.stdout.strip() or version_result.stderr.strip()
            if version_result.returncode != 0 or not version_output:
                version_error = (
                    f"{tool} did not answer 'version' (exit {version_result.returncode}, no output)"
                )
            elif not re.search(r"\d+\.\d+", version_output):
                # A binary can exit 0 with *some* output (a usage banner, an
                # "unknown flag" message) without actually reporting a version.
                # Require something that looks like a version number (digits
                # and dots) so that case is still caught as a failed control.
                version_error = (
                    f"{tool} version check produced no version-looking output: {version_output!r}"
                )

        if version_error is not None:
            return [
                Finding(
                    category="external_scan",
                    severity="high",
                    label=f"{tool}_failed",
                    detail=(
                        f"{tool} positive control failed: {version_error} — "
                        "binary present but not usable, scan not attempted"
                    ),
                    path=None,
                    line=None,
                )
            ], f"error:{version_error}"
        version_suffix = f" ({version_output})"

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
    source = f"{tool}:scan{version_suffix}"
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
) -> tuple[list[Finding], str, str, int, int, int]:
    """Per-file scan for directories (path attached).

    Caps at *max_files* files; ``max_files <= 0`` means unlimited.

    Also reports how many corpus files exist under *target*, including skipped
    binaries and unreadable files, not just how many were read — "unobserved is never green" means a partial
    scan must say so, not just state the cap that produced it. Counting the
    full list costs a directory walk plus the binary sniff already required
    by ``is_scannable_file``; it never reads a file's full body.
    """
    corpus_paths = [
        p
        for p in sorted(target.rglob("*"))
        if p.is_file()
        and not any(part.startswith(".git") or part in _SKIPPED_DIR_NAMES for part in p.parts)
    ]
    scannable_paths = [p for p in corpus_paths if is_scannable_file(p)]
    total_scannable = len(corpus_paths)
    scan_targets = scannable_paths if max_files <= 0 else scannable_paths[:max_files]

    findings: list[Finding] = []
    chunks: list[str] = []
    count = 0
    suppressed_count = 0
    for file_path in scan_targets:
        try:
            text = _read_text_file(file_path)
        except OSError:
            return (
                findings,
                "\n".join(chunks),
                f"error:read:{file_path}",
                suppressed_count,
                count,
                total_scannable,
            )
        scanned, suppressed = _apply_safety_exceptions(
            scan_text(text, path=str(file_path)), root, config
        )
        findings.extend(scanned)
        suppressed_count += suppressed
        chunks.append(text)
        count += 1
    corpus = "\n".join(chunks)
    findings.append(assess_rollback_signal(corpus))
    source = f"dir:{target} ({count} files)"
    return findings, corpus, source, suppressed_count, count, total_scannable


def _risk_level_action(score: int) -> tuple[str, str]:
    """Map a risk score to its (level, action) verdict — single source of truth."""
    if score >= 31:
        return "high", "Review required — do not proceed without human approval"
    if score >= 11:
        return "caution", "Caution — explicit human review before any proceed decision"
    return "low", "Low early-warning risk — final approval remains human"


#: Valid values for the ``scope`` payload field — named at the point where the
#: corpus is chosen, never inferred later from the free-text ``source`` string.
SCAN_SCOPES = frozenset({"diff", "status", "file", "directory", "external", "none"})


def _classify_coverage(
    scanned_files: int | None, total_scannable: int | None, *, errored: bool
) -> str:
    """Return ``FULL`` / ``PARTIAL`` / ``UNOBSERVED`` for a non-external scope.

    ``errored`` covers a missing, unreadable, or otherwise failed corpus.
    ``FULL`` requires both counts known, equal, and greater than zero — an
    empty corpus (0/0) is not proof of complete coverage, it is nothing
    observed at all.
    """
    if errored or scanned_files is None or total_scannable is None:
        return "UNOBSERVED"
    if total_scannable > 0 and scanned_files == total_scannable:
        return "FULL"
    if scanned_files < total_scannable:
        return "PARTIAL"
    return "UNOBSERVED"


def _result_payload(
    source: str,
    findings: list[Finding],
    strict: bool,
    exceptions_applied: int = 0,
    scanned_files: int | None = None,
    total_scannable: int | None = None,
    *,
    scope: str,
) -> dict:
    """Assemble the scan result dict from findings — single source of truth.

    Counts describe observed files versus the selected corpus, including skipped
    binaries and unreadable files in the total. External scanners and unavailable
    corpora leave coverage unknown because no file inventory is reported.

    ``scope`` names which corpus this scan looked at (see ``SCAN_SCOPES``); the
    caller sets it explicitly at the point the corpus was chosen, so readers
    never have to infer it from parsing ``source``. ``coverage`` is derived
    from ``scope`` plus the observed/total counts (or, for ``external``,
    from whether the scanner ran).
    """
    score = risk_score(findings)
    level, action = _risk_level_action(score)
    errored = source.startswith(("error:", "missing:"))
    if scope == "external":
        coverage = "UNOBSERVED" if source.startswith("error:") else "FULL"
    else:
        coverage = _classify_coverage(scanned_files, total_scannable, errored=errored)
    return {
        "source": source,
        "scope": scope,
        "coverage": coverage,
        "findings": findings,
        "rows": summarize_checks(findings, strict=strict),
        "risk_score": score,
        "level": level,
        "action": action,
        "exceptions_applied": exceptions_applied,
        "scanned_files": scanned_files,
        "total_scannable": total_scannable,
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
            "error:external scanners unavailable (" + "; ".join(errors) + ")",
            merged,
            strict,
            scope="external",
        )
    label = "+".join(sources) + f" ({len(merged)} findings)"
    if errors:
        label += " [partial: " + "; ".join(errors) + "]"
    return _result_payload(label, merged, strict, scope="external")


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
        return _result_payload(ext_source, ext_findings, strict, scope="external")

    try:
        exceptions = load_scan_exceptions(root)
    except ScanExceptionsConfigError as exc:
        return _result_payload(f"error:scan-exceptions:{exc}", [], strict, scope="none")

    exceptions_applied = 0
    scanned_files: int | None = None
    total_scannable: int | None = None
    scope: str

    if path:
        target = Path(path)
        if not target.is_absolute():
            target = (root / target).resolve()
        if target.is_file():
            scope = "file"
            scanned_files, total_scannable = 0, 1
            try:
                if target.suffix.lower() in _BINARY_SUFFIXES or _looks_binary(target):
                    return _result_payload(
                        f"file:{target}",
                        [],
                        strict,
                        scanned_files=0,
                        total_scannable=1,
                        scope="file",
                    )
                text = _read_text_file(target)
            except OSError:
                findings = []
                source = f"error:read:{target}"
            else:
                scanned_files = 1
                findings, exceptions_applied = _apply_safety_exceptions(
                    scan_text(text, path=str(target)), root, exceptions
                )
                findings.append(assess_rollback_signal(text, path=str(target)))
                source = f"file:{target}"
        elif target.is_dir():
            scope = "directory"
            (
                findings,
                _corpus,
                source,
                exceptions_applied,
                scanned_files,
                total_scannable,
            ) = _scan_directory(target, root, exceptions, max_files=max_files)
        else:
            scope = "none"
            findings = []
            source = f"missing:{target}"
    else:
        coverage: dict[str, int] = {}
        corpus, source = collect_scan_corpus(path=None, cwd=root, coverage=coverage)
        scanned_files = coverage.get("scanned")
        total_scannable = coverage.get("total")
        if source.startswith("git diff"):
            scope = "diff"
        elif source.startswith("git status"):
            scope = "status"
        else:
            scope = "none"
        findings = scan_text(corpus)
        findings.append(assess_rollback_signal(corpus))

    return _result_payload(
        source,
        findings,
        strict,
        exceptions_applied,
        scanned_files=scanned_files,
        total_scannable=total_scannable,
        scope=scope,
    )
