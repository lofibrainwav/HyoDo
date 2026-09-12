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
| MCP access-audit readback | not in 4.19.2 | SHIPPED; operation outcome and `audit.state` are separated, audit loss is fail-visible |
| release-note drift verifier | not in 4.19.2 | SHIPPED; repository notes are canonical, remote-unavailable is UNOBSERVED, mutation is explicit + readback verified |
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
| Graph v2 multi-parent runtime | NOT BUILT | SHIPPED on `main`; v2 multi-parent read/normalize/export/viewer, Tarjan SCC, v1 writer/readback compatibility; #222 closed |
| Information Flow Attestation v0 | RESEARCH | SHIPPED observer-only on `main`; privacy lineage is separate from causal/evidence edges and grants no authority; #229 closed |
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

1. Run and seal the final regression/convergence review (#224) against the now-frozen Graph v2 and IFA contracts.
2. Reconcile CHANGELOG/version/release notes and publish the landed post-4.19.2 work as the next governed public release.
3. Dogfood that public package from KINGDOM rather than a source checkout and seal the clean-install receipt.
4. Complete matched KINGDOM/ACL shadow A/B (#225) and record the result, including a null result if that is what evidence shows.
5. Resolve remaining host/transport scope explicitly: fresh Codex canary; Cursor/remote MCP observed or explicitly out of scope.
6. Close the meta/final-closure issues and enter maintenance mode with no ambiguous production debt.
