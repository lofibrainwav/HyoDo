# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `hyodo score --from-check [--root R] [--json]`: derives the five
  HyoDo Integrity Score pillar inputs from `hyodo check` / `hyodo safe` /
  the test-integrity scan, run in-process (no subprocess), instead of
  requiring the caller to guess five floats. `hyodo/score_derive.py` adds a
  literal `PILLAR_RULE_TABLE` (rule_id -> pillar + weight) with full
  per-pillar provenance and an `OBSERVED` / `PARTIAL` / `UNOBSERVED`
  coverage state per pillar; an `UNOBSERVED` pillar reports `None` (never a
  smuggled 0 or 100) and is excluded from the Eternity geometric-mean term
  rather than defaulted. Explicit `--truth` etc. flags still work alongside
  `--from-check` and override one derived pillar, recorded as
  `override: true` in its provenance. The HyoDo Integrity Score formula
  itself is unchanged; this only proposes its inputs, and the command still
  prints "review signal, not automatic approval." See
  `docs/SCORE_DERIVATION.md` for the rule table and a calibration run
  against the HyoDo repo, an example checkout, and an empty directory.
- `hyodo connect claude-code` now bootstraps a permissive starter
  `.hyodo/policy.toml` when none exists yet (dry run prints
  `would create: .hyodo/policy.toml`; `--write` creates it and tracks its
  digest in `connect.json` the same way it tracks `.claude/settings.json`,
  so `--status` reports drift on it too). An existing policy file — HyoDo's
  own or the operator's — is never overwritten.
- `hyodo safe` (`--json` and text) now reports `scope`
  (`diff` / `status` / `file` / `directory` / `external` / `none`) and
  `coverage` (`FULL` / `PARTIAL` / `UNOBSERVED`) alongside `source`, so a
  reader no longer has to infer what was scanned from a free-text string.
  Text mode prints `Scope: <scope> · Coverage: <coverage>
  (<scanned>/<total> files)` after the `source:` line, plus a hint to pass
  a directory when the scope is `diff` or `status`; both are suppressed in
  `--quiet` and absent from `--json`'s hint (the fields themselves remain
  in `--json`). See `docs/SECURITY_SURFACE.md`.

### Fixed

