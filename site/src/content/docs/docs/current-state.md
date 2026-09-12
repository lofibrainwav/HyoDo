---
title: Current state
description: Public release, current main, and measured HyoDo state separated by evidence boundary.
---

# HyoDo current state

Snapshot: **2026-09-11 PT**.

This page separates the latest public package from newer work already landed on
`main` and from direct live/KINGDOM observations. It intentionally does not pin
its own commit SHA; an exact revision belongs in a release or runtime receipt,
not in a self-referential current-state page.

- Canonical source branch: **`main`**
- Latest public package: **4.19.2**
- Next release target: **4.19.3** (candidate; not published)
- Phase 0: **CLOSED**; Evidence Pack v1 is sealed with named residuals.
- Active closure program: **#263 HyoDo Final Closure**

| Capability | Public 4.19.2 | Current main / measured state |
| --- | --- | --- |
| gates, policy, event ledger | SHIPPED | SHIPPED |
| local Friction Contribution | SHIPPED | SHIPPED; local only |
| MCP stdio / loopback / private Tailscale | SHIPPED | SHIPPED |
| canonical runtime identity v1 | not in 4.19.2 | SHIPPED; `/api/identity` + receipt contract, KINGDOM consumer merged |
| MCP access-audit readback | not in 4.19.2 | SHIPPED; operation and audit state are separate, audit loss is fail-visible |
| release-note drift verifier | not in 4.19.2 | SHIPPED; repo notes are canonical, unavailable remote evidence is UNOBSERVED, mutation requires explicit apply + readback |
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
| Graph v2 true multi-parent runtime | NOT BUILT | SHIPPED on `main`; multi-parent read/normalize/export/viewer + Tarjan SCC with v1 compatibility; #222 closed |
| Information Flow Attestation v0 | RESEARCH | SHIPPED observer-only on `main`; privacy lineage stays separate and non-authoritative; #229 closed |
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

The remaining final-closure path is the #224 convergence review, a governed
post-4.19.2 release, KINGDOM clean-install dogfood on that public artifact,
matched #225 ACL/KINGDOM shadow experiments, explicit host/transport scope
closure, and maintenance mode.

Capability existence is not run usage. Missing evidence is not green. Research
is not shipped capability evidence.
