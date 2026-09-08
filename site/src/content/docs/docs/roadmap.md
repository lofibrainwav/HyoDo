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
defaults to fixed demo data. On that page you can opt in to load a local
`hyodo.evidence-graph/v1` file in the browser; nothing is uploaded. Since
4.14.0 the installed CLI renders the same graph from your real agent-event
ledger (`hyodo dashboard`, `/graph`); the public page is not that viewer and
does not read a remote ledger. See
[its documentation](/docs/evidence-graph/) for the exact boundary.

Stage 2 packages (`hyodo skills`, `hyodo inspect`, `hyodo graph export`, `hyodo eye`) ship in HyoDo 4.15.0. They record digests, hashes, and receipts only; embeddings, model calls, and capture tools remain external.

HyoDo 4.16.0 derives Benevolence and the HyoDo Integrity Score's five pillar inputs from measured `check`/`safe`/test-integrity evidence, closes shadow-mode and continuity coverage gaps, and adds scan positive controls.

## Shipped today vs. not built yet

| Shipped today | Not built yet |
| --- | --- |
| `hyodo safe` scans | Live Drive connector (remote inventories are recorded as claims, never fetched) |
| `hyodo init` and `hyodo check` gates | Remote MCP OAuth onboarding |
| FDE evidence spine and policy checks | Full folder semantic onboarding |
| `ASK` decisions and trust levels | RAG or embeddings in public HyoDo |
| Schema validation and local eval runs | Cross-source verification loop |
| Source-line graph JSON report export | Stage 4 intent loop |
| Research-node hand-off (`hyodo skills ingest --from-node`) — the node itself stays external | |
| MCP stdio, Tailscale serve, doctor | |
| PyPI Trusted Publishing, SBOM, SARIF | |
| `hyodo connect` (dry-run by default; `cursor`/`codex` report UNOBSERVED) | |
| Local graph viewer (`hyodo dashboard` → `/graph`, reads the real ledger) | |
| Audience profiles (`--audience vibe`/`engineer`/`professional`) (4.15.0) | |
| `hyodo skills` lens (ingest/lens/propose, no model or embeddings) (4.15.0) | |
| `hyodo inspect` field-deployment folder absorption (4.15.0) | |
| `hyodo graph export` evidence-graph bridge (4.15.0) | |
| `hyodo eye capture`/`verify` ephemeral visual evidence (4.15.0) | |
| `actor_id` nesting and per-actor rings in the local graph viewer (4.15.0) | |
| `hyodo check`/`score --from-check` derived Benevolence and pillar coverage (4.16.0) | |
| `hyodo safe` scope/coverage reporting and scan positive controls (4.16.0) | |
| `hyodo mcp continuity` hook-recorded host coverage (4.16.0) | |

A public [evidence-graph prototype](/evidence-graph/) shows the intended shape
using demo fixture data by default, with an opt-in local v1 file load. See
[its documentation](/docs/evidence-graph/) for the source-line graph export
boundary and what remains demo-only.

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