- `hyodo policy check --shadow` and `hyodo event record --shadow` no longer
  exit 2 (a blocking exit under Claude Code's hook contract) when
  `.hyodo/policy.toml` is missing or invalid, the hook payload cannot be
  mapped, or the ledger append itself fails — shadow mode's documented
  guarantee ("always exits 0, nothing is blocked") now holds on every early
  exit, not only once a policy loads. Each of those paths now prints its
  diagnostic prefixed `[SHADOW, not blocking]` and, where an event exists to
  stamp, records `policy.shadow: true` / `policy.decision: "UNOBSERVED"`
  with the reason. Separately, a missing policy file under
  `--hook claude-code` (shadow or not) is now evaluated against the same
  permissive all-defaults policy `skills ingest`/`eye capture` already fall
  back to, tagged `reason: policy_missing`, and recorded — non-shadow
  behavior for a missing policy is unchanged (still UNOBSERVED, still exit
  2), but it is now a recorded decision instead of a crash before anything
  is recorded. Previously, `hyodo connect claude-code --shadow --write` on a
  repository without a policy file blocked every tool call, the opposite of
  shadow mode's purpose.
- `hyodo mcp continuity` no longer reports `status: READY` on a workspace
  with no `.hyodo` stores at all and 0/2 hosts observed. `measure_continuity`
  only appended `reasons` for corrupt/invalid stores, so "nothing exists"
  read as READY — a semantic false-green. The `hyodo.continuity/v1` receipt
  now separates `integrity_status` (READY when every present store parses,
  CORRUPT otherwise) from `coverage_status` (OBSERVED/PARTIAL/UNOBSERVED,
  based on hosts observed and whether the required stores are present and
  readable); overall `status`/exit code stay READY/0 only when both are
  satisfied, so an empty root now correctly reports `UNOBSERVED`/exit 2.
- `hyodo safe --scan gitleaks`: adapter used the removed `--format` flag
  (gitleaks 8.x exits 126); now `--report-format json --report-path -` plus
  a `version` positive control; regression test with a fake binary.
- `hyodo safe --scan trufflehog`: added the same positive control as
  gitleaks (`trufflehog --version`, accepting either stdout or stderr,
  requiring a version-looking string). A trufflehog binary that starts and
  exits with no output was previously only caught by the generic
  no-output-plus-nonzero-exit rule; a CLI-drifted binary that still exits 0
  with unrelated output would have been silently reported as clean. Failure
  now reports a high-severity `trufflehog_failed` finding and the scan is
  not attempted; regression tests with fake binaries.

### Changed

- `hyodo mcp continuity` now counts hook-recorded actors as hosts, not only
  MCP access-ledger callers. Any `.hyodo/agent-events.jsonl` event with
  `actor: "agent"` and a non-empty `actor_id` — the shape `hyodo connect
  claude-code` produces — counts as its own distinct observed host
  (`source: "hook"`, identity `hook:<actor_id>`), even though a hook-wired
  host never touches the MCP access ledger. A shadow-stamped event
  (`policy.shadow: true`) still counts: the host was observed even though
  nothing was enforced. Each caller row now carries a `source: "mcp" |
  "hook"` field, hook rows add `calls` and `shadow`
  (`true`/`false`/`"mixed"`), and the receipt's `hosts` block adds
  `by_source: {"mcp": N, "hook": M}`. `coverage_status` reaches `OBSERVED`
  once the combined host count meets `expected_hosts` and the agent-events
  store is present and readable, and either the access ledger is present
  and readable or at least one hook host was observed — a repository
  onboarded only through Claude Code hooks (no MCP client ever connected)
  can now reach `OBSERVED` instead of being stuck at `hosts observed: 0/2`
  forever. The text CLI output prints each host's source; the JSON schema
  id (`hyodo.continuity/v1`) is unchanged. See `docs/CONNECT.md` and
  `docs/M5_REMOTE_CONNECTOR_CONTRACT.md`.

## [4.15.0] - 2026-09-07

Stage 2 of the HyoDo Agent OS design on the source line: skill lens, folder
absorption, graph export bridge with actor rings and derived roles,
ephemeral visual evidence, the optional `actor_id` field, the research-node
hand-off, and the M5-C/M5-D onboarding and continuity receipts.

### Added

- `hyodo skills ingest --from-node <file>` accepts a BYOM research node's
  `hyodo.skill-retrieval/v1` hand-off (rule text + digests + an ordinal
  rank; never a vector, never a float score), gated by the same
  `skills.ingest` policy as a path/url source
  (`skill_ingest:node:<label>`), and `hyodo skills propose` gains a
  `## Retrieved` section listing node-sourced rules that passed. See
  "Research node contract" in `docs/SKILLS.md`.
- `hyodo dashboard`'s `/graph` page now renders one grid (five virtue
  columns by actor row, oldest-to-newest within each cell, amended event
  -> virtue mapping for test runners/file ops/network fetches/the mission
  prompt) instead of two disconnected lists, with an SVG overlay drawing
  `parent_event_id` and `evidence_refs` edges anchored at each tile's own
  boundary (dangling refs as short red stubs, off-grid endpoints skipped
  and counted separately), a 9x9 pixel-grid orb pulse replacing the flat
  circle, tile labels showing the tool name or event kind (full text kept
  in the tile's `title`), short lineage-id row labels, indented
  collapsible nested rows (an `orchestrator` role requires an actual
  spawned `agent` child lane), and a fixed open question under any virtue
  column with zero events. See
  `docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`
  and `docs/GRAPH_EXPORT.md`.
- Optional `actor_id` field on `hyodo.agent-event/v1` (additive; absent or
  `null` by default): an opaque label the harness chooses (session id, seat
  name, model alias) so two agents in one run keep separate rows instead of
  collapsing into one. `hyodo event record --actor-id <label>` fills it in
  when the event JSON lacks one; `--hook claude-code` sets it from the hook
  payload's `session_id`. Carried through `hyodo report --format graph` and
  `hyodo graph export` node output, and through the local graph viewer's
  per-actor rows (`parent_row`/`depth`/`role` now detect nesting and
  orchestration across labelled agent-to-agent rows, not just
  agent-to-hyodo). HyoDo never derives identity or authorization from it.
  See `docs/CONNECT.md`, `docs/GRAPH_EXPORT.md`.
- `hyodo eye capture|verify` (Stage 2 package 2-D, "ephemeral visual
  evidence"): capture one screen through a BYOM tool
  (`.hyodo/config.toml`'s `[eye] command`), record an exact digest and a
  pure-stdlib 64-bit perceptual hash, show it with a countdown, delete it,
  and record proof of destruction as a second ledger event -- no pixels
  ever reach the ledger. `eye.capture` is an unconditional external
  variable (softened to `ALLOW` only at trust level 3), and `eye verify`
  reports a raw Hamming distance, never a percentage. See `docs/EYE.md`.
- `hyodo inspect <path>` (Stage 2 package 2-B, field-deployment absorption):
  digest every file under a directory into `.hyodo/folder-manifest.json`
  (`hyodo.folder-manifest/v1`) and chunk it into
  `.hyodo/chunks-manifest.json` (`hyodo.chunks-manifest/v1`, byte ranges and
  digests only, never chunk text), with an honest `observed/expected`
  coverage count, secret-shaped files excluded from chunking and reported by
  digest and location only, `--ignore` globs, and an optional
  `--remote-inventory` claim recorded (never fetched) from a connector like
  a Drive MCP listing. Local, read-only, never calls `evaluate_policy`, no
  network, no new dependency. See `docs/INSPECT.md`.
- `hyodo skills ingest|lens|propose` (Stage 2 package 2-A, the "skill
  lens"): ingest a project's own Markdown skill as an external variable
  (never silently `ALLOW`, `.hyodo/skills/manifest.json`), report live
  per-pillar `observed/expected` coverage with rule-level provenance, and
  propose a tailored custom skill made of the currently-passing compiled
  rules. No model, no RAG, no fetched skill bodies by default. See
  `docs/SKILLS.md`.
- `hyodo mcp config <host>` (`claude-code`, `claude-desktop`, `cursor`,
  `vscode`, `codex`): prints, or with `--write` merges key-level, the MCP
  client configuration that registers HyoDo's local stdio adapter — no
  bearer token, no secret, ever. `chatgpt` reports `UNOBSERVED` honestly
  (the remote connector is not live). See `docs/ONBOARDING.md`.
- `hyodo start` is now the first-use onboarding flow: workspace/detected
  hosts, the existing audience question, one "connect which host now?"
  question (at most three choices, one preview, one yes/no confirm), then a
  first prompt to try. Non-interactive runs print the same four steps as
  text and ask/write nothing.
- `hyodo mcp continuity` (M5-D, `hyodo.continuity/v1`): a read-only receipt
  proving that a second MCP host (the paired loopback bridge) shares one
  local truth store with the stdio adapter — no second ledger, remote
  (ChatGPT) honestly `UNOBSERVED`. `hyodo mcp contract --json` additively
  folds the same receipt in as `"continuity"`.
- `hyodo graph export [--out .hyodo/graph.json] [--yes] [--root]` (Stage 2
  package 2-C): writes the `hyodo.graph-export/v1` bridge artifact an
  external note system can turn into permanent notes — nodes/edges
  mirroring `hyodo report --format graph`, a `backlinks` reverse index,
  and six-pillar `clusters`. `hyodo report --format graph` gains the same
  `backlinks` field, additively; its exit contract is unchanged. See
  `docs/GRAPH_EXPORT.md`.
- Actor rings (Stage 2 package 2-C, core-engine-monitor spec section 5,
  step (c)): `hyodo dashboard`'s `/graph` page now nests each actor row
  with a derived `role` (`human`/`orchestrator`/`reviewer`/`worker`) and
  lets you click a row's label to open its skills/memory/routines/tools
  rings, built from the ledger and local `.hyodo/skills/manifest.json` /
  `.hyodo/connect.json` manifests only — no network. `GET
  /api/actor?key=<row key>` serves the same rings as JSON.

### Fixed

- Test integrity (1-E) no longer flags a test as `no_assertion` when it
  delegates its assertions to a same-module helper function (checked
  transitively up to three call hops); a helper defined in another module is
  still unresolved and the test stays flagged. See `docs/TEST_INTEGRITY.md`.
- `hyodo skills lens` now reports a seventh `unclassified` row/JSON key for
  compiled rules that carry no `[pillars: ...]` tag and match no keyword, so
  every compiled rule is visible in exactly one lens row. See
  `docs/SKILLS.md`.

### Evidence

- Signed tag `v4.15.0` (object `7b40d401`, commit `4cd571c0`, GitHub
  verification valid); release evidence run `34152948925` attached the
  CycloneDX SBOM and its SHA-256; publish run `34153047735` published to
  PyPI via OIDC with provenance for the wheel and the sdist. Receipt:
  `docs/releases/4.15.0.md`.

## [4.14.0] - 2026-09-07

Phase 1 closeout: test integrity, `hyodo connect`, the local
evidence-graph viewer, audience profiles, and the M5-B local bridge
complete Phase 1 packages 1-A through 1-E.

### Fixed

- Surface trust level 2+ ledger obligations and recording outcomes in CLI receipts;
  show ASK and UNOBSERVED event decisions in yellow.

### Added

- Audience profiles (`--audience vibe|engineer|professional`, `HYODO_AUDIENCE`,
  or `[audience]` in `.hyodo/config.toml`) on `check`, `safe`, `policy check`,
  and `event record --policy`: presentation wording only — decisions, exit
  codes, `rule_id`s, evidence references, and `--json` payload content stay
  byte-identical across profiles (a `--json` payload may add one key,
  `"audience"`). See `docs/AUDIENCE.md`.
- `hyodo start` now asks one interactive question ("Who is reading these
  results?") to write `.hyodo/config.toml`'s audience profile; non-interactive
  runs ask nothing and write nothing.
- Test integrity (Phase 1-E): `hyodo check` now runs a native, model-free AST
  scan of the project's own tests (`hyodo/test_integrity.py`, reusing
  `hyodo/safe/anti_gaming.py`'s HYO-SAFE-010/011/012 rule ids) alongside its
  four existing gates, reporting how many tests assert nothing observable
  (`check --json`'s `test_integrity` object). `check --strict-tests` fails the
  Truth gate when pyright passes but vacuous tests are found. See
  `docs/TEST_INTEGRITY.md`.
- Widened credential-shaped URL detection (`hyodo/events.py`): `/.aws/`,
  `/.ssh/`, `/.netrc`, `/.kube/`, `credentials`, `id_rsa`, `.pem`, and
  `/etc/shadow` path markers; `password=`, `access_token=`, `apikey=`,
  `auth=`, and `sig=` query markers. See `docs/POLICY_TRUST.md`.
- Local evidence-graph viewer: `hyodo dashboard` now serves `GET /graph`
  (server-rendered five-column virtue layout plus the core-engine-pulse orb)
  and `GET /api/graph` (live `hyodo.evidence-graph/v1` JSON, mirroring
  `hyodo report --format graph`'s corrupt/unreadable handling). Rollout step
  (b) of the core engine monitor design shipped server-rendered; sharing the
  design's TypeScript renderer with the public site prototype is pending.
- `hyodo connect` (Phase 1-D): dry-run-by-default harness wiring for Claude
  Code hooks (`.claude/settings.json`), `pre-commit`, and GitHub Actions,
  plus `--shadow` mode (`policy check`/`event record` gain a `--shadow` flag
  and a `--hook claude-code` payload adapter) that records the real decision
  with `policy.shadow: true` while always exiting 0; `--status` reports
  drift against `.hyodo/connect.json`. `cursor`/`codex` report UNOBSERVED —
  their hook contracts are not verified against a live install.
- M5-B local bridge: an untracked `.hyodo/pairing.json` pairing lifecycle
  (`hyodo mcp pair` / `unpair` / `revoke` / `pairing show`), a `--paired`
  option on `hyodo mcp serve` that verifies the caller's bearer token against
  that pairing on every request (a revoke takes effect immediately, never a
  static token comparison), and a `bridge` object in
  `hyodo mcp contract --json` reporting the measured local pairing state —
  remote `availability` stays `UNOBSERVED` (#163).
- Measured summary verdicts and deterministic `--explain` / `--quiet`
  presentation for check, safe, and policy check.
- `hyodo check --json` receipts and verdict fields in safe and policy JSON.
- M5-A machine-readable remote connector contract via `hyodo mcp contract --json`, with explicit CONTRACT_ONLY/UNOBSERVED availability, OAuth discovery requirements, workspace pairing lifecycle, and local-execution boundaries (#163).
- Graph edges and `hyodo report --format graph` (#160).
- Anti-gaming AST visitor, not yet wired into a CLI command (#161).
- Digest-only `tool.urls`, `gate:` evidence refs, `require_mission_prompt`,
  and `unknown_edge_target` rejection reasons in the 1-B completion PR.

### Changed

- `tool.urls` no longer stores a plain-text path by default.

- Document trust ladder, grants, and ASK exit code 3 in CLI help.

## [4.13.0] - 2026-09-06

Policy ASK, score identity, and release-surface hygiene preparation.

### Added

- Policy evaluation now reports measured `ASK` decisions for unlisted web
  domains, outside-root paths, and configured discretionary tools. Operators can
  cap and explicitly grant trust with `hyodo policy trust grant|show`.
- Trust grants are stored in the untracked `.hyodo/policy-trust.json` file.
- OpenSSF Scorecard, MCP Registry, Claude Code marketplace, and funding
  distribution surfaces.

### Changed

- Version preparation now validates and updates all seven version-bearing
  sources together: VERSION, package metadata, Dockerfile, and distribution
  manifests.
- The release preparation and version-setting scripts share one update path.
- The public score label is **HyoDo Integrity Score**, using the
  **Six-Virtue Model** and **Trinity Gates** subset, with **HYOGOOK V5**
  retained as formula lineage.
- The GitHub required score check context is now **HyoDo Integrity Score**;
  the formula lineage remains visible in its workflow output.

### Fixed

- `event record --policy` now returns exit `3` for `ASK` and exit `2` for
  policy `UNOBSERVED`, instead of treating every non-DENY decision as success.
- Release preparation now rejects divergence in any extended version source,
  not only VERSION, pyproject.toml, and `hyodo/__init__.py`.
- `hyodo safe` now discloses directory-scan coverage and the interactive
  installer uses the current `--hyo` flag.

### Evidence

- Policy ASK implementation merged through PR #149.
- Public score identity merged through PR #151.
- Public GitHub score check context merged through PR #152.
- Post-merge CI and install smoke passed on the main merge commit.
- This is cycle preparation only; no tag, GitHub Release, or PyPI publication
  is performed by this change.

## [4.12.0] - 2026-09-05

Release-trust and external-consumption seal after the 4.11.0 MCP access-ledger
release.

### Added

- CI-only Hypothesis reproducibility profile that keeps local Hypothesis
  exploration and local example databases intact.
- Status-aware mutmut 3.7.0 mutation receipt parser and sealed full-core
  mutation census.
- Cosmic Ray scoring mutation automation with advisory PR feedback and
  scheduled/manual full-core execution.
- Pre-commit discoverability hooks for `hyodo check` and `hyodo safe --strict`.
- Same-ref composite GitHub Action for external consumers.
- SARIF 2.1.0 report output for measured HyoDo findings.
- Consumer smoke tests for pre-commit and the composite action.
- Verified annotated release-tag gate before PyPI publication.
- Immutable-release-safe exact-tag SBOM evidence workflow.

### Changed

- PyPI publication no longer starts from tag push alone. The primary publish
  trigger is now `release: published` after durable Release evidence is present.
- PyPI publication now requires a published GitHub Release with durable
  `sbom.cyclonedx.json` and `sbom.cyclonedx.json.sha256` assets.
- The PyPI build independently downloads and verifies the release SBOM checksum
  before building distributions.
- Mutation workflow PR triggers are narrowed to scoring-relevant surfaces so
  release/docs-only PRs do not pay the expensive advisory mutation run.

### Fixed

- Hypothesis CI reproducibility no longer disables local exploratory behavior.
- Mutation scoring no longer collapses timeout, skipped, not-checked, no-test,
  interrupted, segfault, type-check, and suspicious outcomes into a fake
  denominator.
- Release evidence publication avoids destructive `--clobber` behavior.
- Published releases missing durable evidence fail closed instead of being
  mutated after publication.

### Evidence

- mutmut 3.7.0 full-core census: 1,847 generated / 163 killed / 155 survived /
  1,529 no selected tests; tested kill rate 51.26%; all-generated kill rate
  8.83%.
- Cosmic Ray scoring-core advisory evidence: 345 total / 150 killed /
  195 survived; kill rate 43.48%; fresh automation artifact `9979111436`.

## [4.11.0] - 2026-09-03

Feature release: MCP access ledger and agent-rules opt-in (Issue #95 M4 complete).

### Added

- `hyodo mcp access-log` — audit trail of MCP tool invocations. Every tool call
  is recorded to `.hyodo/mcp-access.jsonl` (append-only, best-effort, never
  blocks the call). Supports `--root`, `--limit`, and `--json`. Fail-closed on
  missing `mcp` extra (exit 2, install hint).
- `hyodo mcp rules list` — show active agent rules from
  `.hyodo/agent-rules.toml` (or built-in defaults when absent). Supports
  `--root` and `--json`.
- `hyodo mcp rules init` — write default agent rules to
  `.hyodo/agent-rules.toml` (idempotent, preserves an existing file).
- `hyodo_agent_rules` MCP tool — returns current agent rules over the MCP
  protocol.

## [4.10.0] - 2026-09-03

Feature release: new `hyodo mcp doctor` diagnostic command.

### Added

- `hyodo mcp doctor` — read-only local MCP setup diagnostic. Reports SDK
  availability and major version, workspace root validity, port availability
  (and dashboard-reserved 8768), and Tailscale connectivity. Supports `--json`
  for machine-readable output. Always exits 0; diagnoses, never blocks.
  Fail-closed on missing `mcp` extra (exit 2, install hint).

## [4.9.0] - 2026-09-03

Compatibility release: the optional MCP adapter now runs on both MCP Python
SDK majors, and release tooling stops failing on valid distributions.

### Fixed

- The MCP adapter now runs on both MCP Python SDK majors. The SDK's v2.0.0
  removed `mcp.server.fastmcp` (renamed `FastMCP` to `MCPServer` in
  `mcp.server.mcpserver`) and moved host/port/`json_response`/
  `streamable_http_path` from the constructor into `streamable_http_app()`,
  which made the dependabot range-widening PR fail CI for a month. A new
  `hyodo._mcp_compat` resolves the installed major once per process; the CLI's
  "MCP support is not installed" probe works on both (and still fails closed
  with exit 2 on a core install without the extra); CI now exercises the v1
  line on a pinned job so widening the extra to `mcp>=1.27,<3` cannot silently
  drop it.
- `scripts/verify-public.sh` and the smoke/publish workflows now upgrade
  `twine` to `>=7` before `twine check`. twine 6.x cannot parse the
  Metadata-Version 2.5 sdists current hatchling emits and failed the local
  full verify on a valid distribution.

- Dashboard evidence now names why a safety risk score is absent. `risk_score`
  is still omitted when there is nothing to scan (an empty change set must not
  read as "score 0, therefore safe"), but a single `null` could not tell
  "the scan never ran" apart from "the scan ran and found nothing to measure".
  A consumer read it the wrong way and rendered a scan that had actually run as
  unobserved. `safety.risk_score_state` now carries `measured` or
  `no_scan_target` alongside it. Additive field — existing consumers are
  unaffected, and `safety.source` remains the reliable "did a scan run" signal.

### Changed

- The "Public language: English only" rule in `CLAUDE.md` is now enforced by a
  test instead of being a line nobody checked. Tracked `.py` and `.md` files may
  contain Korean only as the six trilingual virtue labels; everything else is
  English. Accumulated Korean comments and docstrings were translated, and a
  handoff doc that told agents the opposite was corrected.
  Commit messages and PR title/body are covered by a `public-language` CI job,
  since a test cannot read them. Attribution states the model in
  `Co-Authored-By` rather than a Korean authorship line.

## [4.8.2] - 2026-07-22

Security and observability release. An external review found fifteen ways the
tool could be told what to conclude, or could report something it never looked
at as clean. Every finding was reproduced before and after the fix.

### Security

- **Policy decisions are measured, not accepted.** A caller could put
  `{"policy": {"decision": "ALLOW"}}` in its own event and have it recorded and
  tallied. Validation now always produces an unevaluated policy block; only
  HyoDo's own evaluation stamps `evaluated_by`. The caller's assertion is kept
  under `policy.claimed` for audit rather than deleted.
- **`max_steps` counts the ledger, not the caller.** The budget was checked
  against the self-reported `step_index`, so an agent resending `step_index: 0`
  never exhausted it. An unreadable ledger is `UNOBSERVED`, never `ALLOW`.
- **Digests are recomputed from the body.** A body could arrive paired with an
  unrelated digest; digest-only mode then dropped the body and kept the lie.
- **`event_id` reuse is refused.** Same id with identical content is idempotent;
  same id with different content is a conflict.
- **Shipped `blocked_path_globs` examples now match.** `**/.env` never matched a
  repository-root `.env`, so all four patterns in the FDE example policy were
  inert.
- **Workflow input is bound through `env:`.** `inputs.tag` was interpolated into
  the release script before shell execution, ahead of its own validation.
- **A crashed secret scanner is not clean.** `gitleaks`/`trufflehog` return codes
  were ignored, so a dead scanner produced an `info`-level "no secrets found"
  that `--strict` let through.
- **Raw-body storage is operator consent.** MCP clients could set
  `full_body=True` themselves; it now requires `hyodo mcp stdio
  --allow-full-body`, and a denied request is reported, not silently downgraded.
- **BYOG command sets are fingerprinted.** A `.hyodo/gates.toml` that changes its
  commands after first use is `SKIP` (never `PASS`) non-interactively, or shown
  for approval interactively. `HYODO_GATES_TRUST_ALL=1` pre-approves for CI.

### Fixed

- **`hyodo safe` reads new files, not just their names.** Without a path argument
  the fallback corpus scanned `git status` output as text — and `git diff HEAD`
  is empty exactly when the only changes are untracked files. Untracked
  directories are expanded too.
- **An unreadable ledger no longer reports as zero events.** `read_agent_events`
  returns `None` for unreadable, and the report prints `UNOBSERVED`.
- **`hyodo eval` runs in `--root`** and records provenance (working directory,
  git HEAD, dirty flag). `git_dirty` is `None` when git could not be consulted —
  never a false "clean".
- **Unresolved `$ref` exits 2 instead of raising.** Reference resolution fails
  inside `iter_errors`, which was outside the error guard, so `--json` consumers
  received a traceback.
- **`hyodo_safe` accepts `max_files`** so an MCP client can scan past the
  directory cap.
- **Out-of-range pillar scores fail.** `-t 9` (a typo for `-t 0.9`) was clamped
  to a perfect `1.0` while the table displayed `9`.

### Changed

- `referencing` is now a declared dependency: `hyodo.schema` imports it directly.
- `CONTRIBUTING.md` describes the review process that actually runs. A security
  tool should not overstate its own governance.

## [4.8.1] - 2026-07-21

### Added

- **Auditable local scan exceptions** — optional
  `.hyodo/scan-exceptions.toml` keeps private legal or financial working
  material outside a product-code syntax boundary with a required reason.
  Safety exceptions require both an exact workspace-relative path and one
  exact finding rule; malformed policies fail closed with exit code 2.

## [4.8.0] - 2026-07-21

### Added

- **Optional local MCP connector** — `hyodo[mcp]` exposes the existing CLI
  operations (`context`, `safe`, `check`, event, and policy) to local LLM
  clients over stdio. Loopback serving is opt-in; Tailscale binding requires a
  token and never listens on public interfaces.
- **FDE evidence gates (Phases 2–4)** — `hyodo schema check` validates
  versioned JSON payloads, `hyodo eval` deterministically scores local golden
  JSONL fixtures, and `hyodo report` produces local Markdown or HTML evidence
  reports with a reproducible content hash.

### Security

- Remote MCP transports fail closed without a token. Public binding, wallet,
  Redis, Vercel execution, and runtime-interceptor claims remain out of scope.

### Notes

- M4 polish (`mcp doctor`, access ledger, and agent-rule opt-in) is deferred.
- Tailscale bind and token rejection are tested; a second-device MCP tool call
  has not been measured and is not claimed as completed.

## [4.4.0] - 2026-07-21

### Changed

- **README positioning** — lead with FDE / AI agent guardrail value
  (audit evidence, policy DENY, BYOG, fail-closed), not pre-commit
  replacement. Engineering labels first; pillar branding dual-mapped.
  Claim boundary: interceptor/PDF export not shipped.
- Package description updated to match FDE/agent-guardrail positioning.

### Added

- **FDE Evidence Spine (Phase 1 MVP)** — opt-in agent event ledger and local
  policy gate (not a runtime interceptor; callers must enforce DENY):
  - schema `hyodo.agent-event/v1` in `hyodo/events.py`
  - append-only ledger `.hyodo/agent-events.jsonl` (separate from gate
    `history.jsonl`)
  - digest-only default; `--full-body` opt-in for raw `io.*_text`
  - policy schema `hyodo.policy/v1` (`.hyodo/policy.toml`) with
    `allowed_tools`, `max_steps`, `blocked_path_globs`
  - CLI: `hyodo event validate|record`, `hyodo policy check`
  - exit contracts: validate/record `0|1|2`; policy `ALLOW=0` / `DENY=1` /
    unobserved=`2` (never silent ALLOW)
  - tests: `tests/test_agent_events.py`
  - examples: `examples/fde-evidence-spine/`

## [4.3.0] - 2026-07-21

### Added

- **BYOG shell idioms** (#89, found by the first real-world BYOG dogfood):
  `KEY=VALUE` env prefixes in a gate command are split out and passed to the
  subprocess environment (so `command[0]` is the real binary — no more false
  SKIP "not installed"), and wildcard arguments are glob-expanded before
  execution. Expansion is sandboxed to the project root: absolute patterns and
  `../` escapes are never expanded, and zero matches keep the literal argument
  (POSIX nullglob-off behavior). `shell=False` remains the only execution mode.
- **Gate-set fingerprint in history receipts** (#87): every receipt now carries
  `gate_set_fingerprint` (SHA-256/12 of the JSON-encoded sorted gate-name set —
  collision-proof against delimiter tricks), and `consecutive_all_pass_runs`
  resets at gate-set boundaries so shrinking the gate set can no longer
  silently extend a streak. Legacy receipts are compared via fingerprints
  derived from their recorded gate names; the ledger stays append-only.
  `RECEIPT_SCHEMA_VERSION` is now 2.

### Fixed

- `hyodo check` against a checkout whose canonical gates use env-prefix or
  glob shell idioms (e.g. `KINGDOM_TEST_SCOPE=unit bash scripts/run-tests.sh`,
  `shellcheck scripts/*.sh`) now actually executes those gates instead of
  reporting a misleading SKIP/FAIL.

## [4.2.0] - 2026-07-21

### Added

- **`hyodo init [PATH]`** — detects a project's existing quality tools
  (`detect_project_gates`) and writes `.hyodo/gates.toml` (Bring-Your-Own-Gates,
  schema `hyodo.gates/v1`), printing a trilingual pillar/command/source table
  for every absorbed gate. Refuses to overwrite an existing config unless
  `--force` is passed. An empty detection writes an honest starter template
  (commented-out examples) instead of guessing.
- **`hyodo check` resolves `.hyodo/gates.toml` first**: when present, `check`
  runs the absorbed user gates instead of the HyoDo-checkout-only preset
  (`--general` remains an explicit, unchanged override). A malformed
  `gates.toml` exits `2` with the parse/schema error instead of silently
  skipping the user's gates. The checkout-only guidance now points to
  `hyodo init` when neither a user config nor a HyoDo checkout is found.
- **`hyodo dashboard` measures `.hyodo/gates.toml` gates when present** —
  `evidence.gates` is built from the user's own gate names instead of the
  fixed `typecheck`/`lint_format`/`tests`/`sbom` keys; falls back to the
  built-in checkout gates otherwise. Benevolence/Hyo/Eternity stay native
  collectors, unaffected by Bring-Your-Own-Gates.
- Base dependency `tomli>=1.2.0; python_version < "3.11"` — `hyodo.gates`
  needs a TOML parser on Python 3.10 checkouts (stdlib `tomllib` is 3.11+),
  and `hyodo.cli.main` now imports `hyodo.gates` unconditionally at startup.

## [4.1.0] - 2026-07-21

### Added

- **`hyodo safe --scan gitleaks|trufflehog|all`** — external secret scanner
  integration. gitleaks runs offline regex detection; trufflehog live-verifies
  candidates (documented: candidate secrets leave the machine) and unverified
  hits report as medium severity. `--scan all` merges both; a scanner that
  fails to run is surfaced as a medium `*_unavailable` finding — never
  silently dropped. If neither runs, the scan exits `2`.
- **`hyodo safe --max-files N`** — configurable directory scan cap
  (default 40, `0` = unlimited).
- **`hyodo score --partial`** — allows missing pillars (defaulted to 0.5).
  The score band (STRONG/CAUTION/BLOCK) stays score-derived; partial input
  adds a separate `SIGNAL_CONFIDENCE_WEAK` marker instead of overwriting the
  band label.
- **`hyodo check --general`** — bounded language-agnostic syntax gates with
  auto-detection (Python `py_compile`, TS `tsc --noEmit`, JS `node --check`,
  Go `go vet`, Rust `cargo check`, Shell `bash -n`; up to 50 files per
  language, vendor directories pruned). Output states the sampling limit.
- **External scan display row** — `summarize_checks` now renders an
  "External scan" row when external findings exist, so scanner hits are
  visible in the table instead of only inflating the risk score.

### Fixed

- **Post-publish verify** (`scripts/release/verify-pypi-release.py`): provenance
  is polled with its own retry budget (version JSON + PEP 740 integrity API),
  instead of a single-shot check right after the version appears. Prevents the
  false red seen on 4.0.1 when attestation CDN lagged the package JSON.
  Publish workflow uses `--provenance-retries 30` (~5 min). Install smoke
  refreshes the wheel URL each attempt (index → wheel-url fallback retained).

## [4.0.1] - 2026-07-20

### Fixed

- **`hyodo score` no longer defaults missing pillars to 1.0.** All five
  pillars must be provided explicitly; partial input exits `2` instead of
  inventing a false `REVIEW_SIGNAL_STRONG`.
- **Legacy flag collisions are errors.** Combining `--hyo` with `--eternity`,
  or `--benevolence` with `--serenity`, exits `2` with a clear message
  (previously the legacy flag silently overrode the primary value when it
  was not exactly `1.0`).
- **`is_strong_review_signal`** rejects non-numeric `risk_score` /
  `trinity_score` (e.g. level strings like `"low"`) with `TypeError`.
- **`hyodo safe` findings** include optional `path` and `line` for file and
  per-file directory scans (JSON + text). Git-diff default corpus still has
  no path attribution.
- Empty **Production impact** row is always ✅ (no non-strict-only ⚠️ that
  looked like a finding without a finding).

### Changed

- CLI score title and onboarding: **HYOGOOK F-score (philosophy V6)** — formula
  lineage V5 remains the F math; philosophy version is V6.
- Removed dead Dependabot `/afo_core` ecosystem block (tree removed from the
  public repo on 2026-07-19).
- Dockerfile: drop placeholder maintainer email; version label `4.0.1`.

### Docs

- Quick Start pin and demo checklists updated to `4.0.1`.
- Onboarding example requires all five pillars.

## [4.0.0] - 2026-07-20

### Removed

- **Breaking:** the `loyalty=` keyword alias on `calculate_hygook_v5_score`
  and the `--loyalty` CLI flag (deprecated in 3.3.0). Use `hyo=` / `--hyo`
  (the `-c` short flag now feeds `--hyo`). Positional callers are unaffected.
- **Breaking:** `should_auto_approve()` (deprecated since 3.2.x with removal
  announced for 4.0.0). Use `is_strong_review_signal()`.

### Changed

- CI and verification scripts exercise `--hyo` directly; the legacy
  `calculate_trinity_score()` path (including its `loyalty` parameter and
  `TRINITY_WEIGHTS` keys) stays frozen for historical reproducibility.

### Note

- The 3.3.0 deprecation window was intentionally short (same-day releases);
  3.x remains on PyPI for callers that still pass `loyalty=`.

## [3.3.0] - 2026-07-20

### Added

- `hyo` is the canonical fourth pillar of the HYOGOOK score (philosophy V6):
  `calculate_hygook_v5_score(..., hyo=...)` and `hyodo score --hyo`. Positional
  callers are unaffected.
- `hyodo.__philosophy_version__` (`"V6"`) exposes the philosophy lineage
  separately from the package semver.
- `tests/test_hyo_restoration.py`: deprecation contract, signature/doc pillar
  parity, and the F-score floor (6.0) sealed as regression tests.

### Deprecated

- `loyalty=` keyword on `calculate_hygook_v5_score` and the `--loyalty` CLI
  flag: both emit `DeprecationWarning` and map to `hyo`. Passing both raises
  `TypeError`. Scheduled for removal in 4.0.0.

### Changed

- `PHILOSOPHY.md`, `README.md`, and demo docs now name the pillar Hyo —
  a reciprocal and voluntary relational discipline superseding the earlier
  one-sided Loyalty. The legacy `calculate_trinity_score()` path is frozen so
  historical scores remain reproducible.

## [3.2.1] - 2026-07-20

### Fixed

- `hyodo check` and the public verification script now pass the interpreter
  running HyoDo to Pyright. This prevents false missing-import failures when a
  virtual environment is active but a different system Python appears first on
  `PATH`.

## [3.2.0] - 2026-07-19

### Added

- `hyodo safe --json` emits a single machine-readable JSON document (findings,
  risk score, level, and a self-reported exit code) so external CI can consume
  `safe` results programmatically; exit codes are identical to text mode.
- `docs/SAFE_RULES.md` documenting every `safe` rule family (secrets, dangerous
  commands, production impact), the scoring model, and known limits and
  false-positive shapes.

### Changed

- Simplified the README, contribution guide, repository agent guidance, and
  roadmap around the supported public CLI.
- Consolidated onboarding into `QUICK_START.md`.
- Made public entry-document lint a release blocker and reduced the extended
  `afo_core` advisory lint to one non-blocking, visible snapshot.
- `hyodo check` now reports how many gates actually executed (`N/M gates ran`)
  in the pass and fail banners, so exit-code consumers can tell a full run from
  a partial one.
- README reframed around two tracks: `safe` (runs on any repository) versus
  `check` (validates a HyoDo checkout only).

### Removed

- Redundant `LICENSE.md`; `LICENSE` remains the single MIT license source.
- Redundant `QUICK_START_SIMPLE.md`.
- Stale tracked demo receipt; `scripts/demo-dry-run.sh` now produces local
  evidence that must be regenerated before use.

### Fixed

- `hyodo check` SBOM/Eternity gate no longer swallows HyoDo's own invocation
  bugs as an environment SKIP: a genuine OS/environment failure still SKIPs, but
  an unexpected exception now FAILs — closing an anti-ghost-gate gap.

## [3.1.8] - 2026-07-16

### Added

- **PyPI Trusted Publishing workflow** (`.github/workflows/publish.yml`): OIDC-only
  publish on annotated tags `vX.Y.Z`, GitHub Environment `pypi`, build +
  `pypa/gh-action-pypi-publish`, then post-publish provenance + install smoke.
- `scripts/release/verify-pypi-release.py` — public API wait, provenance check,
  cold `pip install` smoke.
- `docs/PYPI_TRUSTED_PUBLISHING.md` — one-time PyPI publisher fields and release
  flow SSOT.

### Changed

- Release checklist: PyPI path is Trusted Publishing (not long-lived API token).
- Version SSOT aligned to **3.1.8**.

### Notes

- Requires one-time PyPI Trusted Publisher registration (owner account) and
  GitHub Environment `pypi` before the first OIDC publish succeeds.
- Manual `twine upload` with API token is no longer the documented release path.

## [3.1.7] - 2026-07-16

### Fixed

- **Ruff gate runs format**: `hyodo check` Gate 2 now executes both `ruff check`
  and `ruff format --check` (with `--fix`, format write). Format-only failures
  no longer false-green.
- **`hyodo safe` scan read failure**: unreadable paths report `error:read:` and
  exit **2** (same class as missing path). OSError is no longer swallowed into
  empty corpus + exit 0.
- **Path-length-stable CLI test**: checkout path assertion tolerates Rich
  line-wrapping of long absolute paths.

### Changed

- Public regression tests cover format-fail gate and scan-error exit 2.
- Coverage floor raised from `fail_under = 0` to `fail_under = 50` for the public
  `hyodo` package.
- Version SSOT and install pins aligned to **3.1.7**.

### Notes

- Follow-up Truth Patch after 3.1.6 cross-audit (P1 only). No language-agnostic
  expansion, Trusted Publishing, or `afo_core` split in this release.

## [3.1.6] - 2026-07-16

### Fixed

- **Truth contract for `hyodo check`**: no longer reports `All gates passed` when
  zero gates ran. Unsupported trees exit 2 with `No project gates were executed`
  / `This is not a validation pass`. PASS / FAIL / SKIP / UNSUPPORTED are
  separated (SKIP is not painted as PASS).
- **`hyodo check PATH`**: gates resolve and run against the given path's HyoDo
  checkout root instead of re-probing only `Path.cwd()`.
- **`hyodo safe --strict`**: exits 1 when any high-severity finding is present
  (CI-usable). Default mode remains early-warning exit 0. Missing path exits 2.
- **Legacy `calculate_trinity_score`**: weight sum is normalized so all-ones
  inputs yield 100 (was 95 because weights summed to 0.95).
- **CI false-green**: public `tests/` pytest is a release blocker
  (`continue-on-error` removed). Markdown lint is explicitly advisory.
  Smoke expects empty-directory `hyodo check` exit 2 and `safe --strict`
  high-risk fixture exit 1.

### Changed

- Score CLI/README: review-emphasis percentages are labeled as not used in the
  F formula (`F = sum(1–10 pillars) + geometric mean`).
- `should_auto_approve()` is a deprecation warning wrapper around
  `is_strong_review_signal()` (removal planned for 4.0.0).
- Documented scan limits: directory cap 40 files; default corpus is git
  diff/status when no path is given.

### Notes

- Shipped as **3.1.6** because PyPI already had **3.1.5** when this patch landed.
- GitHub tag `v3.1.6` + PyPI `hyodo==3.1.6` published after merge (measure live if citing).
- No language-agnostic expansion, SARIF, or TruffleHog in this release.

## [3.1.5] - 2026-07-16

### Changed

- Refreshed the demo receipt with explicit pre-commit provenance and current
  public CLI output.
- Made installer headers read `VERSION` when available instead of carrying a
  stale patch number.
- Reconciled release/demo documentation with the live zero-open Dependabot
  alert readback while retaining the historical cleanup context.

## [3.1.4] - 2026-07-16

### Added

- `[tool.pyright] pythonVersion = "3.10"` in `pyproject.toml` so Pyright matches
  `requires-python >=3.10` (avoids PEP 604 false-red when tools default to 3.9).

### Changed

- Score / docs wording: "strong review signal" only — never "proceed immediately"
  or bare "candidate for approval" without human-gate language.
- `QUICK_START.md` rewritten as CLI-first pointer to `QUICK_START_SIMPLE.md`.
- `hyodo safe` action strings: low/caution use human-gate language only.
- `LICENSE.md` points at canonical `LICENSE` (same MIT).
- `PHILOSOPHY.md` rewritten as short HYOGOOK V5 public note.
- Version SSOT and public badges/demo receipts aligned to `3.1.4`.

### Removed

- Empty English-SSOT stub docs (`docs/ARCHITECTURE.md`, JS/TS stub, security-scanning stub).
- Stale tracked `artifacts/sbom` and `memory/` placeholder notes.

## [3.1.3] - 2026-07-16

### Fixed

- `hyodo check` package mode (wheel-only / empty cwd): skip type/lint when no repo checkout,
  so smoke `hyodo check` after `pip install dist/*.whl` exits 0 without dev extras.
- Missing pyright/ruff/pytest soft-skip in package mode; still hard-fail inside a repo.

## [3.1.2] - 2026-07-16

### Fixed

- `hyodo check` runs pyright/ruff/pytest via `sys.executable -m ...` so PATH
  homebrew tools cannot break the Goodness gate with a foreign interpreter.
- `hyodo check` now exits non-zero when any gate fails (demo-safe, CI-safe).

### Added

- `scripts/demo-dry-run.sh` and refreshed demo docs for the v3.1.x public path.
- Unit coverage for CLI tool invocation helpers.

## [3.1.1] - 2026-07-16

### Added

- `scripts/verify-public.sh` — local public package gate (lint, typecheck, tests, build, sdist guard, CLI).
- `scripts/release/check_version_sync.py` and `set_version.py` — VERSION / pyproject / `__init__` SSOT.
- `docs/DEMO_READY_CHECKLIST.md` for post-release demo preflight.
- Model-agnostic provider proof map (`docs/PROVIDER_PROOF.md`).
- Security surface boundary doc (`docs/SECURITY_SURFACE.md`).
- External claim audit with measured evidence (`docs/EXTERNAL_CLAIM_AUDIT.md`).
- Real early-warning safety scanner (`hyodo/safety.py`) used by `hyodo safe`.
- Unit tests for safety helpers (`tests/test_safety.py`).
- Dependabot config for public surface and grouped `afo_core` updates.
- Public API `is_strong_review_signal` (review signal only; not auto-approval).

### Changed

- Public product language is **English-only**. Locale trees (`i18n/ko|zh|ja`) removed.
- Public docs and CLI lead with model-agnostic CLI/CI; Claude Code is optional.
- Primary product framing no longer leads with "cost-aware savings".
- Badge/copy use **tiered routing (intent only)** and state no public savings benchmark.
- Removed public auto-approval language from CLI score/check outputs.
- Hatch **sdist** limited to public package surface (does not ship `afo_core`).
- Pytest/coverage default to public `hyodo` package only.
- afo_core security floors and lock SSOT (poetry.lock only; no requirements double-count).
- afo_core Python range tightened to `>=3.10,<3.14` for litellm compatibility.
- Install scripts rewritten in English; minimal install does not require Docker/Redis/Postgres.
- CI regression guard bans auto-approve phrasing on public surfaces.
- Smoke workflow: dynamic VERSION sync, sdist afo_core guard.
- Documented no-patch Dependabot dismiss policy for diskcache/torch residual.

### Removed

- Japanese, Chinese, and Korean localization trees under `i18n/`.
- Language switcher links from root docs.
- Optional `chromadb` / chroma vector store from afo_core (Qdrant SSOT).
- Optional `mem0ai`, `crewai`, `moviepy` from afo_core dependency solves.
- Repo clutter: stub improvement/migration notes, transplant verifier, kingdom-only
  memory hooks, broken ticket045/validator scripts that pointed at missing `packages/afo-core`.

## [3.1.0] - 2026-05-08

### Added

- Interactive installer and simple quick start path.
- Minimal Docker compose profile for optional extended services.
- HYOGOOK V5 public documentation for optional scoring.

### Changed

- Version alignment to `3.1.0` across package metadata and badges.
