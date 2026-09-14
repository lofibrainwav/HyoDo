# HyoDo current state

Snapshot: 2026-09-13 PT

This file separates shipped product capability from live/runtime observation. Exact
revision identity belongs in the signed release, CI receipt, or runtime identity
receipt rather than in this self-referential page.

- Canonical source branch: `main`
- Current source candidate: HyoDo `4.19.6`, based on fresh-main `af028c62b075580830ad418614cb172af5e5e7a2`
- Latest public package: HyoDo `4.19.5`
- Public release chain: CLOSED — signed tag, GitHub Release + SBOM, PyPI OIDC provenance, neutral-cwd install smoke, and hosted runtime-identity schema readback verified.
- Phase 0: CLOSED; Evidence Pack v1 remains sealed with named residuals.
- HyoDo product status: release closure complete; remaining live-host and orchestration experiments are downstream integration/research work.

The HyoDo/Kingdom ownership and status-separation contract is maintained in
[`PRODUCT_BOUNDARY.md`](./PRODUCT_BOUNDARY.md). Kingdom processes, tests,
branches, and worktrees must not be folded into HyoDo closeout status.

## Current truth

| Capability | Public 4.19.5 | Current main / 4.19.6 candidate |
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
| admission observation v1 / CLI | NOT IN 4.19.5 | CANDIDATE; execution remains UNOBSERVED |
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

HyoDo 4.19.5 is the closed public baseline. The current source candidate is
4.19.6; it is not published and must not be inferred as a public artifact. Do
not infer runtime identity from this page alone;
use the signed release, CI receipt, or runtime identity receipt. Fresh
Codex/Cursor host observations,
QMD/Neo4j closed-loop memory, and matched ACL/KINGDOM shadow experiments are
downstream integration/research work and must not silently reopen HyoDo product
authority or rewrite sealed release evidence.
