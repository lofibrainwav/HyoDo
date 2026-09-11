# HyoDo roadmap

This roadmap describes direction, not a delivery promise. Work is accepted only
when implementation, tests, documentation, and release evidence agree.

## Current public baseline

HyoDo 4.19.2 is the latest published release after the public 4.18.0 measured
run. The 4.18.0 signed tag, public wheel and sdist, SBOM receipt, PyPI
provenance, clean-install readback, and Evidence Pack v1 remain sealed. Every
release in the 4.19.x line carries its own measured chain receipt under
`docs/releases/`: signed tag, GitHub Release, exact tag SBOM evidence, PyPI
OIDC provenance, and post-publish install readback.

Live Cursor and Codex callback observation remains `UNOBSERVED`. The host
adapters are fixture-verified and the two-event recording path is measured on
the published artifact, but no installed host has been observed emitting into
a ledger.

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
