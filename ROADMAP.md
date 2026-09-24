# HyoDo roadmap

This roadmap describes direction, not a delivery promise. Work is accepted only
when implementation, tests, documentation, and release evidence agree.

## Current public baseline

HyoDo 4.21.5 is the latest published release. Its signed tag, GitHub Release,
SBOM receipt, PyPI provenance, and install readback are recorded in
`docs/releases/4.21.5.md`. Prior release receipts remain preserved under
`docs/releases/` and are not rewritten by this release.

## Current release

HyoDo 4.21.7 is the current release target and source-tree release baseline.
Its signed tag, GitHub Release + SBOM, PyPI provenance, and install smoke are
measured in `docs/releases/4.21.5.md`. HyoDo 4.21.2 remains an incomplete immutable
historical release whose GitHub Release was published without SBOM evidence
and never reached PyPI (`docs/releases/4.21.2.md`).
This does not establish every host integration.
HyoDo 4.19.6 remains an immutable prior release whose receipt records the
dashboard startup-readiness fix; 4.19.5 and 4.19.4 are earlier immutable
releases.

Public release evidence does not imply that any particular Codex or Cursor host
is connected right now. Host observation is deployment-specific; adapter
fixtures, local ledgers, and package publication remain separate evidence
axes.

Landed and released:

- `hyodo safe` for early-warning scans with strict and JSON modes.
- Bring-Your-Own-Gates with `hyodo init` and `hyodo check`.
- FDE evidence spine with event validation, append-only audit records, and
  local policy checks.
- Schema validation, local eval runs, and deterministic evidence reports.
- MCP M1-M4: stdio, loopback/private Tailscale serve, `mcp doctor`, access
  ledger, and agent-rules opt-in.
- Python 3.10-3.14 CI coverage plus a pinned MCP SDK v1 compatibility lane.
- PyPI Trusted Publishing with post-publish provenance and install readback.

The public package remains local-first and model-agnostic. Missing or unreadable
evidence is not converted into a pass.

## Current focus

### 4.20.0 (released 2026-09-19)

- Preserve graph participants and explicit From/To relationships.
- Show bounded, host-supplied intent comparisons with evidence references.
- Keep temporal storage expansion and automatic intent extraction unimplemented.
- Verify publication and installation separately from source and site delivery.

### 4.20.1 (released 2026-09-20)

- Preserve host-supplied Codex model and tool-result observations without
  inferring terminal outcomes or authority.
- Keep evidence-graph, verification-view, public-boundary, and release claims
  aligned with measured source and host evidence.
- Release chain measured: verified tag, GitHub Release + SBOM, PyPI provenance,
  and install smoke are recorded in `docs/releases/4.20.1.md`.

### 4.20.2 (released 2026-09-20)

- Tighten lens reconciliation so tool names, metadata tags, and an output digest
  alone never count as measured lens semantics.
- Require explicit paths, URLs, method, or policy-rule evidence before a tool
  event can be counted as `MAPPED`; preserve legacy viewer placement only as
  compatibility presentation.
- Preserve the immutable 4.20.1 artifacts; this correction is published only
  under 4.20.2.
- Release chain measured: verified tag, GitHub Release + SBOM, PyPI provenance,
  and install smoke are recorded in `docs/releases/4.20.2.md`.

### 4.21.0 (released 2026-09-22)

- Report gate coverage beside the gate verdict: `hyodo check` now emits
  `coverage` (FULL/PARTIAL/NONE), `complete`, and `effective` so one passing
  gate beside one skipped gate no longer reads as `HYODO PASS`.
- Preserve the 4.20 machine contract exactly: exit codes and the existing JSON
  keys (`status`, `gates_ran`, `gates_total`, `failed`) are unchanged, and the
  new keys are additive.
- Downgrade `effective` to UNOBSERVED when measurement provenance is MISMATCH
  or UNOBSERVED, without altering the 4.20 `status` semantics for either case.
- Report how a BYOG command set came to be trusted (`trust.via`) and whether
  its receipt persisted (`trust.persistence`); a receipt that cannot be stored
  is surfaced instead of being charged to a gate result.
- Stop printing the trust-bypass environment variable in the refusal text, show
  the exact commands that were refused, and report an unrecorded previous
  command set as UNOBSERVED rather than describing it.
- Separate "a project file exists" from "a supported tool was detected", and
  stop writing a live `.hyodo/gates.toml` when nothing was detected, so the
  built-in sampled fallback survives a zero-detection `hyodo init`.

