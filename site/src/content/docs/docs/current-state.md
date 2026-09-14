---
title: Current state
description: Public release, current main, and measured HyoDo state separated by evidence boundary.
---

# HyoDo current state

Snapshot: **2026-09-13 PT**.

HyoDo **4.19.5** is the closed public baseline. Product capability and live host
observation remain separate evidence axes.

- Canonical source branch: **`main`**
- Current source candidate: **4.19.6**, based on fresh-main `af028c62b075580830ad418614cb172af5e5e7a2`
- Latest public package: **4.19.5**
- Release chain: **CLOSED** — signed tag, GitHub Release + SBOM, PyPI provenance,
  neutral-cwd install smoke, and hosted runtime-identity schema readback verified.
- Phase 0: **CLOSED**; Evidence Pack v1 remains sealed with named residuals.

| Capability | Public 4.19.5 | Current main / 4.19.6 candidate |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; local only |
| MCP stdio / loopback / private Tailscale | SHIPPED | SHIPPED |
| canonical runtime identity v1 | SHIPPED | SHIPPED; `/api/identity` + receipt contract |
| MCP access-audit readback | SHIPPED | SHIPPED; audit loss is fail-visible |
| release-note drift verifier | SHIPPED | SHIPPED; mutation requires explicit apply + readback |
| Codex host adapter | SHIPPED | SHIPPED; fresh canonical live canary remains UNOBSERVED |
| Cursor host adapter | SHIPPED | SHIPPED; fresh live callback remains UNOBSERVED |
| orchestration observation ingest | SHIPPED | SHIPPED |
| admission observation v1 / CLI | NOT IN 4.19.5 | CANDIDATE; execution remains UNOBSERVED |
| Graph v2 multi-parent runtime | SHIPPED | SHIPPED; deterministic multi-parent graph with v1 compatibility |
| Information Flow Attestation v0 | SHIPPED | SHIPPED observer-only; non-authoritative |
| ACL / Wisdom Reflex automatic routing | RESEARCH | RESEARCH / shadow only |
| public remote MCP | CONTRACT ONLY | CONTRACT ONLY / UNOBSERVED |
| friction collector/uploader | NOT BUILT | NOT BUILT |

## Ownership stays separate

```text
KINGDOM  executes / orchestrates
EROS / host policy owns execution authority
Evidence Gate      judges completion evidence
ACL      makes shadow recommendations
HyoDo    observes / records / validates / attests / measures
```

Fresh Codex/Cursor observation, QMD/Neo4j closed-loop work, and matched
ACL/KINGDOM experiments are downstream integration/research work. The 4.19.6
candidate is not a public artifact until its release gates complete.
