"""Skill lens: consume a project's own Markdown skills as a yardstick.

A skill is not shown to the end user as a menu. HyoDo ingests it, compiles
its rules into deterministic mechanical checks where possible, and reports
per-pillar coverage (``observed / expected``) with full provenance — which
skill, which rule, produced which status. Everything here is pure stdlib,
deterministic, and re-derivable from the ingested source; no model, no RAG,
no embeddings.

Schema: ``hyodo.skills-manifest/v1``
Manifest: ``.hyodo/skills/manifest.json``
Bodies (opt-in only): ``.hyodo/skills/bodies/<digest>.md``
Proposal (opt-in only): ``.hyodo/skills/proposed.md``
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from hyodo.events import content_digest

SKILLS_MANIFEST_SCHEMA = "hyodo.skills-manifest/v1"
MANIFEST_RELATIVE_PATH = Path(".hyodo") / "skills" / "manifest.json"
BODIES_RELATIVE_DIR = Path(".hyodo") / "skills" / "bodies"
PROPOSED_RELATIVE_PATH = Path(".hyodo") / "skills" / "proposed.md"

#: Fixed, deterministic pillar order used everywhere in this module's output.
PILLARS: tuple[str, ...] = ("truth", "goodness", "beauty", "benevolence", "hyo", "eternity")

#: Keyword table used only when a rule carries no ``[pillars: ...]`` tag.
#: A rule may match more than one pillar. A keyword matches only at the start of
#: a word (so ``test`` covers ``tests`` and ``testing`` but ``ui`` never matches
#: the letters inside ``require``), case-insensitively, with the tag stripped.
_PILLAR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "truth": ("test", "verify", "assert", "coverage"),
    "goodness": ("secret", "security", "safe", "credential", "injection"),
    "beauty": ("doc", "readme", "ui", "clarity", "naming"),
    "benevolence": ("onboarding", "developer experience", "dx", "setup"),
    "hyo": ("convention", "context", "project rule", "style guide"),
    "eternity": ("dependency", "maintenance", "deprecat", "upgrade", "lockfile"),
}

#: Word-start anchored forms of :data:`_PILLAR_KEYWORDS`, built once.
_PILLAR_KEYWORD_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    pillar: tuple(re.compile(r"\b" + re.escape(keyword)) for keyword in keywords)
    for pillar, keywords in _PILLAR_KEYWORDS.items()
}

_TAG_RE = re.compile(r"\[pillars:\s*([^\]]*)\]\s*$", re.IGNORECASE)
_RULES_HEADING_RE = re.compile(r"^##\s+rules\s*$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#{1,6}\s")
_BULLET_RE = re.compile(r"^-\s+(.*)$")

_MECHANICAL_PREFIXES = ("require file:", "forbid pattern:", "require pattern:", "ruff:")


@dataclass(frozen=True)
class CompiledCheck:
    """A rule reduced to one of the four mechanical prefixes."""

    kind: str  # "require_file" | "forbid_pattern" | "require_pattern" | "ruff"
    arg: str


@dataclass(frozen=True)
class Rule:
    """One parsed rule bullet from a skill file.

    ``text`` is the rule as written, tag included. ``base_text`` has any
    trailing ``[pillars: ...]`` tag removed and is what feeds both the rule
    id slug and the keyword pillar mapping when no tag is present.
    """

    skill_name: str
    text: str
    base_text: str
    rule_id: str
    pillars: tuple[str, ...]
    compiled: CompiledCheck | None
    rule_text_digest: str | None = field(default=None)

    def __post_init__(self) -> None:
        if self.rule_text_digest is None:
            object.__setattr__(self, "rule_text_digest", content_digest(self.text))


@dataclass(frozen=True)
class RuleStatus:
    """The live evaluation of one compiled rule against a root."""

    rule: Rule
    status: str  # "PASS" | "FAIL" | "UNOBSERVED"
    reason: str


def _slugify(text: str) -> str:
    """Lowercase, replace non-alphanumerics with ``-``, collapse, trim, cap at 48."""
    lowered = text.lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    collapsed = re.sub(r"-+", "-", replaced).strip("-")
    return collapsed[:48].rstrip("-")


def rule_id_for(skill_name: str, base_text: str) -> str:
    """Return ``<skill-name>:<slug>`` — deterministic, no model."""
    return f"{skill_name}:{_slugify(base_text)}"


def strip_pillar_tag(rule_text: str) -> tuple[str, tuple[str, ...] | None]:
    """Split a rule's trailing ``[pillars: ...]`` tag from its base text.

    Returns ``(base_text, tagged_pillars)``; ``tagged_pillars`` is ``None`` when
    no tag is present (keyword mapping applies instead), or a tuple (possibly
    empty) of the pillars named in the tag, filtered to :data:`PILLARS`.
    """
    match = _TAG_RE.search(rule_text)
    if match is None:
        return rule_text.strip(), None
    base = rule_text[: match.start()].rstrip()
    raw_names = [name.strip().lower() for name in match.group(1).split(",")]
    pillars = tuple(name for name in PILLARS if name in raw_names)
    return base, pillars


def infer_pillars(base_text: str) -> tuple[str, ...]:
    """Map rule text to pillars via the keyword table, fixed :data:`PILLARS` order."""
    lowered = base_text.lower()
    matched = []
    for pillar in PILLARS:
        patterns = _PILLAR_KEYWORD_PATTERNS[pillar]
        if any(pattern.search(lowered) for pattern in patterns):
            matched.append(pillar)
    return tuple(matched)


def compile_rule(base_text: str) -> CompiledCheck | None:
    """Reduce rule text to a mechanical check, or ``None`` (advisory)."""
    stripped = base_text.strip()
    for prefix in _MECHANICAL_PREFIXES:
        if stripped.lower().startswith(prefix):
            arg = stripped[len(prefix) :].strip()
            kind = {
                "require file:": "require_file",
                "forbid pattern:": "forbid_pattern",
                "require pattern:": "require_pattern",
                "ruff:": "ruff",
            }[prefix]
            if not arg:
                return None
            return CompiledCheck(kind=kind, arg=arg)
    return None


def skill_name_for(path: Path) -> str:
    """Parent directory name for ``SKILL.md``, else the file stem."""
    if path.name.lower() == "skill.md":
        return path.parent.name
    return path.stem


def parse_skill_text(text: str) -> list[str]:
    """Return raw rule bullet strings per the skill file format ruling.

    Rules are the ``- `` bullets under the first ``## Rules`` heading
    (case-insensitive). If there is no such heading, every top-level ``- ``
    bullet in the file is a rule. Everything else is ignored.
    """
    lines = text.splitlines()
    rules_start: int | None = None
    for index, line in enumerate(lines):
        if _RULES_HEADING_RE.match(line.strip()):
            rules_start = index + 1
            break

    bullets: list[str] = []
    if rules_start is not None:
        for line in lines[rules_start:]:
            if _HEADING_RE.match(line):
                break
            match = _BULLET_RE.match(line)
            if match:
                bullets.append(match.group(1).strip())
        return bullets

    for line in lines:
        match = _BULLET_RE.match(line)
        if match:
            bullets.append(match.group(1).strip())
    return bullets


def parse_skill_rules(skill_name: str, text: str) -> list[Rule]:
    """Parse *text* into fully classified :class:`Rule` objects."""
    rules: list[Rule] = []
    for raw in parse_skill_text(text):
        base_text, tagged_pillars = strip_pillar_tag(raw)
        pillars = tagged_pillars if tagged_pillars is not None else infer_pillars(base_text)
        compiled = compile_rule(base_text)
        rules.append(
            Rule(
                skill_name=skill_name,
                text=raw,
                base_text=base_text,
                rule_id=rule_id_for(skill_name, base_text),
                pillars=pillars,
                compiled=compiled,
            )
        )
    return rules


@dataclass(frozen=True)
class ParsedSource:
    """Result of resolving one ``ingest`` source before policy is evaluated."""

    kind: str  # "path" | "url"
    raw_source: str
    manifest_source: str  # "path:<rel>" or "url:<domain>"
    readable: bool
    content: str | None
    content_digest_value: str | None
    resolved_path: Path | None
    domain: str | None


def resolve_source(root: Path, source: str) -> ParsedSource:
    """Classify and (for ``path:``) read *source* without touching policy."""
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        domain = parsed.netloc or "unknown"
        # Package 2-A never fetches url: sources over the network — domain only.
        return ParsedSource(
            kind="url",
            raw_source=source,
            manifest_source=f"url:{domain}",
            readable=False,
            content=None,
            content_digest_value=None,
            resolved_path=None,
            domain=domain,
        )

    candidate = Path(source)
    resolved = candidate if candidate.is_absolute() else root / candidate
    try:
        rel = resolved.resolve().relative_to(root.resolve())
        rel_str = str(rel)
    except ValueError:
        rel_str = source
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError:
        return ParsedSource(
            kind="path",
            raw_source=source,
            manifest_source=f"path:{rel_str}",
            readable=False,
            content=None,
            content_digest_value=None,
            resolved_path=resolved,
            domain=None,
        )
    return ParsedSource(
        kind="path",
        raw_source=source,
        manifest_source=f"path:{rel_str}",
        readable=True,
        content=text,
        content_digest_value=content_digest(text),
        resolved_path=resolved,
        domain=None,
    )


def build_ingest_tool(parsed: ParsedSource) -> dict[str, Any]:
    """Build the ``tool`` block of a ``skills.ingest`` tool_call event."""
    if parsed.kind == "path":
        return {"name": "skills.ingest", "paths": [parsed.raw_source], "urls": []}
    return {"name": "skills.ingest", "paths": [], "urls": [{"domain": parsed.domain}]}


def manifest_entry(
    parsed: ParsedSource,
    rules: list[Rule],
    ingested_at: str | None,
    body_stored: bool,
) -> dict[str, Any]:
    """Build one ``skills[]`` row for ``manifest.json``."""
    compiled_ids = [rule.rule_id for rule in rules if rule.compiled is not None]
    pillars: list[str] = []
    for rule in rules:
        if rule.compiled is None:
            continue
        for pillar in rule.pillars:
            if pillar not in pillars:
                pillars.append(pillar)
    name = (
        skill_name_for(parsed.resolved_path)
        if parsed.resolved_path
        else (parsed.domain or "unknown")
    )
    return {
        "name": name,
        "source": parsed.manifest_source,
        "content_digest": parsed.content_digest_value,
        "status": "ok" if parsed.readable else "unreadable",
        "pillars": pillars,
        "compiled_rule_ids": compiled_ids,
        "ingested_at": ingested_at,
        "body_stored": body_stored,
    }


def load_manifest(root: Path) -> tuple[dict[str, Any] | None, str]:
    """Load ``manifest.json``. Returns ``(manifest_or_none, status)``.

    ``status`` is one of ``"ok"``, ``"missing"``, ``"malformed"``. A malformed
    manifest is treated as empty by callers, never crashed on.
    """
    path = root / MANIFEST_RELATIVE_PATH
    if not path.exists():
        return None, "missing"
    try:
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, json.JSONDecodeError):
        return None, "malformed"
    if not isinstance(data, dict) or data.get("schema") != SKILLS_MANIFEST_SCHEMA:
        return None, "malformed"
    skills = data.get("skills")
    if not isinstance(skills, list):
        return None, "malformed"
    return data, "ok"


def save_manifest(root: Path, skills: list[dict[str, Any]]) -> None:
    """Write ``manifest.json``, creating parent directories as needed."""
    path = root / MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": SKILLS_MANIFEST_SCHEMA, "skills": skills}
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def store_body(root: Path, digest: str, text: str) -> None:
    """Persist a skill body at ``.hyodo/skills/bodies/<digest>.md`` (opt-in only)."""
    directory = root / BODIES_RELATIVE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{digest}.md").write_text(text, encoding="utf-8")


def _git_tracked_text_files(root: Path) -> list[Path]:
    """Return git-tracked files under *root*, skipping binaries/undecodable ones."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(root),
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    files: list[Path] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        candidate = root / line
        if not candidate.is_file():
            continue
        files.append(candidate)
    return files