### 4.21.1 (released 2026-09-22)

- Align top-level `hyodo --version` with the canonical public product identity.
- Make the post-publish install verifier reject stale identity wording instead
  of accepting any output that merely contains the expected version number.
- Preserve all 4.21.0 check status, exit-code, coverage, trust, and provenance
  semantics unchanged.

### 4.21.7 (security release, 2026-09-23)

- Move operator authority state out of the checkout: gate approvals, policy
  trust grants, pairing records, scan-exception approvals, and ledger origin
  anchors live in per-user state bound to the workspace path; same-named
  checkout files carry no authority. Contract: `docs/TRUST_BOUNDARY.md`.
- `hyodo safe` with nothing observed is `UNOBSERVED`, not `PASS`; sampled
  `hyodo check` reports `project_coverage: SAMPLED` and `complete: false`.
- Hostile-clone gauntlet against the built wheel is a required release gate.

### 4.21.6 (GitHub Release only, 2026-09-23; superseded by 4.21.7)

PyPI publication was withheld at the environment approval; 4.21.7 carries
these changes.

- Ship the retired-reader registration GC from #477: before a new MCP reader
  registers, records whose PID/process-start identity is provably retired
  (SIGTERM, SIGKILL, crash, reboot) are removed; an unobservable identity is
  never treated as dead. Closes the deployed-runtime gap where 4.21.5 kept
  collecting registration residue after an unclean reader exit.
- Release candidate planning accepts both coherent states (`UNPREPARED` and
  `PREPARED`) instead of rejecting a fully prepared candidate.

### 4.21.5 (released 2026-09-23)

- Make runtime promotion observable: MCP readers self-register and
  `hyodo mcp census` reports `PROMOTION_COMPLETE` only when no stale or
  unregistered reader is live.
- Stale readers (moved root, replaced or unreadable code) refuse measurement
  tools with `STALE_RUNTIME_RECONNECT_REQUIRED`; HyoDo still never restarts or
  kills a reader, and the host keeps promotion authority.
- Release chain measured 9/9 OBSERVED in `docs/releases/4.21.5.md`.

### 4.21.4 (released 2026-09-23)

- Close the installed-wheel provenance false green: source identity is proved
  from the measuring package's actual `hyodo/` content instead of an enclosing
  repository commit.
- Keep real source drift `MISMATCH` / `effective=UNOBSERVED` while allowing a
  byte-identical installed wheel to remain observed regardless of venv location.
- Carry the zero-detection `hyodo init` documentation correction already landed
  on main; no execution-authority or policy semantics change.
- Release chain measured 9/9 OBSERVED in `docs/releases/4.21.4.md`.

### 4.21.3 (released 2026-09-22)

- Republishes the 4.21.2 content plus the publication-order fix from #463
  through the corrected pipeline; the release pipeline owns publication as a
  strictly linear state chain and refuses wrong order.
- Changes no product or CLI semantics beyond #463; 4.21 status, coverage, and
  exit-code contracts are unchanged.
- Publication steps measured and sealed in `docs/releases/4.21.3.md`
  (9/9 OBSERVED, 2026-09-22).

### 4.21.2 (incomplete immutable historical release)

- Make the documented public verifier work from a pipless uv-created project venv.
- Bound test-integrity language to syntax the AST heuristic actually recognizes.
- Separate `--max-files` cap gaps from non-text/binary safety-scan gaps.
- Keep unchanged release-chain readback zero-write instead of churning receipt time.
- Run the built-artifact description check in public verification, and make the
  public-language gate reject bare virtue-syllable prose and require the canonical
  trilingual label form.
- Preserve all 4.21.0/4.21.1 status, exit-code, coverage, trust, and provenance
  semantics.

### External adoption

- Keep the README and Quick Start centered on adopter tasks, not internal terms.
- Preserve clear install, exit-code, support, and security boundaries.
- Keep PyPI metadata aligned with the GitHub product description.

### Release honesty

- Keep the protected final release check non-skippable when upstream jobs fail.
- Preserve Python and MCP compatibility coverage as release evidence.
- Keep documentation claims tied to measured CI and published artifacts.

### Evidence integrity

- Keep policy decisions separate from caller assertions.
- Preserve fail-closed handling for unreadable ledgers and invalid inputs.
- Keep default agent-event storage digest-only unless an operator explicitly
  permits more.

