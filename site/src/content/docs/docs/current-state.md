---
title: Current state
description: Public release, current main, and measured HyoDo state separated by evidence boundary.
---

# HyoDo current state

Public release readback: **2026-09-19 PT**. Runtime capability matrix below
was measured 2026-09-13 PT, before 4.19.6; it is a historical snapshot.

HyoDo **4.20.1** is the current public package. Product capability and live
host observation remain separate evidence axes.

- Canonical source branch: **`main`**
- Latest public package: **4.20.1**
- Release chain: **CLOSED** — signed tag, GitHub Release + SBOM, PyPI provenance,
  and install smoke verified in the [release receipt](https://github.com/lofibrainwav/HyoDo/blob/main/docs/releases/4.20.1.md).
- Phase 0: **CLOSED**; Evidence Pack v1 remains sealed with named residuals.

HyoDo 4.20.1 preserves distinct graph participants and explicit From/To
endpoints, and adds opt-in comparisons of host-supplied scalar requirements.
Evidence references, missing observations, and changed requirements are shown
without claiming automatic intent understanding or execution authority.
Separately stored occurrence, observation, and recording timestamps remain a
design target. Fresh Codex or Cursor host observations remain `UNOBSERVED`.

## Runtime capability snapshot (2026-09-13 PT)

The matrix below compares the 4.19.5 public package with main as measured on
2026-09-13. It is not a fresh runtime readback for 4.20.0.

| Capability | Public 4.19.5 at snapshot | Main / measured state at snapshot |
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
| Graph v2 multi-parent runtime | SHIPPED | SHIPPED; deterministic multi-parent graph with v1 compatibility |
| Information Flow Attestation v0 | SHIPPED | SHIPPED observer-only; non-authoritative |
| Adaptive support-allocation experiments | RESEARCH | Downstream research / shadow only |
| public remote MCP | CONTRACT ONLY | CONTRACT ONLY / UNOBSERVED |
| friction collector/uploader | NOT BUILT | NOT BUILT |

## Ownership stays separate

```text
Integrating host       executes / orchestrates
Host authorization     owns execution authority
Evidence validation    judges completion evidence
Downstream research    makes non-authoritative shadow recommendations
HyoDo                  observes / records / validates / attests / measures
```

Fresh Codex/Cursor observation, QMD/Neo4j closed-loop work, and matched
Support-allocation/host experiments are downstream integration/research work. They are not
prerequisites for calling the HyoDo 4.20.1 public artifact released and verified.
