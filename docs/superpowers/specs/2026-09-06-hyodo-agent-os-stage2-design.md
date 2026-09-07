# HyoDo Agent OS — Stage 2 design: lenses, absorption, and ephemeral evidence

## Status

Draft for owner review; nothing here is implemented; depends on Phase 1
packages 1-B through 1-E. Package 1-A (`ASK` decisions and the trust
ladder) is the only Phase 1 package that has shipped, in v4.13.0. Every
citation below to `hyodo/policy.py`, `hyodo/events.py`, `hyodo/gates.py`,
and `hyodo/safety.py` points at code that exists today; every citation to
`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md`
points at design that is written but not yet built, and this document
never restates that design — it links to it.

## Context

HyoDo's public identity is an open-source Agent OS built one honest layer
at a time: Phase 1 gave `evaluate_policy` a real `ASK` outcome and a
trust ladder (`hyodo/policy.py:343-...`, `docs/POLICY_TRUST.md`); the
remaining Phase 1 packages (1-B evidence-graph edges, 1-C the verdict
line, 1-D `connect`, 1-E test integrity) turn the ledger into a real
graph and give an operator a calm, deterministic verdict. Stage 2 is the
layer above that: it teaches HyoDo to *consume* a project's own rules as
a lens (2-A), to absorb a whole environment on arrival the way a field
deployment engineer would (2-B), to give the resulting evidence graph the
structure of a Zettelkasten rather than a flat ledger (2-C), and to
handle visual evidence — a screenshot — as something that must prove its
own destruction, not just its own existence (2-D).

