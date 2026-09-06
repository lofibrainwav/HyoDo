---
title: Evidence Graph
description: What the evidence-graph prototype shows, and which of its fields are real today.
---

## What this shows

The [evidence graph](/evidence-graph/) renders one run as a grid: rows are
participants (a human operator and three illustrative agents — planner,
executor, reviewer), columns are step index, and each occupied cell is one
event. Hovering or focusing a cell opens a 5W1H record for that event in the
side panel.

## 5W1H mapping

| Field | Source                                       |
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

## Proposed fields: `parent_event_id` and `evidence_refs`

The two link types the graph draws — a solid elbow for "result of" and a
dashed curve for "decided from" — are **not** in the shipped
`hyodo.agent-event/v1` schema. See
[`hyodo/events.py`](https://github.com/lofibrainwav/HyoDo/blob/main/hyodo/events.py)
for the fields that do exist today. `parent_event_id` and `evidence_refs`
are planned in package 1-B of the
[Phase 1 design spec](https://github.com/lofibrainwav/HyoDo/blob/main/docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md).
Until then, both fields exist only in this prototype's fixture data.

## Broken links

When a `parent_event_id` resolves to no event in the run, the graph draws a
short broken edge instead of hiding the gap or silently resolving it. The
fixture includes one such case on purpose, so the broken-link rendering is
part of what this prototype demonstrates, not an edge case it hides.

## Demo fixture data only

The 14 events on the page are fixed, in-memory demo data. Nothing is
uploaded, stored, or fetched from a network, and no real ledger is read.
The shipped `hyodo` CLI has no graph viewer yet — this page is a prototype
of the intended shape, not an installed feature.

## Next

- [Roadmap](/docs/roadmap/)
- [Trust](/docs/trust/)
