# HyoDo current state

Public release readback: 2026-09-15 PT
Runtime capability matrix below: measured 2026-09-13 PT, before 4.19.6.

This file separates shipped product capability from live/runtime observation. Exact
revision identity belongs in the signed release, CI receipt, or runtime identity
receipt rather than in this self-referential page.

- Canonical source branch: `main`
- Latest public package: HyoDo `4.19.6`
- Public release chain: CLOSED — signed tag, GitHub Release + SBOM, PyPI OIDC provenance, and install smoke verified in [`releases/4.19.6.md`](./releases/4.19.6.md).
- Phase 0: CLOSED; Evidence Pack v1 remains sealed with named residuals.
- HyoDo product status: release closure complete; remaining live-host and orchestration experiments are downstream integration/research work.

The HyoDo/Kingdom ownership and status-separation contract is maintained in
[`PRODUCT_BOUNDARY.md`](./PRODUCT_BOUNDARY.md). Kingdom processes, tests,
branches, and worktrees must not be folded into HyoDo closeout status.

## 4.19.6 release update

HyoDo 4.19.6 is the current public package. It adds explicit dashboard startup
states and records pytest skip and expected-failure reasons. It also clarifies
HyoDo's public positioning and its boundary with host action authorization.
The release does not claim fresh Codex or Cursor host observations; those
remain `UNOBSERVED` as described in the measured matrix below.

## Runtime capability snapshot (2026-09-13 PT)

| Capability | Public 4.19.5 at snapshot | Main / measured state at snapshot |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; no collector/uploader |
| MCP stdio, loopback, private Tailscale | SHIPPED | SHIPPED |
| canonical runtime identity v1 | SHIPPED | SHIPPED; `/api/identity` + receipt contract, KINGDOM consumer merged |
| MCP access-audit readback | SHIPPED | SHIPPED; operation outcome and `audit.state` are separate, audit loss is fail-visible |
| release-note drift verifier | SHIPPED | SHIPPED; repository notes are canonical, remote-unavailable is UNOBSERVED, mutation is explicit + readback verified |
| Codex host adapter | SHIPPED | SHIPPED; fresh canonical live canary remains UNOBSERVED |
| Codex output digest / causal parent / model provenance | SHIPPED | SHIPPED; historically observed, fresh canonical host receipt remains separate evidence |
| Cursor host adapter | SHIPPED | SHIPPED; fresh live callback remains UNOBSERVED |
| orchestration observation ingest | SHIPPED | SHIPPED |
| Graph v2 multi-parent runtime | SHIPPED | SHIPPED; deterministic multi-parent read/normalize/export/viewer + Tarjan SCC with v1 compatibility |
| Information Flow Attestation v0 | SHIPPED | SHIPPED observer-only; privacy lineage stays separate and non-authoritative |
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

## Maintenance boundary

The runtime matrix above compares public 4.19.5 with the source state measured
on 2026-09-13; it is not a fresh runtime readback for 4.19.6. The 4.19.6
release-chain receipt is recorded separately above. Do not infer runtime
identity from this page alone; use the signed release, CI receipt, or runtime
identity receipt. Fresh
Codex/Cursor host observations,
QMD/Neo4j closed-loop memory, and matched ACL/KINGDOM shadow experiments are
downstream integration/research work and must not silently reopen HyoDo product
authority or rewrite sealed release evidence.
