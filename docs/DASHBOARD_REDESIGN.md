# Dashboard redesign baseline

Status: **design baseline, implementation not started**.

This document separates the HyoDo local dashboard from the KINGDOM consumer.
They have different owners and different evidence authority:

| Surface | Owner | Current state | Boundary |
| --- | --- | --- | --- |
| `hyodo dashboard` / `:8768` | HyoDo | Six-pillar instrument cards plus local `/graph` | Reads local HyoDo evidence; no composite score |
| Public `/evidence-graph/` | HyoDo site | Fixed 14-event demo fixture with optional local JSON load | Not a live KINGDOM run |
| KINGDOM HyoDo board | KINGDOM | Six-axis merge of KINGDOM pulse and HyoDo live evidence | Consumer only; must preserve `UNOBSERVED` |

## Why the current layout is not enough for Evidence Pack v1

The six cards answer “what is the current checkout gate state?” They do not
make a real measured run the primary object. The graph answers “what events are
connected?” but does not yet present a run receipt, exact HyoDo/KINGDOM SHAs,
or a signal-by-signal coverage matrix. The KINGDOM board adds useful context,
but mixes two sources in one card and is not organized around Measured Run #3.

## Proposed information architecture

1. **Run overview** — selected run id, measured time, exact HyoDo and KINGDOM
   SHAs, observer contract version, consent/privacy boundary, and terminal
   outcome. Freshness and source are always visible.
2. **Coverage matrix** — serial, parallel, DAG join, retry, wait, rework,
   human intervention, and unresolved observation. Each signal is exactly one
   of `OBSERVED`, `PARTIAL`, or `UNOBSERVED`, with an evidence reference or an
   explicit reason for absence.
3. **Execution timeline** — ordered nodes and attempts, with join edges and
   wait/rework markers. This is a drill-down, not a new verdict engine.
4. **Evidence graph** — reuse the existing HyoDo graph viewer for event and
   dependency inspection, without inventing fields or changing decisions.
5. **Current checkout health** — keep the existing six-pillar cards as a
   secondary tab/panel for local gate health, not the run landing page.

## Non-negotiable design contracts

- No composite score is introduced as release or execution authority.
- `UNOBSERVED` remains visible; missing data never becomes green.
- HyoDo remains an observer/attester. KINGDOM remains the executor.
- Local HyoDo evidence and KINGDOM snapshot evidence retain separate source
  labels and timestamps.
- Demo fixtures, local live evidence, and sealed measured receipts use distinct
  badges and cannot be presented as interchangeable.
- The first implementation must render the same eight-signal matrix used by
  the Evidence Pack v1 receipt. A field is not considered measured merely
  because the UI has a placeholder for it.

## Open product decision

Recommended default: make **Run overview** the landing view for the next
milestone, with the six-pillar checkout panel one click away. This matches the
actual goal, which is to measure KINGDOM execution, not to optimize a static
health score. If the operator instead wants the six-pillar panel to remain the
landing view, the run overview should still be the first linked action and the
coverage matrix must remain visible without opening a demo graph.

## Acceptance before implementation is called complete

- A real Run #3 receipt can be selected and traced from overview to raw-safe
  evidence references and graph nodes.
- All eight requested signals show `OBSERVED`, `PARTIAL`, or `UNOBSERVED`.
- HyoDo live, KINGDOM snapshot, and fixture/demo sources are visually distinct.
- Keyboard navigation, reduced motion, narrow viewport, stale evidence, and
  missing evidence are tested.
- The rendered dashboard and the Evidence Pack receipt agree on counts,
  timestamps, SHAs, and uncertainty labels.