def _is_probably_text(path: Path) -> str | None:
    """Return decoded text, or ``None`` if the file looks binary/undecodable."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def evaluate_compiled_rule(rule: Rule, root: Path) -> RuleStatus:
    """Live-evaluate one compiled rule against the current *root*."""
    compiled = rule.compiled
    if compiled is None:
        return RuleStatus(
            rule=rule, status="UNOBSERVED", reason="advisory rule; no mechanical check"
        )

    if compiled.kind == "require_file":
        target = root / compiled.arg
        exists = target.is_file()
        return RuleStatus(
            rule=rule,
            status="PASS" if exists else "FAIL",
            reason=f"{compiled.arg} {'exists' if exists else 'is missing'}",
        )

    if compiled.kind in ("forbid_pattern", "require_pattern"):
        try:
            pattern = re.compile(compiled.arg)
        except re.error as exc:
            return RuleStatus(rule=rule, status="UNOBSERVED", reason=f"invalid regex: {exc}")
        matched_any = False
        for candidate in _git_tracked_text_files(root):
            text = _is_probably_text(candidate)
            if text is None:
                continue
            if pattern.search(text):
                matched_any = True
                break
        if compiled.kind == "forbid_pattern":
            return RuleStatus(
                rule=rule,
                status="FAIL" if matched_any else "PASS",
                reason="pattern found in a tracked file" if matched_any else "pattern not found",
            )
        return RuleStatus(
            rule=rule,
            status="PASS" if matched_any else "FAIL",
            reason="pattern found in a tracked file" if matched_any else "pattern not found",
        )

    if compiled.kind == "ruff":
        try:
            result = subprocess.run(
                ["ruff", "check", "--select", compiled.arg, "hyodo/"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(root),
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return RuleStatus(rule=rule, status="UNOBSERVED", reason="ruff_unavailable")
        return RuleStatus(
            rule=rule,
            status="PASS" if result.returncode == 0 else "FAIL",
            reason="ruff check clean" if result.returncode == 0 else "ruff check reported findings",
        )

    return RuleStatus(rule=rule, status="UNOBSERVED", reason="unknown compiled rule kind")


def _rules_for_manifest_entry(entry: dict[str, Any], root: Path) -> list[Rule]:
    """Re-derive live :class:`Rule` objects for one manifest skill entry.

    Manifest rows store only ids/digests, never full rule text — the source
    is re-parsed live so lens/propose always reflect the current file, not a
    snapshot frozen at ingest time. A ``url:`` source (never fetched in this
    package) or a source that no longer reads yields no rules.
    """
    source = entry.get("source")
    if not isinstance(source, str) or not source.startswith("path:"):
        return []
    rel = source[len("path:") :]
    target = root / rel
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return []
    name = entry.get("name")
    skill_name = name if isinstance(name, str) and name else skill_name_for(target)
    return parse_skill_rules(skill_name, text)


@dataclass(frozen=True)
class PillarLens:
    """One pillar's coverage row for ``hyodo skills lens``."""

    pillar: str
    expected: int
    observed: int
    passed: int
    provenance: list[tuple[str, str, str]]  # (rule_id, skill, status)


