---
title: Current state
description: Public release, current main, and measured HyoDo state separated by evidence boundary.
---

Runtime capability matrix below was measured 2026-09-13 PT, before 4.19.6; it
is a historical snapshot.

HyoDo **4.21.11** is the current release target and source-tree release candidate.
The latest fully sealed public release remains **4.21.9**. HyoDo 4.21.10 has a verified
signed tag, published GitHub Release, and SBOM evidence, but its PyPI publish
workflow is waiting at the `pypi` environment approval boundary, so that
release chain is not closed yet. Product capability and live host observation
remain separate evidence axes.

- Canonical source branch: **`main`**
- Current release target: **4.21.11** (release chain `UNOBSERVED`)
- Latest published package: **4.21.9** (fully sealed; see the 4.21.9 receipt)
- 4.21.6 was tagged and has a GitHub Release, but it was never published to
  PyPI; it is superseded by 4.21.7 and left unchanged.
- Phase 0: **CLOSED**; Evidence Pack v1 remains sealed with named residuals.

HyoDo 4.21.7 is security-only. Operator decisions -- gate approvals, policy
trust grants, pairing records, scan-exception approvals, and ledger origin --
live in per-user state outside the checkout, so a repository cannot supply its
own authority. See the
[trust boundary contract](https://github.com/lofibrainwav/HyoDo/blob/main/docs/TRUST_BOUNDARY.md).

HyoDo 4.21.11 carries #506: unknown `policy.toml` keys fail closed as
`policy_invalid` / `UNOBSERVED` instead of silently weakening intended
policy. Valid `hyodo.policy/v1` semantics are unchanged.

HyoDo 4.21.10 carries the native hook root fix from #501 at immutable tag target
`b3d8da5b32aefcb553da3414c69177fbad30d347`. Its GitHub Release and SBOM are
published, while PyPI publication is still waiting at the environment gate.
#506 merged after that tag and is not part of 4.21.10.

HyoDo 4.21.9 carries the provenance classification fix from #488: an
unreadable source subtree is `SOURCE_UNOBSERVED` / `UNOBSERVED` with
`green_allowed=false`, not `SELF_OTHER_CHECKOUT` / `MISMATCH`. #487 is
test-only fixture hardening and adds no product capability.

HyoDo 4.21.8 carries the evidence/judgment boundary: gate-to-virtue
attribution remains evidence, `hyodo.lens-evidence/v1` reports lens state with
`authority: UNOBSERVED`, and legacy score derivation is compatibility only.
Package release evidence does not imply a live Codex or Cursor connection;
host observation is deployment-specific.

## Runtime capability snapshot (2026-09-13 PT)

The matrix below compares the 4.19.5 public package with main as measured on
2026-09-13. It is not a fresh runtime readback for the current 4.21.9 release.

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
prerequisites for calling the HyoDo 4.21.9 public artifact released and verified.
