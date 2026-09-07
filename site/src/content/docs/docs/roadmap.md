---
title: Roadmap
description: Where HyoDo is headed, staged honestly against what ships today.
---

HyoDo is the first organ of an open-source Agent OS.

This page describes direction, not a delivery promise. The
[ROADMAP.md](https://github.com/lofibrainwav/HyoDo/blob/main/ROADMAP.md) file
in the repository is the source of truth; this page summarizes it.

## Five stages

| Stage | Name | Status |
| --- | --- | --- |
| 0 | Launch surface | Live |
| 1 | Judgment | In progress |
| 2 | Mobilization | Planned |
| 3 | Reconciliation | Exploration |
| 4 | Intent | Exploration |

Stage 1 includes `ASK` decisions, trust levels, external variables, and web
policy. That policy layer shipped in v4.13.0 and requires no model.

The [evidence graph](/evidence-graph/) is a public, browser-only prototype that
renders fixed demo data. The source development line can emit a local graph JSON
report from the agent-event ledger, but the public page is not an installed
browser viewer and does not read a real ledger. See
[its documentation](/docs/evidence-graph/) for the exact boundary.

`hyodo connect` and Stage 2's bring-your-own-model support are not built yet.

## Shipped today vs. not built yet

| Shipped today | Not built yet |
| --- | --- |
| `hyodo safe` scans | `hyodo connect` |
| `hyodo init` and `hyodo check` gates | Installed browser graph viewer |
| FDE evidence spine and policy checks | Research nodes under policy |
| `ASK` decisions and trust levels | Bring-your-own-model support |
| Schema validation and local eval runs | Full folder semantic onboarding |
| Source-line graph JSON report export | RAG or embeddings in public HyoDo |
| MCP stdio, Tailscale serve, doctor | Cross-source verification loop |
| PyPI Trusted Publishing, SBOM, SARIF | Stage 4 intent loop |

A public [evidence-graph prototype](/evidence-graph/) shows the intended shape
using demo fixture data. See [its documentation](/docs/evidence-graph/) for the
source-line graph export boundary and what remains demo-only.

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