### 4.13.0 (released)

- Machine-readable `hyodo check` results for CI consumers landed on main.

- Policy ASK and the trust ladder are live on main, with explicit operator
  grants and fail-closed `UNOBSERVED` handling.
- Keep the seven version-bearing sources synchronized during release prep.

### 4.14.0 (released 2026-09-07)

- Phase 1 packages 1-B through 1-E (graph edges, digest-only URLs, mission
  detection, test integrity) landed on main.
- Local evidence-graph viewer: `hyodo dashboard` serves `/graph`, reading the
  real agent-event ledger.
- Audience profiles (`--audience vibe|engineer|professional`) change
  presentation wording only; decisions, exit codes, and evidence references
  stay byte-identical.
- M5-A machine-readable remote connector contract and the M5-B local bridge
  with a pairing lifecycle landed on main.
- `hyodo connect` dry-run-by-default harness wiring for Claude Code hooks,
  `pre-commit`, and GitHub Actions, with `--shadow` mode and `--status` drift
  reporting.

### 4.15.0 (released 2026-09-07)

- M5-C onboarding (`hyodo mcp config <host>`, guided `hyodo start`) and M5-D
  continuity receipt (`hyodo mcp continuity`) closed issue #163.
- Stage 2 packages on the source line: `hyodo skills ingest|lens|propose`
  (skill files consumed as a lens over the six pillars, ingestion gated as a
  supply-chain external variable), `hyodo inspect` (digest-only folder and
  chunk manifests, connector-supplied remote inventories recorded as claims),
  `hyodo graph export` (backlinks and pillar clusters) with actor rings and
  derived actor roles in the local viewer, and `hyodo eye capture|verify`
  (ephemeral visual evidence with an existence and destruction pair).
- Embeddings, model calls, and screen capture tools stay outside HyoDo: the
  package records digests, hashes, and receipts only.

### 4.16.0 (released 2026-09-07)

- `hyodo check` derives a real Benevolence signal from onboarding evidence
  (`hyodo/dx_signals.py`) instead of reporting it `UNOBSERVED`; `hyodo score
  --from-check` derives all five HyoDo Integrity Score pillar inputs
  in-process from `check`/`safe`/test-integrity, with per-pillar
  `OBSERVED`/`PARTIAL`/`UNOBSERVED` coverage.
- Shadow mode's "always exits 0, nothing is blocked" guarantee now holds on
  every early exit in `hyodo policy check --shadow` and `hyodo event record
  --shadow`; `hyodo connect claude-code` bootstraps a starter
  `.hyodo/policy.toml` when none exists.
- `hyodo safe` reports `scope` and `coverage` alongside `source`; the
  gitleaks and trufflehog scan adapters gain version positive controls
  against silent CLI drift.
- `hyodo mcp continuity` counts hook-recorded actors as their own hosts, so
  a hook-only onboarding (no MCP client ever connected) can reach
  `OBSERVED`/`READY` instead of being stuck at `hosts observed: 0/2`.

### 4.18.0 (released 2026-09-10)

- Sampled syntax checks disclose their bounded scope in normal, quiet, and JSON
  output.
- Public release evidence is complete: signed tag, GitHub Release, SBOM and
  checksum assets, PyPI OIDC provenance, and clean-install smoke.
- The local evidence graph preserves call/result lanes, parent/evidence edges,
  parallel clusters, and the explicit `UNOBSERVED` boundary.
- KINGDOM native Measured Run #3 was recorded through the public package and
  sealed as Evidence Pack v1. The pack is observation evidence, not execution
  authority.

### 4.19.0 (released 2026-09-10)

- Evidence-root dashboard review is explicit and graph-only: gates, safety, and
  history remain `UNOBSERVED`.
- Optional event timing is preserved without inventing missing duration.
- JSONL ledger readers stream input while preserving corrupt-line and unreadable
  ledger semantics.

### 4.19.1 (released 2026-09-10)

- Cursor and Codex host adapters normalize native tool-hook payloads into
  canonical `hyodo.agent-event/v1` observation, preserving privacy-minimized
  argument, output, and path digests.
- Platform contract, adapter verification, and live-canary status are recorded
  as separate provenance axes, so a passing fixture is never read as a live
  host callback.

### 4.19.2 (released 2026-09-10)

- One host tool call now leaves both of its canonical events. `tool_call` and
  `tool_result` derived from the same `tool_use_id` carry distinct `event_id`s
  qualified as `{host}:{event_name}:{tool_use_id}`; a bare tool id had made the
  second half an `event_id` conflict, and the ledger dropped it in silence.
