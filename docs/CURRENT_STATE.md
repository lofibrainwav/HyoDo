# HyoDo current state

Snapshot: 2026-09-11 PT

This file separates the latest public package from newer work already landed on `main`.

- Current reconciliation SHA: `8f6bf23a9bfa5fb6eb6eb804335d9d864aa50a82`
- Latest public package: HyoDo `4.19.2`
- Phase 0: CLOSED; Evidence Pack v1 is sealed with named residuals.
- Active phase: Phase 1 observation and passive-shadow seams.

## Current truth

| Capability | Public 4.19.2 | Current main / measured state |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; no collector/uploader |
| MCP stdio, loopback, private Tailscale | SHIPPED | SHIPPED |
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

## Immediate priority

1. Keep public-release claims separate from current-main claims.
2. Reconcile roadmap, issues, README and site whenever measured state changes.
3. Govern and publish the landed post-4.19.2 fixes as the next release.
4. Use the public package as KINGDOM's canonical dogfood dependency.
5. Finish Graph v2 multi-parent semantics/runtime for honest fork/join measurement.
6. Run ACL/KINGDOM matched shadow A/B after the evidence contracts freeze.
7. Promote only independently verified improvements.
