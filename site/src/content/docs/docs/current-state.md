---
title: Current state
description: Public release, current main, and measured HyoDo state separated by evidence boundary.
---

# HyoDo current state

Snapshot: **2026-09-11 PT**.

HyoDo has moved beyond several older planning notes. This page separates the
latest public package from newer work already landed on `main` and from direct
live/KINGDOM observations.

- Latest public package: **4.19.2**
- Reconciled `main`: `8f6bf23a9bfa5fb6eb6eb804335d9d864aa50a82`
- Phase 0: **CLOSED**; Evidence Pack v1 is sealed with named residuals.
- Active phase: Phase 1 observation/passive-shadow expansion.

| Capability | Public 4.19.2 | Current main / measured state |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; local only |
| MCP stdio / loopback / private Tailscale | SHIPPED | SHIPPED |
| Codex host adapter | SHIPPED | SHIPPED plus newer landed fixes |
| installed Codex callback | release-era UNOBSERVED | historically OBSERVED in an isolated real-host run |
| current canonical Codex canary | UNOBSERVED | UNOBSERVED until a fresh receipt is sealed |
| Codex output digest | not in 4.19.2 | LANDED + OBSERVED |
| Codex causal parent | not in 4.19.2 | LANDED + OBSERVED |
| Codex model provenance | not in 4.19.2 | LANDED + OBSERVED |
| Cursor live callback | UNOBSERVED | UNOBSERVED |
| orchestration observation ingest | not in 4.19.2 | LANDED |
| KINGDOM declared serial/parallel stage shape | not in 4.19.2 | OBSERVED |
| sidecar replay idempotency | not in 4.19.2 | LANDED + verified |
| unstated attempt remains unknown | not in 4.19.2 | LANDED + verified |
| Graph v2 true multi-parent runtime | NOT BUILT | NOT BUILT; oracle/fixtures only |
| ACL / Wisdom Reflex automatic routing | RESEARCH | RESEARCH / shadow only |
| public remote MCP | CONTRACT ONLY | CONTRACT ONLY / UNOBSERVED |
| friction collector/uploader | NOT BUILT | NOT BUILT |

## Ownership stays separate

```text
KINGDOM            executes / orchestrates
EROS / host policy owns execution authority
Evidence Gate      judges completion evidence
ACL                makes shadow recommendations
HyoDo              observes / records / validates / attests / measures
```

The next product path is documentation convergence, a governed post-4.19.2
release, KINGDOM dogfood on the public artifact, Graph v2 multi-parent runtime,
and then matched ACL/KINGDOM shadow experiments.

Capability existence is not run usage. Missing evidence is not green. Research
is not shipped capability evidence.
