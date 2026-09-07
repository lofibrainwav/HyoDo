---
title: Evidence Graph
description: What the evidence-graph prototype shows, what the source graph export emits, and what remains demo-only.
---

## What this shows

The [evidence graph](/evidence-graph/) renders one run as a grid: rows are
participants (a human operator and three illustrative agents — planner,
executor, reviewer), columns are step index, and each occupied cell is one
event. Hovering or focusing a cell opens a 5W1H record for that event in the
side panel.

## 5W1H mapping

| Field | Source                                        |
| ----- | --------------------------------------------- |
| Who   | `actor`                                       |
| When  | `ts`, `step_index`                            |
| What  | `kind`, plus `tool.name` or `policy.decision` |
| Where | `tool.paths`, `tool.urls`                     |
| How   | derived from `kind`                           |
| Why   | `policy.reason`                               |

## Decisions

`ALLOW`, `ASK`, `DENY`, and `UNOBSERVED` are live policy decisions as of
v4.13.0. `hyodo policy check` exits `0` for `ALLOW`, `1` for `DENY`, `2` for
`UNOBSERVED`, and `3` for `ASK`. `UNOBSERVED` is never treated as a pass —
it means no policy record exists for that step, not that the step was
approved.

## Graph fields and release boundary

The two link types the graph draws — a solid elbow for "result of" and a
dashed curve for "decided from" — map to optional `hyodo.agent-event/v1`
fields on the source development line: `parent_event_id` and `evidence_refs`.
`tool.urls` is also preserved in graph output so web observations can name the
observed domain, a path digest, and a `credential_shaped` boolean (or `null`
when unobserved) without storing the path or a full response body.

`hyodo report --format graph` emits a deterministic local JSON artifact at
`.hyodo/reports/hyodo-report.graph.json`. It is still evidence-only: broken
parents, broken evidence references, unreadable ledgers, or corrupt ledger
lines are reported as `UNOBSERVED` instead of being converted into a clean
graph.

Release boundary: the public page still uses fixed demo fixture data and does
not read a real ledger. Installing the latest published package may lag the
source development line until the next release is published.

## Broken links

When a `parent_event_id` resolves to no event in the run, the graph draws a
short broken edge instead of hiding the gap or silently resolving it. The
fixture includes one such case on purpose, so the broken-link rendering is
part of what this prototype demonstrates, not an edge case it hides.

## Demo fixture data only

The 14 events on the page are fixed, in-memory demo data. Nothing is
uploaded, stored, or fetched from a network, and no real ledger is read.
`hyodo report --format graph` can emit a local JSON graph artifact on the
source development line. The CLI now includes a local viewer — `hyodo
dashboard` serves `/graph`, reading the real ledger — on the source line, not
yet in a published release until 4.14.0 ships. This public page remains a
standalone fixture-data prototype and does not read a real ledger.

## Next

- [Roadmap](/docs/roadmap/)
- [Trust](/docs/trust/)
