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
| 1 | Judgment | `ASK` decisions, trust levels, evidence graph | Planned |
| 2 | Mobilization | Research nodes under policy | Planned |
| 3 | Reconciliation | Cross-source verification | Exploration |
| 4 | Intent | The full loop | Exploration |

Stage 1 also covers external variables, web policy, and `hyodo connect` — it
requires no model. Stage 2 adds bring-your-own-model support.

## Shipped today vs. not built yet

| Shipped today | Not built yet |
| --- | --- |
| `hyodo safe` scans (strict, JSON) | `ASK` decisions (declared, unused) |
| `hyodo init` / `hyodo check` gates | External variables, trust levels |
| FDE evidence spine, policy checks | Web policy, evidence graph |
| Schema validation, local eval runs | `hyodo connect` |
| MCP stdio, Tailscale serve, doctor | Research nodes under policy |
| PyPI Trusted Publishing, SBOM | Bring-your-own-model support |
| SARIF, pre-commit hooks, GH Action | Cross-source verification, full loop |

"`ASK` decisions (declared, unused)" means the decision word already exists
in the policy vocabulary but no evaluation path emits it yet — see
[Philosophy → Math → Code](/docs/philosophy/) for the honest detail.

## Proposing roadmap work

Work is accepted only when implementation, tests, documentation, and release
evidence agree. See
[CONTRIBUTING.md](https://github.com/lofibrainwav/HyoDo/blob/main/CONTRIBUTING.md)
for how to propose changes, and the full
[ROADMAP.md](https://github.com/lofibrainwav/HyoDo/blob/main/ROADMAP.md) for
landed milestones and later exploration.

## Next

- [Philosophy → Math → Code](/docs/philosophy/)
- [Trust](/docs/trust/)
