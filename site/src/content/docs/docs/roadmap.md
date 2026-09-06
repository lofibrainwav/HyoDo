---
title: Roadmap
description: Where HyoDo is headed, staged honestly against what ships today.
---

HyoDo is the first organ of an open-source Agent OS.

This page describes direction, not a delivery promise. The
[ROADMAP.md](https://github.com/lofibrainwav/HyoDo/blob/main/ROADMAP.md) file
in the repository is the source of truth; this page summarizes it.

## Five stages

| Stage | Name | What it covers | Status |
| --- | --- | --- | --- |
| 0 | Launch surface | The `hyodo` CLI and quality gates | Live |
| 1 | Judgment | `ASK` decisions, trust levels, external variables, and web policy (shipped in v4.13.0); a public evidence-graph prototype (demo data only); hyodo connect (not built) | In progress |
| 2 | Mobilization | Research nodes under policy | Planned |
| 3 | Reconciliation | Cross-source verification | Exploration |
| 4 | Intent | The full loop | Exploration |

Stage 1's policy layer — `ASK` decisions, trust levels, external variables,
and web policy — shipped in v4.13.0 and requires no model. The
[evidence graph](/evidence-graph/) is a public, browser-only prototype that
renders fixed demo data; it is not an installed local viewer and does not
read a real ledger — see [its documentation](/docs/evidence-graph/) for
exactly which fields are real today. `hyodo connect` and Stage 2's
bring-your-own-model support are not built yet.

## Shipped today vs. not built yet

| Shipped today | Not built yet |
| --- | --- |
| `hyodo safe` scans (strict, JSON) | `hyodo connect` |
| `hyodo init` / `hyodo check` gates | Evidence graph as an installed local viewer |
| FDE evidence spine, policy checks | `parent_event_id` / `evidence_refs` in the shipped ledger schema |
| `ASK` decisions, trust levels, external variables, web policy (v4.13.0) | Research nodes under policy |
| Schema validation, local eval runs | Bring-your-own-model support |
| MCP stdio, Tailscale serve, doctor | Cross-source verification, full loop |
| PyPI Trusted Publishing, SBOM, SARIF, pre-commit hooks, GH Action | Stage 4 intent loop |

A public [evidence-graph prototype](/evidence-graph/) shows the intended
shape using demo fixture data — see
[its documentation](/docs/evidence-graph/) for which fields are live today
and which are proposed.

## Proposing roadmap work

Work is accepted only when implementation, tests, documentation, and release
evidence agree. See
[CONTRIBUTING.md](https://github.com/lofibrainwav/HyoDo/blob/main/CONTRIBUTING.md)
for how to propose changes, and the full
[ROADMAP.md](https://github.com/lofibrainwav/HyoDo/blob/main/ROADMAP.md) for
landed milestones and later exploration.

## Next

- [Philosophy → Math → Code](/docs/philosophy/)
- [Evidence Graph](/docs/evidence-graph/)
- [Trust](/docs/trust/)
