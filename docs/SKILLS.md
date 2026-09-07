# Skill lens (`hyodo skills`)

A skill is not shown to the end user as a menu. HyoDo ingests it, compiles
its rules into deterministic mechanical checks where possible, and reports
per-pillar coverage with full provenance. There is no model, no RAG, no
embeddings, and no chunk/vector store anywhere in this feature — everything
is pure stdlib and re-derived live from the source file each time you run
`lens` or `propose`.

## What a lens is

`hyodo skills ingest` records a skill source (a local path or a URL) and,
once policy clears, compiles its rules into `.hyodo/skills/manifest.json`
(schema `hyodo.skills-manifest/v1`). `hyodo skills lens` re-parses every
ingested source live and reports, per pillar, an integer
`observed / expected` coverage count and a `passed / observed` coherence
count — never a percentage, never a probability. `hyodo skills propose`
renders a tailored custom skill made of the rules that currently pass.

## Skill file format

A skill is a Markdown file. Rules are the `- ` bullets under the first
`## Rules` heading (case-insensitive). If the file has no such heading,
every top-level `- ` bullet in the file is a rule. Everything else —
headings, prose, code fences — is ignored.

## Rule id

`<skill-name>:<slug>`, where `skill-name` is the file's parent directory
name for a `SKILL.md`, or the file stem otherwise, and `slug` is the rule
text lowercased, with non-alphanumeric runs collapsed to a single `-`,
trimmed, and capped at 48 characters (any trailing `[pillars: ...]` tag is
removed before slugging). This is fully deterministic — no model is ever
involved in producing a rule id.

## Pillar mapping

A rule may end with an explicit tag, e.g. `[pillars: truth, goodness]`
(any subset of `truth`/`goodness`/`beauty`/`benevolence`/`hyo`/`eternity`).
Without a tag, HyoDo maps the rule text by keyword:

| Pillar | Keywords |
| --- | --- |
| Truth | test, verify, assert, coverage |
| Goodness | secret, security, safe, credential, injection |
| Beauty | doc, readme, ui, clarity, naming |
| Benevolence | onboarding, developer experience, dx, setup |
| Hyo | convention, context, project rule, style guide |
| Eternity | dependency, maintenance, deprecat, upgrade, lockfile |

A rule may hit several pillars. A rule that hits none — no tag, no keyword
match — still compiles (or is listed `UNOBSERVED`); it appears in the lens's
seventh row, `unclassified` (same `expected`/`observed`/`passed`/`provenance`
shape as a pillar row, and the `"unclassified"` key in `skills lens --json`),
so every compiled rule stays visible somewhere instead of silently
disappearing from the six-pillar count.

## The four mechanical prefixes

Only these four rule-text prefixes compile into a mechanical, executed
check. Anything else is advisory: excluded from the pillar score and
listed under `unobserved` with a `rule_text_digest` (a digest of the rule
text, never the text itself in that list).

- `require file: <relative path>` — PASS if the file exists under root.
- `forbid pattern: <python regex>` — PASS if no git-tracked text file
  matches (binary/undecodable tracked files are skipped, not scanned).
- `require pattern: <python regex>` — PASS if at least one tracked text
  file matches.
- `ruff: <CODE>` — PASS if `ruff check --select <CODE> hyodo/` exits 0. If
  `ruff` itself is not on `PATH`, the rule is `UNOBSERVED` with reason
  `ruff_unavailable` — never `FAIL`.

## Evaluation order and trust

Ingesting a skill is an external variable exactly like a web fetch, not an
opt-in a project has to configure first — `skill_ingest:<source>` is added
to `external_variables` unconditionally. Trust level 2 never softens a
`skill_ingest:*` decision to `ALLOW` (a skill's rules can drive checks
against every future run, so it stays as conservative as an unlisted web
domain); only trust level 3 (full delegation) does. See
`docs/POLICY_TRUST.md` for the trust ladder itself.

## Exit codes

| Command | ALLOW | DENY | UNOBSERVED | ASK |
| --- | --- | --- | --- | --- |
| `skills ingest` | 0 | 1 | 2 | 3 |
| `skills lens` | 0 (report only) | n/a | 2 (manifest malformed) | n/a |
| `skills propose` | 0 | n/a | n/a | n/a |

An `ASK` from `ingest` writes nothing to the manifest; re-run with `--yes`
(records a `human_response`-shaped approval event, then proceeds) or after
granting trust level 3. `lens` treats a missing manifest (nothing ingested
yet) as an honest `0/0` everywhere, not an error; only a malformed
`manifest.json` is `UNOBSERVED` (exit 2), reported on stderr and as
`"manifest_status": "malformed"` in `--json` output. `propose` never calls
`evaluate_policy` — nothing external is contacted at proposal time, only
sources already judged at ingest time — so a malformed manifest there is
still exit 0, with empty `## Rules`/`## Unverified`/`## Provenance`
sections.

## What is never stored or fetched

- A `url:` source is **never fetched over the network** in this package —
  only its domain is recorded, with `content_digest: null` and
  `status: "unreadable"`. Fetching a skill's body from a URL is a later
  package.
- A skill's raw body is never stored by default. `--store-body` on
  `ingest` opts in and writes it to
  `.hyodo/skills/bodies/<digest>.md`; the manifest's `body_stored` field
  is `false` unless that flag was passed.
- `hyodo skills propose` never writes a file unless `--accept` is passed,
  and then writes exactly one file, `.hyodo/skills/proposed.md`, and
  records exactly one ledger event.
- An unreadable source (missing file, or any `url:` source) is always
  recorded in the manifest — with `content_digest: null` and
  `status: "unreadable"` — never silently dropped.
