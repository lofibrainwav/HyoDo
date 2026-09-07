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

Stage 2 packages (`hyodo skills`, `hyodo inspect`, `hyodo graph export`, `hyodo eye`) exist on the source development line and are not yet in a published release. They record digests, hashes, and receipts only; embeddings, model calls, and capture tools remain external.

## Shipped today vs. not built yet

| Shipped today | Not built yet |
| --- | --- |
| `hyodo safe` scans | Research nodes under policy |
| `hyodo init` and `hyodo check` gates | Bring-your-own-model support |
| FDE evidence spine and policy checks | Full folder semantic onboarding |
| `ASK` decisions and trust levels | RAG or embeddings in public HyoDo |
| Schema validation and local eval runs | Cross-source verification loop |
| Source-line graph JSON report export | Stage 4 intent loop |
| MCP stdio, Tailscale serve, doctor | |
| PyPI Trusted Publishing, SBOM, SARIF | |
| `hyodo connect` (dry-run by default; `cursor`/`codex` report UNOBSERVED) | |
| Local graph viewer (`hyodo dashboard` → `/graph`, reads the real ledger) | |

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