#: Pillar key for a compiled rule that carries no ``[pillars: ...]`` tag and
#: matches no entry in :data:`_PILLAR_KEYWORDS` — `infer_pillars` returns an
#: empty tuple for it, so it would otherwise never appear in any lens row.
UNCLASSIFIED_PILLAR = "unclassified"


@dataclass(frozen=True)
class LensResult:
    """Full result of ``hyodo skills lens``."""

    pillars: list[PillarLens]
    #: Same shape as one entry of `pillars`, for compiled rules with no pillar
    #: (see :data:`UNCLASSIFIED_PILLAR`) — kept separate so every compiled rule
    #: is visible in exactly one row: one of the six pillars, or this one.
    unclassified: PillarLens
    unobserved: list[dict[str, Any]]  # {"rule_id", "skill", "rule_text_digest"}
    manifest_status: str  # "ok" | "missing" | "malformed"


def compute_lens(root: Path) -> LensResult:
    """Live-recompute per-pillar coverage/coherence from the manifest + sources."""
    manifest, status = load_manifest(root)
    entries = manifest.get("skills", []) if manifest else []

    by_pillar: dict[str, list[RuleStatus]] = {pillar: [] for pillar in PILLARS}
    unclassified_statuses: list[RuleStatus] = []
    unobserved: list[dict[str, Any]] = []
    seen_rule_ids: set[str] = set()

    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        for rule in _rules_for_manifest_entry(entry, root):
            if rule.rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(rule.rule_id)
            if rule.compiled is None:
                unobserved.append(
                    {
                        "rule_id": rule.rule_id,
                        "skill": rule.skill_name,
                        "rule_text_digest": rule.rule_text_digest,
                    }
                )
                continue
            rule_status = evaluate_compiled_rule(rule, root)
            if rule.pillars:
                for pillar in rule.pillars:
                    by_pillar[pillar].append(rule_status)
            else:
                unclassified_statuses.append(rule_status)

    def _lens_row(pillar_name: str, statuses: list[RuleStatus]) -> PillarLens:
        expected = len(statuses)
        observed_statuses = [s for s in statuses if s.status != "UNOBSERVED"]
        observed = len(observed_statuses)
        passed = sum(1 for s in observed_statuses if s.status == "PASS")
        provenance = [(s.rule.rule_id, s.rule.skill_name, s.status) for s in statuses]
        return PillarLens(
            pillar=pillar_name,
            expected=expected,
            observed=observed,
            passed=passed,
            provenance=provenance,
        )

    pillars = [_lens_row(pillar, by_pillar[pillar]) for pillar in PILLARS]
    unclassified = _lens_row(UNCLASSIFIED_PILLAR, unclassified_statuses)

    return LensResult(
        pillars=pillars,
        unclassified=unclassified,
        unobserved=unobserved,
        manifest_status=status,
    )


