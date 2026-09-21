# HyoDo current state

Public release readback: 2026-09-20 PT
Runtime capability matrix below: measured 2026-09-13 PT, before 4.19.6.

This file separates shipped product capability from live/runtime observation. Exact
revision identity belongs in the signed release, CI receipt, or runtime identity
receipt rather than in this self-referential page.

- Canonical source branch: `main`
- Latest public package: HyoDo `4.20.2`
- Public release chain: CLOSED — signed tag, GitHub Release + SBOM, PyPI OIDC
  provenance, and install smoke verified in
  [`releases/4.20.2.md`](./releases/4.20.2.md).
- Phase 0: CLOSED; Evidence Pack v1 remains sealed with named residuals.
- HyoDo product status: the recorded 4.20.2 release is closed. Post-release
  research and integration have separate evidence and promotion criteria;
  they do not silently reopen the sealed public artifact. Live-host and
  orchestration experiments remain downstream integration/research work.

The HyoDo/Kingdom ownership and status-separation contract is maintained in
[`PRODUCT_BOUNDARY.md`](./PRODUCT_BOUNDARY.md). Kingdom processes, tests,
branches, and worktrees must not be folded into HyoDo closeout status.

## 4.20.2 release update

HyoDo 4.20.2 publishes the lens-reconciliation correctness fix from #441:
tool names, metadata tags, and an `output_digest` alone are not treated as
measured lens semantics. The frozen 9,621-event reconciliation therefore keeps
unsupported semantics visible rather than promoting compatibility placement to
evidence. The measured release chain is recorded in
[`releases/4.20.2.md`](./releases/4.20.2.md), and the reconciliation receipt is
[`reconciliation receipt`](research/EVIDENCE_RECONCILIATION_2026-09-20.md).

Graph v2, bounded host-supplied requirement comparison, and the prior release
capabilities remain available. Natural-language intent extraction and
separately stored occurrence, observation, and recording timestamps are not
implemented. Fresh Codex or Cursor host observations remain deployment-specific;
the matrix below is historical.

## Runtime capability snapshot (2026-09-13 PT)

| Capability | Public 4.19.5 at snapshot | Main / measured state at snapshot |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; no collector/uploader |
| MCP stdio, loopback, private Tailscale | SHIPPED | SHIPPED |
| canonical runtime identity v1 | SHIPPED | SHIPPED; `/api/identity` + receipt contract, reference-host consumer merged |
| MCP access-audit readback | SHIPPED | SHIPPED; operation outcome and `audit.state` are separate, audit loss is fail-visible |
| release-note drift verifier | SHIPPED | SHIPPED; repository notes are canonical, remote-unavailable is UNOBSERVED, mutation is explicit + readback verified |
| Codex host adapter | SHIPPED | SHIPPED; fresh canonical live canary remains UNOBSERVED |
| Codex output digest / causal parent / model provenance | SHIPPED | SHIPPED; historically observed, fresh canonical host receipt remains separate evidence |
| Cursor host adapter | SHIPPED | SHIPPED; fresh live callback remains UNOBSERVED |
| orchestration observation ingest | SHIPPED | SHIPPED |
| Graph v2 multi-parent runtime | SHIPPED | SHIPPED; deterministic multi-parent read/normalize/export/viewer + Tarjan SCC with v1 compatibility |
| Information Flow Attestation v0 | SHIPPED | SHIPPED observer-only; privacy lineage stays separate and non-authoritative |
| Adaptive support-allocation experiments | RESEARCH | Downstream research / shadow only |
| public remote MCP | CONTRACT ONLY | CONTRACT ONLY / UNOBSERVED |
| friction collector/uploader | NOT BUILT | NOT BUILT |

## Ownership invariant

- The integrating host executes and orchestrates.
- Host authorization policy owns execution authority.
- Evidence Gate judges completion evidence.
- Downstream research may make non-authoritative shadow recommendations.
- HyoDo observes, records, validates, attests and measures.

Capability existence is not run usage. Missing evidence is not green. Research is not shipped capability evidence.

## Maintenance boundary

The runtime matrix above compares public 4.19.5 with the source state measured
on 2026-09-13; it is a historical snapshot, not a fresh runtime readback for
4.20.2. The 4.20.2 release-chain receipt is recorded separately above. Do not
infer runtime identity from this page alone; use the signed release, CI receipt,
or runtime identity receipt. Fresh
Codex/Cursor host observations,
QMD/Neo4j closed-loop memory, and matched support-allocation/host shadow experiments are
downstream integration/research work and must not silently reopen HyoDo product
authority or rewrite sealed release evidence.
