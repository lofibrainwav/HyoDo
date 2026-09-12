# HyoDo current state

Snapshot: 2026-09-11 PT

This file separates the latest public package from newer work already landed on `main`.
It intentionally does **not** hard-code its own commit SHA: a self-referential SHA becomes
stale the moment this file is updated. Use the repository `main` ref, a release receipt,
or a measured runtime-identity receipt when an exact revision is required.

- Canonical source branch: `main`
- Latest public package: HyoDo `4.19.2`
- Phase 0: CLOSED; Evidence Pack v1 is sealed with named residuals.
- Active closure program: #263 HyoDo Final Closure.

## Current truth

| Capability | Public 4.19.2 | Current main / measured state |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; no collector/uploader |
| MCP stdio, loopback, private Tailscale | SHIPPED | SHIPPED |
| canonical runtime identity v1 | not in 4.19.2 | SHIPPED; `/api/identity` + receipt contract, KINGDOM consumer merged |
| Codex host adapter | SHIPPED | SHIPPED plus newer landed fixes |
| installed Codex callback | release-era claim UNOBSERVED | historically OBSERVED in an isolated real-host run |
| current canonical Codex canary receipt | UNOBSERVED | UNOBSERVED until a fresh receipt is sealed |
| Codex output digest | not in 4.19.2 | LANDED and OBSERVED |
| Codex causal call/result parent | not in 4.19.2 | LANDED and OBSERVED |
| Codex model provenance | not in 4.19.2 | LANDED and OBSERVED |
| Cursor live callback | UNOBSERVED | UNOBSERVED |
| orchestration observation ingest | not in 4.19.2 | LANDED |
| KINGDOM serial/parallel stage readback | not in 4.19.2 | OBSERVED |
| sidecar replay idempotency | not in 4.19.2 | LANDED and verified |
| unstated attempt stays unknown | not in 4.19.2 | LANDED and verified |
| Graph v2 multi-parent runtime | NOT BUILT | NOT BUILT; SCC oracle/fixtures only |
| Information Flow Attestation v0 | RESEARCH | contract/fixture lane OPEN (#229) |
| ACL / Wisdom Reflex automatic routing | RESEARCH | RESEARCH / shadow only |
| public remote MCP | CONTRACT ONLY | CONTRACT ONLY / UNOBSERVED |
| friction collector/uploader | NOT BUILT | NOT BUILT |

## Ownership invariant

- KINGDOM executes and orchestrates.
- EROS / host policy owns execution authority.
- Evidence Gate judges completion evidence.
- ACL makes shadow recommendations.
- HyoDo observes, records, validates, attests and measures.

Capability existence is not run usage. Missing evidence is not green. Research is not shipped capability evidence.

## Final-closure priority

1. Eliminate SSOT/release drift and audit-loss ambiguity.
2. Govern and publish the landed post-4.19.2 work as the next public release.
3. Dogfood the public package from KINGDOM rather than a source checkout.
4. Finish Graph v2 multi-parent semantics/runtime for honest fork/join measurement.
5. Finish IFA v0 contract/fixtures/local readback without acquiring execution authority.
6. Run the final regression/convergence suite.
7. Complete matched KINGDOM/ACL shadow A/B and record the result.
8. Resolve remaining host/transport scope explicitly and enter maintenance mode.