@dataclass(frozen=True)
class ProposeResult:
    """Rendered custom skill proposal for ``hyodo skills propose``."""

    markdown: str
    manifest_status: str


def render_proposal(root: Path, project_name: str) -> ProposeResult:
    """Render the Markdown proposal per the propose ruling.

    Includes every compiled rule that currently PASSes (verbatim text, tags
    kept), an ``## Unverified`` section of advisory rules by digest, and a
    ``## Provenance`` section naming source skills + digests.
    """
    manifest, status = load_manifest(root)
    entries = manifest.get("skills", []) if manifest else []

    passed_rules: list[Rule] = []
    unverified: list[Rule] = []
    provenance_lines: list[str] = []
    seen_rule_ids: set[str] = set()

    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        entry_rules = _rules_for_manifest_entry(entry, root)
        for rule in entry_rules:
            if rule.rule_id in seen_rule_ids:
                continue
            seen_rule_ids.add(rule.rule_id)
            if rule.compiled is None:
                unverified.append(rule)
                continue
            rule_status = evaluate_compiled_rule(rule, root)
            if rule_status.status == "PASS":
                passed_rules.append(rule)
        if entry_rules:
            provenance_lines.append(
                f"- {entry.get('name')} (`{entry.get('source')}`, digest "
                f"`{entry.get('content_digest')}`)"
            )

    lines = [f"# {project_name} conventions (proposed by hyodo)", ""]
    lines.append("## Rules")
    if passed_rules:
        for rule in passed_rules:
            lines.append(f"- {rule.text}")
    lines.append("")
    lines.append("## Unverified")
    if unverified:
        for rule in unverified:
            lines.append(f"- {rule.rule_id} (digest `{rule.rule_text_digest}`)")
    lines.append("")
    lines.append("## Provenance")
    if provenance_lines:
        lines.extend(provenance_lines)
    markdown = "\n".join(lines).rstrip("\n") + "\n"
    return ProposeResult(markdown=markdown, manifest_status=status)


def save_proposal(root: Path, markdown: str) -> None:
    """Write the proposal to ``.hyodo/skills/proposed.md`` (opt-in via --accept)."""
    path = root / PROPOSED_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