HyoDo does not ship a model, embeddings, retrieval, or vector search
anywhere in this document. Every package below that reasons over
unstructured content — a skill file's prose, a folder's documents, a
captured screen — treats that reasoning as a BYOM ("bring your own
model") external research node. HyoDo's own public surface records only
digests, manifests, decisions, and receipts of what such a node claimed
to do; it never stores the node's raw output as HyoDo's own claim. This
rule is restated once inside each package that touches it (2-B, 2-C,
2-D) because each package is tempted, in a different way, to store more
than a digest.

The honesty rules Phase 1 established are unchanged and binding here:
`probability`/`confidence` never appear as a field
(`hyodo/policy.py:104-106`); an unknown is `UNOBSERVED`, never a silent
`ALLOW`; the decision path stays deterministic and model-free — nothing
in `evaluate_policy` calls out to a model, and Stage 2 does not change
that; the ledger stays digest-only by default (`hyodo/events.py:1-6`);
exit codes stay `ALLOW` 0, `DENY` 1, `UNOBSERVED` 2, `ASK` 3
(`hyodo/events.py:38`); the schema id stays `hyodo.agent-event/v1` with
optional fields only, the same convention `hyodo/policy.py:8-11`
documents for `hyodo.policy/v1`.

### Two axes of caution

Phase 1's trust ladder (0-3, `docs/POLICY_TRUST.md:27-32`) already
decides *what* HyoDo allows without asking. Stage 2 adds a second,
orthogonal reading of the same ladder — not a new level, not a schema
change, an operational lens an operator can use to decide *how* to run
an agent at a given level:

- **Dry run is the time axis.** Judge before acting, zero side effects.
  `hyodo policy check` and `hyodo connect`'s default (dry-run) mode are
  both dry runs today: they report what would happen without doing it.
- **Sandbox is the space axis.** Act inside a boundary — a worktree, a
  containerised harness sandbox — so that even an `ALLOW` can only reach
  as far as the boundary permits.

Mapped onto the shipped ladder: level 0 is dry run only (every event is
`ASK` unless a hard `DENY` fires — nothing proceeds without a human
looking at it first, `docs/POLICY_TRUST.md:13-14,29`); level 1 is the
level at which an operator is expected to have already moved real
execution into a sandbox, because discretionary calls still `ASK` one
at a time but a hard `DENY` is enforced regardless; level 2 is
autonomous execution *inside* the boundary the operator already
configured, paired with the non-optional ledger obligation
(`docs/POLICY_TRUST.md:39-42`); level 3 is autorun with a full ledger
and no assumption of confinement. None of this changes
`evaluate_policy`'s shipped ALLOW/ASK/DENY mechanics — it is a reading
for the operator, not a new rule for the evaluator.

One consequence of taking the space axis seriously: a test that fails
*inside* a sandbox is not evidence the code is broken — it may only be
evidence the sandbox forbade something the code legitimately needed. A
gate that reads a sandboxed failure as `FAIL` risks training operators to
disable the sandbox to get a green run. Stage 2's design principle,
carried forward into any future gate-execution package (none of 2-A
through 2-D implement this themselves), is: a test that fails inside a
sandbox is read as `UNOBSERVED` for the gate, not `FAIL`, and the gate
re-runs it outside the box under a trusted actor before it is allowed to
report a real pass or fail. This is a constraint on future work, named
here because it is part of the same two-axis reasoning, not a package of
its own.

Dry run's on-ramp already exists in the Phase 1-D design:
`hyodo connect --shadow` installs the pre-action hook in a mode that
evaluates and records every decision but always exits 0
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:749-750`).
Shadow mode is level 0's dry run applied to governance itself, and Stage
2 does not redefine it — every dry-run reference in this document points
back at that section.

## Goals

- Turn a skill (a markdown rule file such as `SKILL.md`, `AGENTS.md`, or
  a repository convention file) into a lens HyoDo consumes to raise
  observed coverage and coherence, with per-pillar-percentage provenance,
  never into a menu shown to the user.
- Give `hyodo inspect` a definition of "complete" that is honest by
  construction: coverage is either 100% or every unobserved region is
  explicitly enumerated, never silently dropped.
- Give the evidence graph the *structure* of a Zettelkasten — atomic
  events with ids, parent chains, explicit links, one claim per note,
  pillar clusters, hub views — without importing note bodies, vaults, or
  embeddings into the public package.
- Let HyoDo treat a captured screen as ephemeral evidence: prove it
  existed (exact digest, perceptual hash) and prove it was destroyed
  (a paired destruction event), by default, every time.
- Keep every new surface inside the same four-decision, model-free
  contract Phase 1 already committed to.

## Non-goals

- Stage 2 does not ship RAG, embeddings, vector search, or a model
  anywhere in the public package. Skill sharpening, document absorption,
  and perceptual-hash comparison are all either deterministic AST/regex
  work or explicitly named BYOM boundaries.
- Stage 2 does not implement Phase 1 packages 1-B through 1-E. It
  specifies against their design and, where a feature is unavailable
  without them, says so and describes the fallback.
- Stage 2 does not change any Phase 1 schema id, exit code, or the
  four-way `ALLOW`/`DENY`/`UNOBSERVED`/`ASK` decision vocabulary.
- Stage 2 does not weaken a hard `DENY` at any trust level, and does not
  let a supply-chain-shaped external variable (a skill's source, a
  captured screen) become `ALLOW` at trust level 2 the way an
  already-anticipated path or tool can — see each package's Evaluation
  order for why.
- Stage 2 does not display a skill's body to the end user as a
  selectable item, store chunk or document text by default, or store
  captured pixels by default.

---

## Package 2-A — `feat/skill-lens`: `hyodo skills`

A skill is not shown to the user as a menu. HyoDo consumes it as a lens:
its rules become the yardstick for the six pillars, raising observed
coverage (`observed / expected`) and coherence (what the run claimed
against what the lens actually observed). Every pillar percentage
carries provenance — which skill, which rule, produced it.

### Data model

Pillar mapping (a rule may map to more than one pillar):

| Pillar | Maps to |
| --- | --- |
| Truth | verification and tests |
| Goodness | security and safety |
| Beauty | docs, UI, clarity |
| Benevolence | developer experience and onboarding |
| Hyo | project conventions and context alignment |
| Eternity | maintenance, dependencies, long-term health |

This mapping matches HyoDo's own published pillar table — the "measured
by" table in `README.md:157-164` — so a skill's rules land on the same
six areas the score already reports, rather than inventing a seventh
taxonomy.

`.hyodo/skills/manifest.json`, new schema `hyodo.skills-manifest/v1`:

```json
{
  "schema": "hyodo.skills-manifest/v1",
  "skills": [
    {
      "name": "example-skill",
      "source": "path:skills/example/SKILL.md",
      "content_digest": "a1b2c3d4e5f6",
      "pillars": ["truth", "goodness"],
      "compiled_rule_ids": [
        "example-skill:no-bare-except",
        "example-skill:require-tests"
      ],
      "ingested_at": "evt-0012",
      "body_stored": false
    }
  ]
}
```

`source` is prefixed `path:` or `url:` so a local convention file and a
fetched one are never ambiguous. For a `url:` source only the domain is
recorded, matching the domain-only posture `web_domain_unlisted` already
uses (`hyodo/policy.py:449-454`) — the path and query of a fetched skill
URL are not retained. `content_digest` reuses `content_digest()`
(`hyodo/events.py:66-76`), a 12-hex digest matching `_DIGEST_RE`
(`hyodo/events.py:40`). `body_stored` is `false` unless the operator
passes `--store-body` on `ingest`; no skill body is stored by default,
mirroring the full-body opt-in already established for `io.input_text`/
`io.output_text` (`hyodo/events.py:213-224`). `compiled_rule_ids` are
`<skill-name>:<rule-slug>` strings, deterministic from the skill's own
rule text — never model-generated.

Rules that compile into a mechanical check (a `ruff` rule reference, a
required file, a regex over a diff) are checked and scored. A rule the
compiler cannot reduce to a mechanical check — pure prose advice with no
observable signal — is excluded from the score and listed as
`UNOBSERVED` with a digest of the rule text, never guessed at.

### Config example

No new field is required on `.hyodo/policy.toml` for ingestion itself —
see Evaluation order for why ingestion is unconditionally discretionary,
the same way the built-in web tools are. The trust ladder still governs
whether an `ASK` for a given ingestion softens:

```toml
schema = "hyodo.policy/v1"

# Skill ingestion is always discretionary (see Evaluation order below);
# nothing here turns it off. [trust] only controls whether the operator
# has to answer the ASK each time or has granted full delegation.
[trust]
max_level = 3
```

### CLI surface

```text
hyodo skills ingest <path|url> [--store-body]
hyodo skills lens [--json]
hyodo skills propose [--accept]
```

`ingest` records the source, runs it through `evaluate_policy`, and on a
proceeding decision compiles its rules into the manifest. `lens` prints
(or emits as JSON) the current per-pillar coverage/coherence numbers with
their skill/rule provenance. `propose` prints the tailored custom skill
it would write; `--accept` writes it and records the acceptance.

### Evaluation order

Ingesting a skill is an external variable exactly like a web fetch, not
an opt-in the operator has to configure first. A new module-level set in
`hyodo/policy.py`, alongside `_BUILTIN_WEB_TOOLS`
(`hyodo/policy.py:30`):

```python
_BUILTIN_SUPPLY_CHAIN_TOOLS = frozenset({"skills.ingest"})
```

`evaluate_policy`'s external-variable aggregation step
(`hyodo/policy.py:439-470`) gains one more unconditional line next to the
existing `ask_tools:<name>` line (`hyodo/policy.py:469-470`):

```python
if is_tool_event and tool_name in _BUILTIN_SUPPLY_CHAIN_TOOLS:
    domain = urls[0].get("domain") if urls else None
    source = paths[0] if paths else (domain or "unknown")
    external_variables.append(f"skill_ingest:{source}")
```

This makes `skill_ingest:<source>` populate `external_variables`
regardless of whether `ask_tools` lists `skills.ingest` — the same
unconditional treatment `_BUILTIN_WEB_TOOLS` already gets
(`hyodo/policy.py:469-470` checks `_is_web_classified`, which is true for
any built-in tool with no `[web]` configuration required,
`hyodo/policy.py:257-...`). At the trust gate
(`hyodo/policy.py:492-...`), `skill_ingest:*` is treated the same way
`web_domain_unlisted` is: level 2 never promotes it to `ALLOW` (it is not
a boundary the operator pre-configured, unlike `path_outside_root` or a
named `ask_tools` entry), only level 3 (full delegation) does. This is a
deliberate, conservative choice — a skill's rules can later drive
automated checks against every future run, so widening it at level 2
alongside ordinary tool/path boundaries understates the supply-chain
risk (see Open questions for whether an allowlisted source should ever
change this).

Rule compilation happens after a proceeding decision (`ALLOW` or an
operator-approved `ASK`), never before — HyoDo never evaluates a skill's
rules against a project until the ingestion itself has cleared policy.

### Exit contracts

| Command | `ALLOW` | `DENY` | `UNOBSERVED` | `ASK` |
| --- | --- | --- | --- | --- |
| `skills ingest` | 0 | 1 | 2 | 3 |
| `skills lens` | 0 (report only) | n/a | 2 (manifest unreadable) | n/a |
| `skills propose` | 0 | n/a | n/a | n/a |

`propose` never touches `evaluate_policy` — writing the proposal file is
gated only by `--accept`, not by policy, because nothing external is
being contacted at proposal time; the source skills were already judged
at ingest time.

### Failure modes

- A skill source that cannot be read (missing file, unreachable URL) is
  recorded in the manifest with `content_digest: null` and a
  `status: "unreadable"` marker, never silently dropped from the
  manifest list.
- A malformed `manifest.json` (bad JSON, wrong schema id) is treated as
  empty for `lens`/`propose` purposes and reported, never crashed on —
  the same posture `load_policy_config` takes toward a malformed
  `policy.toml` (`hyodo/policy.py:119-130`-area `PolicyConfigError`).
- A rule that maps to a pillar but produces contradictory signals across
  two ingested skills (one requires a check, another forbids it) is
  listed under both skills' provenance with no attempt to arbitrate —
  arbitration is an operator decision, not a HyoDo judgment call.

### Backward compatibility

- Absent `.hyodo/skills/`, every existing command is unaffected: `check`,
  `score`, and `safe` do not read the skill manifest unless a future
  package explicitly wires pillar provenance into their output (see Open
  questions).
- `_BUILTIN_SUPPLY_CHAIN_TOOLS` is additive; it does not change
  `_BUILTIN_WEB_TOOLS`, `ask_tools`, or any existing `external_variables`
  entry for a tool call that predates this package.
- No existing schema id changes; `hyodo.skills-manifest/v1` is new.

---

## Package 2-B — `feat/inspect`: `hyodo inspect` (field-deployment absorption)

On arrival, HyoDo absorbs a whole environment the way a field deployment
engineer would — a documents folder and/or a repository — into an
inventory whose analysis is complete by definition: either coverage
`observed / expected` is 100%, or every unobserved region is explicitly
enumerated. Every conclusion cites a file digest, a chunk id, or an event
id.

### Data model

`.hyodo/folder-manifest.json`, new schema `hyodo.folder-manifest/v1`:

```json
{
  "schema": "hyodo.folder-manifest/v1",
  "root": "examples/fde-evidence-spine",
  "generated_at": "2026-09-06T12:00:00+00:00",
  "files": [
    {
      "path": "examples/fde-evidence-spine/README.md",
      "digest": "a1b2c3d4e5f6",
      "size": 1834,
      "mtime": "2026-09-06T11:00:00+00:00",
      "ignored": false,
      "ignore_reason": null
    }
  ],
  "unreadable": [],
  "coverage": [3, 3]
}
```

`.hyodo/chunks-manifest.json`, new schema `hyodo.chunks-manifest/v1` —
chunk id, file digest, byte range, chunk digest, **never chunk text**:

```json
{
  "schema": "hyodo.chunks-manifest/v1",
  "chunks": [
    {
      "chunk_id": "c-0001",
      "file_digest": "a1b2c3d4e5f6",
      "byte_range": [0, 1834],
      "chunk_digest": "f6e5d4c3b2a1"
    }
  ]
}
```

Embedding is an external BYOM node's job. HyoDo emits these two
manifests and, when a BYOM node reports back what it indexed, records a
receipt of that claim (source chunk ids, node identifier, timestamp) —
never the vectors themselves and never chunk text.

Directory walking follows `hyodo/safety.py`'s existing exclusions
(`_SKIPPED_DIR_NAMES`, `hyodo/safety.py:86-99`: `.venv`, `node_modules`,
`__pycache__`, `dist`, `build`, and the tool caches) so vendored and
generated content is not absorbed by default, and reuses
`_scan_directory`'s "never crash on an unreadable file" posture
(`hyodo/safety.py:608-641`).

### Config example

No new `.hyodo/policy.toml` field. `hyodo inspect` is a local, read-only
report generator, structurally like `hyodo safe`, not a `tool_call` that
goes through `evaluate_policy` — absorbing a directory the operator
explicitly pointed HyoDo at is not itself an external variable the way
fetching a skill from an unlisted source is (2-A). The distinction: a
skill's rules can later drive automated checks against every future run,
while a folder inventory is a one-shot report the operator already
consented to by running the command.

### CLI surface

```text
hyodo inspect <path> [--ignore <pattern>] [--report md|json]
```

The report includes a coverage line ("`observed`/`expected` files
digested") for both formats. `examples/fde-evidence-spine/` (verified:
`README.md`, `policy.toml`, `sample-tool-call.json` — three small,
non-secret files) is the worked seed: `hyodo inspect
examples/fde-evidence-spine` is the smoke test this package's first test
runs against, without adding new fixture content to that example.

### Evaluation order

1. Run `hyodo safe`'s existing rules over every candidate file before
   anything is chunked. A file `safe` flags as secret-shaped is excluded
   from `chunks-manifest.json` and reported by digest and location only,
   never by value.
2. Walk the tree (respecting `_SKIPPED_DIR_NAMES` and `--ignore`),
   digesting each readable file into `folder-manifest.json`.
3. An unreadable file (permission error, binary the reader chokes on) is
   appended to `unreadable` with a reason string; it still counts toward
   `coverage`'s `expected` total, and its absence from `observed` is
   exactly what makes coverage honestly less than 100% rather than
   silently 100%.
4. Chunk every non-excluded, readable file into `chunks-manifest.json`.

### Exit contracts

| Outcome | Exit |
| --- | --- |
| Manifests written, coverage complete (every file digested or
  explicitly enumerated in `unreadable`) | 0 |
| Given path does not exist or is not a directory | 1 |
| Manifest write failure (`OSError`) | 2 |

There is no `ASK`/exit-3 case: `hyodo inspect` never calls
`evaluate_policy` (see Evaluation order above).

### Failure modes

- An unreadable file is always an `unreadable` entry, never a silent
  skip — this is the same "cannot be checked is never treated as checked
  and clean" principle Phase 1-A already applies to policy boundaries
  (`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:325-331`).
- A symlink whose target resolves outside `<path>` is excluded from both
  manifests and listed under `unreadable` with reason
  `symlink_outside_root`, never silently followed.
- A file that changes between the digest pass and the chunk pass (rare,
  but possible on a live repository) is re-digested for chunking; a
  mismatch between the two digests is reported, not silently resolved by
  picking one.

### Backward compatibility

- `hyodo inspect` is a wholly new command; no existing schema, CLI
  surface, or exit contract changes.
- Nothing is written outside `.hyodo/folder-manifest.json` and
  `.hyodo/chunks-manifest.json`; a checkout that has never run `inspect`
  is unaffected.

---

## Package 2-C — evidence graph structure borrowed from Zettelkasten

HyoDo adopts the *structure* of a Zettelkasten (atomic notes with ids,
parent chains, explicit links, one claim per note, clusters, hub pages),
not the notes themselves.

| Zettelkasten | HyoDo | Where |
| --- | --- | --- |
| fleeting note | agent-event ledger event | public, `.hyodo/agent-events.jsonl` |
| literature note | absorbed document/repository chunk (`chunks-manifest.json`, digest) | public inventory; embedding external |
| permanent note `claim` | decision reason, verdict line, lesson from skill sharpening | public ledger |
| Folgezettel `parent` | `parent_event_id` | public schema (Phase 1-B) |
| `links[]` and backlinks | `evidence_refs` plus a reverse index | public schema (1-B), `hyodo report --format graph` |
| `cluster` | six-pillar classification | public (score provenance) |
| hub / concept page | evidence-graph view and per-pillar index | public dashboard |
| cascade integrity check | fail-closed link validation (missing target = invalid; broken edge rendered) | public, `validate_event_edges` (1-B) |

The public package takes only ids, parents, refs, claims, and clusters;
note bodies, vaults, and embeddings stay in whatever external note system
the operator uses. HyoDo's own evidence pipeline still touches embedding
only through the same BYOM boundary named in 2-B — a literature-note row
above is a chunk digest, never chunk text.

### Data model

Two of this table's rows (`parent_event_id`, `evidence_refs`) are Phase
1-B fields that do not exist in `hyodo/events.py` yet; 2-C's own
additions build on top of them and cannot ship before 1-B does.

New optional artifact, `.hyodo/graph.json`, schema
`hyodo.graph-export/v1` — the bridge an external note system may turn
into permanent notes:

```json
{
  "schema": "hyodo.graph-export/v1",
  "generated_at": "2026-09-06T12:00:00+00:00",
  "nodes": [],
  "edges": [],
  "backlinks": {},
  "clusters": {
    "truth": [], "goodness": [], "beauty": [],
    "benevolence": [], "hyo": [], "eternity": []
  }
}
```

`nodes`/`edges` mirror the shape 1-B's `hyodo report --format graph`
already designs (`hyodo.evidence-graph/v1`,
`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:536-560`).
2-C adds two fields on top of that design, both additive under the same
optional-fields-only convention: `backlinks`, a reverse index keyed by
`event_id` listing every event whose `evidence_refs` cites it (1-B's own
design only lists forward edges); and `clusters`, the same event ids
grouped by the pillar the citing decision's `rule_id`/skill provenance
(2-A) maps to.

### Config example

No new `.hyodo/policy.toml` field. The bridge is opt-in per invocation,
not per-project configuration — see CLI surface.

### CLI surface

```text
hyodo graph export [--out .hyodo/graph.json] [--yes]
```

Default is an interactive confirmation before writing (mirroring
`connect`'s consent pattern, `_is_noninteractive()`,
`hyodo/gates.py:249-...`); `--yes` skips the prompt when a TTY is
present. `hyodo report --format graph` itself (1-B) is unchanged in
shape by 2-C beyond the additive `backlinks` field on its own JSON
output.

### Evaluation order

1. Load the ledger via `read_agent_events` (1-B-compatible;
   `hyodo/events.py:414-...`). On a pre-1-B ledger with no
   `parent_event_id`/`evidence_refs` fields at all, every node is
   edge-less and the export still succeeds — an empty graph is a valid,
   honestly-empty graph, not an error.
2. Where 1-B's `validate_event_edges` exists, defer to its
   already-computed `broken_edges` set; 2-C never re-derives edge
   validity itself.
3. Compute `backlinks` as the reverse of every non-broken `evidence_refs`
   entry.
4. Compute `clusters` from each decision event's `rule_id` and, where
   2-A has run, from the skill/rule provenance that produced the pillar
   percentage the decision cites.
5. Write the export only after the confirmation step above.

### Exit contracts

| Outcome | Exit |
| --- | --- |
| Export written | 0 |
| Confirmation declined without `--yes` | 1 |
| Ledger unreadable or write failure | 2 |

`hyodo report --format graph`'s own exit contract (1-B: 0 clean graph, 1
`broken_edges` non-empty, 2 write failure) is unchanged; the `backlinks`
field 2-C adds to its JSON output never changes which exit code that
command returns.

### Failure modes

- A dangling `evidence_refs` entry cannot exist in a ledger 1-B recorded
  (`validate_event_edges` rejects it at record time), but a
  hand-edited or truncated ledger can still produce one; 2-C's
  `backlinks` computation treats such an entry exactly as 1-B's own
  `broken_edges` does — reported, not silently dropped, and the export
  still succeeds (`broken_edges` is advisory to the export command,
  though it fails `report --format graph` itself per 1-B's contract).
- A claim (decision reason) with no `evidence_refs` at all is reported
  the same way 1-B's `orphaned_decisions` already is — advisory, never a
  failure.

### Backward compatibility

- Every field 2-C adds (`backlinks` on `hyodo.evidence-graph/v1`, the
  whole `hyodo.graph-export/v1` artifact) is new and optional; a ledger
  with none of 1-B's edge fields still produces a valid, empty-edge graph
  and export.
- `graph export` is a new command; it does not change `report`'s
  existing formats.

### Hypothesis: code as Zettelkasten (experiment, not a commitment)

Structural links between code units — imports, calls, test references —
must be generated from the AST, never hand-written; a hand-maintained
link graph rots the moment a refactor moves a call site. What a
Zettelkasten structure adds on top of that is a per-unit *claim*
(an invariant, and why it holds) and permanent notes recording decisions
and lessons. Binding a claim to observed test events through
`evidence_refs` makes "a claim with no evidence is `UNOBSERVED`" an
honest Truth-pillar measure, rather than a documentation convention
nobody checks.

Proposed experiment, to run after 1-B and 1-E land: generate one claim
per function in `hyodo/policy.py`, link each to the test events that
exercise it, and list every claim with zero linked test evidence. The
success criterion is concrete: the experiment should catch the same kind
of gap PR #156 fixed by hand — the trust-level-2 ledger obligation
existed in the Phase 1-A design
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:246-254`)
but was missing from `hyodo/cli/main.py`'s actual output until commit
`9432509` ("fix(policy): surface the ledger obligation at trust level
2+ and document the trust ladder (#156)", verified with
`git log --grep`). If claims-per-function had existed, the missing
obligation should have shown up as an unbacked claim before a human
found it by audit.

---

## Package 2-D — `feat/ephemeral-eye`: ephemeral visual evidence

An external screen-capture tool (BYOM; HyoDo does not ship one) is
invoked under policy as `tool_call` `eye.capture` (`ASK`/`ALLOW` by trust
and external variables). HyoDo never stores pixels. It records an exact
digest and a perceptual hash, shows the capture to the operator with a
visible countdown, deletes the file after a TTL (default 5s), and then
records a second event, `tool_result`, with
`meta.ephemeral.destroyed_at`, proving destruction. Proof of existence
and proof of destruction are a pair.

### Data model

`meta.ephemeral` on the existing optional `meta` object:

```json
{"ttl_s": 5, "phash_algo": "dct64", "phash": "a1b2c3d4e5f60718",
 "destroyed_at": null, "kept": false}
```

`hyodo/events.py`'s current `meta` normalization only recognizes `model`
and `tags` (`hyodo/events.py:262-279`: `meta_out` starts as
`{"model": None, "tags": []}` and no third key is ever read from
`meta_raw`). 2-D extends that block with a third, optional key, following
the same "invalid shape is a validation error, absence is `None`"
pattern the block already uses for `model`:

```python
ephemeral_raw = meta_raw.get("ephemeral")
meta_out["ephemeral"] = None
if ephemeral_raw is not None:
    if not isinstance(ephemeral_raw, dict):
        reasons.append("invalid_field:meta.ephemeral")
    else:
        # ttl_s: non-negative int; phash_algo: the literal "dct64";
        # phash: 16 lowercase hex chars (64 bits);
        # destroyed_at: ISO-8601 string or None; kept: bool.
        ...
```

`phash` is validated against a new constant sized for a 64-bit hash,
alongside the existing 12-hex `_DIGEST_RE` (`hyodo/events.py:40`):

```python
_PHASH_RE = re.compile(r"^[0-9a-f]{16}$")
```

The perceptual hash algorithm is a 64-bit DCT-based pHash (an 8x8 DCT of
a downsampled grayscale image, thresholded against the DCT
coefficients' median — the same construction the common `pHash`/
`imagehash.phash` implementations use). It is deterministic: the same
image byte-for-byte always produces the same 16-hex-character value.
`phash_algo` names the algorithm explicitly; Stage 2 accepts exactly one
value, `dct64`, and validation rejects any other. A later algorithm gets
a new literal, so two captures are comparable only when their
`phash_algo` values match, and `hyodo eye verify` reports
`phash_algo_mismatch` instead of a distance when they differ.

`PolicyConfig` gains one more optional field, following the exact
`WebPolicy`/`TrustPolicy` pattern (`hyodo/policy.py:40-53`):

```python
@dataclass(frozen=True)
class EphemeralPolicy:
    phash_distance_threshold: int = 10  # out of 64 bits; advisory only
```

`ephemeral: EphemeralPolicy | None = None` on `PolicyConfig`
(`hyodo/policy.py:56-73`); absent, `hyodo eye verify` falls back to the
same default. The threshold is never printed as a probability — it
annotates a Hamming-distance comparison, the same way `ask_threshold`
only annotates `--explain` text and never changes a decision
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:356-362`).

### Config example

```toml
schema = "hyodo.policy/v1"

[ephemeral]
# Hamming distance out of 64 bits below which `hyodo eye verify` calls two
# captures "the same screen". Advisory only — never a probability, never a
# decision input.
phash_distance_threshold = 10
```

### CLI surface

```text
hyodo eye capture [--ttl SECONDS] [--keep]
hyodo eye verify --against <event_id> [--phash-threshold N]
```

`capture` defaults `--ttl` to 5 seconds. `--keep` retains the file
instead of deleting it. `verify` re-captures now and reports the Hamming
distance between the fresh phash and the referenced event's stored
`meta.ephemeral.phash` — "same screen" or "different screen" text plus
the raw distance, never a percentage.

### Evaluation order

1. Build a `tool_call` event, `tool.name = "eye.capture"`. Like 2-A's
   `skill_ingest:*`, `eye.capture` joins a new unconditional built-in
   set (`_BUILTIN_SUPPLY_CHAIN_TOOLS` grows to include it, or a sibling
   constant — the mechanism is identical to 2-A's), producing an
   `eye_capture` external variable regardless of `ask_tools`
   configuration. At the trust gate it is treated like
   `web_domain_unlisted`: level 2 never promotes it to `ALLOW`; only
   level 3 (full delegation) does — a captured screen is exactly the
   kind of undeclared boundary level 2's "inside the boundary" carve-out
   was never meant to cover.
2. If the resulting decision proceeds (`ALLOW`, or an operator-approved
   `ASK`) but no external capture tool is configured, the outcome is
   `UNOBSERVED`, `rule_id = "eye_tool_absent"` — not a silent no-op.
3. On a real capture: compute the exact digest (`content_digest()`,
   `hyodo/events.py:66-76`) and the phash from the raw image bytes; the
   bytes themselves never reach the ledger. Record a `tool_result` event
   with `io.output_digest` set to the exact digest and
   `meta.ephemeral = {ttl_s, phash_algo, phash, destroyed_at: null,
   kept: false}`.
   This is the proof of existence.
4. Show the capture to the operator with a visible countdown of `ttl_s`
   seconds.
5. Delete the file. On success, record a second `tool_result` event with
   the same `phash`/`ttl_s` and `destroyed_at` set to the deletion
   timestamp — the proof of destruction. Once 1-B ships, this second
   event's `parent_event_id` points at the first; until then the pair is
   ordered by `step_index` and distinguished by `meta.tags`
   (`["eye-capture"]` / `["eye-destroy"]`).
6. `--keep` requires trust level >= 2; below that it is a `DENY`,
   `rule_id = "eye_keep_insufficient_trust"`. At trust level >= 2 with
   `--keep`, no deletion step runs, `kept: true`, `destroyed_at: null`
   permanently, and the ledger obligation from level 2 (`policy check
   --json`'s `ledger_write_required`, `docs/POLICY_TRUST.md:39-42`)
   applies to this event the same way it applies to any other autorun
   decision.

### Exit contracts

| Decision/outcome | Exit |
| --- | --- |
| `ALLOW` (capture proceeds) | 0 |
| `DENY` (capture denied, including `eye_keep_insufficient_trust`) | 1 |
| `UNOBSERVED` (capture tool absent) | 2 |
| `ASK` | 3 |
| Deletion fails after a proceeding capture | 2 |

### Failure modes

- Deletion failing after a successful capture is not treated as a
  successful ephemeral capture: HyoDo cannot prove destruction, so it
  records an event tagged `meta.tags = ["evidence_destruction_failed"]`
  with `destroyed_at: null` and `kept: true` (the file is, in fact, still
  present, whether or not that was requested), and the command exits 2 —
  the gate fails closed on "cannot prove destruction," the same honesty
  rule that turns an unreadable trust file into `UNOBSERVED` rather than
  a default grant
  (`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:417-419`).
- A malformed `meta.ephemeral.phash` (wrong length, uppercase, non-hex)
  fails the stateless `validate_event` check before any capture is
  attempted — it is a format error, not a policy question.
- `eye verify` against an `event_id` whose event has no
  `meta.ephemeral.phash` at all (an ordinary event, or a capture that
  never completed) is a plain error, exit 1 — there is nothing to
  compare against.

### Backward compatibility

- `meta.ephemeral` is a new, optional third key on `meta`; every event
  recorded before 2-D has `meta.ephemeral: null` after re-validation,
  exactly like `model`/`tags` behave for events that predate them.
- `EphemeralPolicy` is optional on `PolicyConfig`; a `policy.toml`
  without `[ephemeral]` behaves identically to today, with
  `phash_distance_threshold` defaulting for `hyodo eye verify` alone.
- No existing schema id changes; `_PHASH_RE` and
  `_BUILTIN_SUPPLY_CHAIN_TOOLS` are additive constants.

---

## Rollout order and non-breakage constraints

Phase 1 first, in its own documented order: 1-B → 1-C → 1-D → 1-E
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md:1097-1126`).
Then Stage 2: 2-A → 2-B → 2-C (most of 2-C's structure lands with 1-B
itself; 2-C's own work is the reverse index, pillar clusters, and the
export bridge) → 2-D.

