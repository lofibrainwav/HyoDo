# HyoDo docs index

Public, English-first documentation. Prefer these over root historical notes.

Current public version: see the root `VERSION` source of truth. HyoDo preserves
explicit `check` and `safe` exit contracts; model-agnostic does not mean
language-agnostic.

`hyodo dashboard` now also serves `GET /graph`, a local evidence-graph viewer
(five fixed virtue columns plus a core-engine-pulse orb) rendered live from
`.hyodo/agent-events.jsonl`; `GET /api/graph` returns the same
`hyodo.evidence-graph/v1` JSON `hyodo report --format graph` writes.

## Start here

| Doc | Purpose |
| --- | --- |
| [../README.md](../README.md) | Product overview + exit contracts |
| [../QUICK_START.md](../QUICK_START.md) | Install + CLI path |
| [ONBOARDING.md](./ONBOARDING.md) | `hyodo start` first-use flow, MCP host table, `hyodo mcp config` |
| [PROVIDER_PROOF.md](./PROVIDER_PROOF.md) | Model-agnostic provider map |
| [SECURITY_SURFACE.md](./SECURITY_SURFACE.md) | Public security surface |
| [POLICY_TRUST.md](./POLICY_TRUST.md) | Policy trust ladder and levels |
| [CONNECT.md](./CONNECT.md) | `hyodo connect` — harness wiring (Claude Code hooks, pre-commit, GitHub Actions) and shadow mode |
| [SKILLS.md](./SKILLS.md) | `hyodo skills ingest` / `lens` / `propose` — skill lens over the six pillars |
| [INSPECT.md](./INSPECT.md) | `hyodo inspect` — field-deployment folder absorption, digests and chunks |
| [GRAPH_EXPORT.md](./GRAPH_EXPORT.md) | `hyodo graph export` — evidence-graph export bridge and actor rings |
| [EYE.md](./EYE.md) | `hyodo eye capture` / `verify` — ephemeral visual evidence, no pixels stored |
| [AUDIENCE.md](./AUDIENCE.md) | `--audience` profiles (vibe / engineer / professional) — wording only, same decision |
| [TEST_INTEGRITY.md](./TEST_INTEGRITY.md) | `hyodo check --strict-tests` — AST-based test-integrity scan |
| [SCORE_DERIVATION.md](./SCORE_DERIVATION.md) | `hyodo score --from-check` — pillar derivation rule table and coverage semantics |
| [HYODO_MCP_CONNECTOR_DESIGN.md](./HYODO_MCP_CONNECTOR_DESIGN.md) | MCP connector design, plus M1 local stdio (remote not shipped) |
| [CODEX_HANDOFF_NEXT.md](./CODEX_HANDOFF_NEXT.md) | Implementer queue after 4.4.0 |
| [EXTERNAL_CLAIM_AUDIT.md](./EXTERNAL_CLAIM_AUDIT.md) | External claim evidence |

## Release and demo (demo last)

| Doc | Purpose |
| --- | --- |
| [../RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) | Release readiness |
| [DEMO_SCRIPT_3_MIN.md](./DEMO_SCRIPT_3_MIN.md) | Recording script (after verify) |
| [DEMO_READY_CHECKLIST.md](./DEMO_READY_CHECKLIST.md) | Pre-record gates |
| [SCAN_EXCEPTIONS.md](./SCAN_EXCEPTIONS.md) | Auditable local scan exceptions |
| [../scripts/demo-dry-run.sh](../scripts/demo-dry-run.sh) | Local demo receipt script |

## Optional

| Doc | Purpose |
| --- | --- |
| [ANTHROPIC_PROOF.md](./ANTHROPIC_PROOF.md) | Claude-specific adapter map |