- Release chain receipts ask whether a version is on PyPI rather than whether
  it is the newest, so a receipt stops decaying when the next release ships.

### 4.19.3 (released 2026-09-11)

- Final closure release for the post-4.19.2 source line.
- Graph v2 multi-parent DAG normalization/export/viewer support.
- Information Flow Attestation v0 as observer-only privacy-lineage surface.
- Canonical runtime identity v1 schema/pin bytes in public wheel, sdist, and site.
- MCP access-audit write/read loss is fail-visible as `UNOBSERVED`.
- Release-note drift has a read-only verifier; the sdist guard validates declared
  package scope instead of enforcing a brittle compressed-byte ceiling.

### 4.19.4 (released 2026-09-12)

- Adds the bounded `provenance.retrieval/v1` carrier for KINGDOM/QMD retrieval
  provenance, with deterministic digests and projection IDs.
- Keeps raw retrieval bodies, queries, prompts, authority, and approval out of
  the HyoDo event ledger; local and public release evidence remain separate.

### 4.19.5 (released 2026-09-13)

- Republishes the corrected public sdist scope under a new immutable patch
  version; the 4.19.4 artifact is not overwritten.
- Closes the source-build to PyPI artifact hash/readback chain after the
  release workflow's provenance and install checks pass.

### 4.19.6 (released 2026-09-15)

- Includes the dashboard startup-readiness and test-gate reporting fix merged
  in PR #343. The measured release chain receipt is `docs/releases/4.19.6.md`.

### 4.19.7 (released 2026-09-16)

- Adds the evidence-only `hyodo skill-eval` oracle (PR #358) and the dashboard
  `Not measured` fix (PR #357). The measured release chain receipt is
  `docs/releases/4.19.7.md`.

### 4.19.9 (release preparation)

- Publishes the storefront repairs from the 2026-09-19 first-visit audit: the
  project description's links resolve off GitHub, the optional MCP extra names
  an install path for each installer, and the homepage hero keeps its copy in
  normal flow.
- Changes no runtime behaviour; CLI contracts, exit codes, and evidence
  semantics are unchanged from 4.19.8.
- The website half of the audit repairs is already served; the published
  package half stays `UNOBSERVED` until the post-publish description readback
  runs.

### 4.19.8 (release preparation)

- Synchronizes the six version-bearing sources and PATH-installed HyoDo CLI.
- Adds a read-only runtime-slot GC classifier that protects active, pinned, and
  dirty-unique HyoDo/KINGDOM runtime artifacts.
- Public publication, signing, and live-runtime promotion remain unobserved
  until their independent receipts and readbacks exist.

## Next candidates

These items require an issue, explicit scope, and acceptance tests before
implementation:

- Improve `safe` rule precision and document known false positives.
- Add an optional measured second-device MCP receipt without making it a
  requirement for local-client use.
- Evaluate an index for large event ledgers instead of full-ledger scans.
- Decide whether the advisory public SBOM should become a release blocker.
- Add stronger release-signing guidance for annotated Git tags.
- Measure any routing or cost guidance before making savings claims.

## Landed milestones

- **v4.4.0** — FDE Phase 1 evidence spine: agent events + policy gate.
- **v4.8.x** — security and observability honesty hardening.
- **v4.9.0** — MCP SDK v1/v2 dual-major compatibility.
- **v4.10.0** — `hyodo mcp doctor`.
- **v4.11.0** — MCP access ledger + agent-rules opt-in; M4 complete.
- **v4.12.0** — release-trust seal: verified-tag gate, SBOM evidence,
  SARIF output, pre-commit hooks, composite GitHub Action.

## Later exploration

- Additional language and repository adapters.
- A plugin API for custom gates.
- Optional browser or service integrations outside the core CLI.
- Optional hash-chain or at-rest encryption for agent events with a clear key
  management story.
- Exportable audit packs beyond the current local HTML/Markdown report.

Exploration does not imply support or a release date. The public package should
remain useful without optional services, model providers, or agent interfaces.

## Proposing roadmap work

Open an [issue](https://github.com/lofibrainwav/HyoDo/issues) describing:

1. the user problem;
2. why existing commands do not solve it;
3. the smallest verifiable change;
4. compatibility and security risks;
5. measurable acceptance criteria.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the development workflow.