Constraints:

- Every new schema field across 2-A through 2-D is optional; no existing
  `.hyodo/policy.toml` or ledger line changes meaning by re-validating
  against the extended schema.
- No new runtime dependency enters the decision path.
  `evaluate_policy` stays pure stdlib and deterministic; a perceptual
  hash *algorithm choice* (2-D) may require an imaging dependency, but
  that dependency lives in the capture-tool boundary that produces
  `phash`, never inside `evaluate_policy` itself (see Open questions).
- Exit codes are unchanged: `ALLOW` 0, `DENY` 1, `UNOBSERVED` 2, `ASK` 3,
  everywhere a new command reuses the four-way contract.
- `README.md` is not edited by this document or by any package it
  describes; README's line budget is a constraint for whichever PR
  eventually documents a Stage 2 command, not for this design.

---

## Test plan per package

| Package | Assertion |
| --- | --- |
| 2-A | Ingesting a local skill with no `[web]`/`ask_tools` configured still produces `skill_ingest:<source>` in `external_variables` (unconditional, regression-pinning `_BUILTIN_SUPPLY_CHAIN_TOOLS`) |
| 2-A | Trust level 2 does not soften a `skill_ingest:*` decision to `ALLOW`; trust level 3 does |
| 2-A | `manifest.json` records `body_stored: false` unless `--store-body` is passed |
| 2-A | An unreadable skill source is listed with `content_digest: null`, not dropped from the manifest |
| 2-A | An advisory rule with no mechanical check is excluded from the `lens` score and listed under `UNOBSERVED` with a rule-text digest |
| 2-A | `propose` without `--accept` writes nothing; `--accept` writes exactly one proposal file and records exactly one ledger event |
| 2-B | `hyodo inspect examples/fde-evidence-spine` reports coverage `[3, 3]` for its three real files |
| 2-B | An unreadable file is listed under `unreadable` and still counted in `coverage`'s expected total |
| 2-B | No entry in `chunks-manifest.json` ever carries a text/body key |
| 2-B | A file `hyodo safe` flags as secret-shaped is excluded from chunking and reported by digest and location only |
| 2-B | A missing/non-directory `<path>` exits 1 with no manifest written |
| 2-C | `graph export` against a pre-1-B ledger (no `parent_event_id`/`evidence_refs`) succeeds with empty `edges`/`backlinks` |
| 2-C | Once 1-B fields exist, every `evidence_refs` entry appears as a `backlinks` entry keyed by its target |
| 2-C | A claim with no `evidence_refs` is reported the way 1-B's `orphaned_decisions` already is — advisory, not a failure |
| 2-C | The claims-per-function experiment (post-1-B/1-E) lists a function whose documented invariant has no linked test event as unbacked |
| 2-D | `eye capture` with no external tool configured exits 2, `rule_id = "eye_tool_absent"` |
| 2-D | `eye capture` at trust level 1 and level 2 both stay `ASK`; level 3 is `ALLOW` |
| 2-D | A successful capture produces two ledger events; the second carries a non-null `destroyed_at` and the same `phash` as the first |
| 2-D | `--keep` below trust level 2 is `DENY`, exit 1; at trust level >= 2 it sets `kept: true`, `destroyed_at: null` permanently |
| 2-D | A simulated deletion failure records `meta.tags = ["evidence_destruction_failed"]` and the command exits 2 even though the capture itself succeeded |
| 2-D | A malformed `meta.ephemeral.phash` (wrong length or case) fails `validate_event` before any capture is attempted |
| 2-D | `eye verify` output always names a raw Hamming distance and never prints a percentage or a probability-shaped number |

---

## Open questions

- Whether skill provenance should appear in `hyodo score` output, or stay
  confined to `hyodo skills lens`.
- pHash library choice versus a pure-Python implementation, and whether
  that dependency choice belongs at the capture-tool boundary only (as
  designed above) or should be vendored into HyoDo itself for
  determinism across environments.
- Whether `hyodo inspect` should respect `.gitignore` by default, or
  require an explicit `--ignore` pattern so a project's own ignore rules
  (which may hide security-relevant files from `git`) do not silently
  hide them from `inspect` too.
- Whether `skill_ingest:*` and `eye_capture` should ever become
  promotable at trust level 2 for an explicitly allowlisted source or
  capture context, the way `path_outside_root` and a named `ask_tools`
  entry already are — this design keeps them level-3-only conservatively
  until real usage shows the level-2 carve-out is missed.
- Whether `hyodo.graph-export/v1` needs its own version lineage separate
  from `hyodo.evidence-graph/v1` once an external note system depends on
  its exact shape.
- Whether a skill `hyodo skills propose` writes should itself be
  ingestable as a skill in a later run, and if so, how to prevent a
  lens-of-a-lens loop from compiling rules about rules indefinitely.
