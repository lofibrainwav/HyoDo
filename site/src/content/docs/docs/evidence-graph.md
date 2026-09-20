---
title: Evidence Graph
description: What the evidence-graph prototype shows, what the source graph export emits, and what remains demo-only.
---

## What this shows

The [evidence graph](/evidence-graph/) renders one run as a grid: rows are
producer-declared participant lanes, columns are observed timestamps from left
to right, and each occupied cell is one event. `step_index` remains event
detail because it resets across runs. Missing or invalid timestamps stay in a
`TIME UNOBSERVED` column. Hovering or focusing a cell opens a 5W1H record,
five independent lens states, the verification rail, and continuity status.

The public viewer accepts `hyodo.verification-view/v0` as its canonical input.
It consumes the projection's lanes, presentable decision, lens columns, and
missing buckets; it does not reconstruct roles, decisions, or continuity from
actor names, tool names, or grid position.

## 5W1H mapping

| Field | Source                                        |
| ----- | --------------------------------------------- |
| Who   | `actor`                                       |
| When  | observed `ts`; `step_index` is detail only   |
| What  | `kind`, plus `tool.name` or `policy.decision` |
| Where | `tool.paths`, `tool.urls`                     |
| How   | derived from `kind`                           |
| Why   | `policy.reason`                               |

## Decisions

`ALLOW`, `ASK`, `DENY`, and `UNOBSERVED` are policy-evaluation outputs as of
v4.13.0. `hyodo policy check` exits `0` for `ALLOW`, `1` for `DENY`, `2` for
`UNOBSERVED`, and `3` for `ASK`. `UNOBSERVED` is never treated as a pass —
it means no policy record exists for that step, not that the step was
approved. These outputs are not execution permissions: HyoDo does not run or
authorize agents, and the host or a human decides what happens next.

## Verification and release boundary

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

The local dashboard and public viewer share the same `hyodo.verification-view/v0`
meaning. The viewer shows `recorded` and `presentable` decisions together; a
recorded `ALLOW` is displayed as `UNOBSERVED` when the projection withholds it.
The five measured columns are independent evidence states, not scores. `永 /
CONTINUITY` is separate from time and remains `UNOBSERVED` unless independent
continuity evidence is supplied. `WHAT IS MISSING` is progressively disclosed
from the projection's own buckets.

Release boundary: the public page defaults to fixed demo fixture data and
does not read a real ledger. On `/evidence-graph/` you can opt in to load a
local `hyodo.verification-view/v0` JSON file in the browser; that is not a
remote ledger. A raw `hyodo.evidence-graph/v1` file remains a compatibility
fallback and cannot provide canonical presentable decisions. Installing the
latest published package may lag the source development line until the next
release is published.

## Broken links

When a `parent_event_id` resolves to no event in the run, the graph draws a
short broken edge instead of hiding the gap or silently resolving it. The
fixture includes one such case on purpose, so the broken-link rendering is
part of what this prototype demonstrates, not an edge case it hides.

## Demo fixture data only

The 14 events on the public page are fixed, in-memory demo data. Nothing
is uploaded, stored, or fetched from a network, and no real ledger is
read. The default view stays on that fixture so the visual shape and the
broken-link case stay reviewable.

On `/evidence-graph/` you can opt in to load a local
`hyodo.verification-view/v0` JSON file (the local dashboard serves this
projection beside `/api/graph`). The file is read in the browser only; it is
never uploaded. A malformed or unknown payload does not become a green grid —
the page keeps the fixture and surfaces the projection `status`/`reason`.
`UNOBSERVED` is never treated as a pass. A raw `hyodo.evidence-graph/v1`
artifact remains loadable for compatibility, but its decisions are not
presentable until the canonical verification view is loaded.

Since 4.14.0 the installed CLI emits the same graph from a real ledger:
`hyodo report --format graph` writes a local JSON artifact and `hyodo
dashboard` serves it at `/graph`. That local dashboard is the live
ledger viewer. This public page does not read a remote ledger.

## Next

- [Roadmap](/docs/roadmap/)
- [Trust](/docs/trust/)
