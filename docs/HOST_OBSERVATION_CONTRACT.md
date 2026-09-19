# Host Observation Contract

What HyoDo's host adapters actually record, what they leave unrecorded, and
which of those gaps are closable with evidence the host already supplies.

This document reports measurements. Where a shape was not observed it says so
rather than describing what it probably is. Every count below comes from one
real local ledger of 3,845 events written by the Codex adapter.

## Why this exists

The evidence-graph surfaces now report their gaps honestly, and the gaps are
large. Against that ledger every event lands in a gutter and no evidence edge
exists at all. That is not a rendering problem. It is the recording surface
telling the truth about itself, and the next question is which parts of it are
fixable with facts the host already hands over.

## Measured coverage

| Signal | Count | Share |
| --- | --- | --- |
| events | 3,845 | |
| `tool_call` | 2,015 | 52% |
| `tool_result` | 1,830 | 48% |
| distinct `actor` values | 1 (`agent`) | |
| events with any `evidence_refs` | 0 | 0% |
| events with a non-null `policy.decision` | 0 | 0% |
| `prompt` events | 0 | 0% |
| `UNMEASURED` (nothing classification can read) | 2,093 | 54% |
| `UNCLASSIFIED` (evidence recorded, no mapping row) | 1,752 | 46% |

`UNMEASURED` is 2,015 `tool_call` plus 78 `tool_result`. Every `tool_call` in
the ledger is unmeasured. `UNCLASSIFIED` is entirely `tool_result` events that
did record an `output_digest`: 1,618 `Bash`, 128 `apply_patch`, 6 `webrun`.

A recording gap and a mapping gap stay separate states because they call for
different repairs. In this ledger they happen to share one cause, which does
not merge them.

## Finding 1 — `evidence_refs` are absent at the source

`hyodo/event_graph.py` emits an `evidence_ref` edge for each entry in an
event's `evidence_refs`. The graph reported zero such edges, which had two
possible causes: the refs are missing, or they are present and not consumed.

Measured: 0 of 3,845 events carry any `evidence_refs`, and the total ref count
is 0. **The graph is correct.** Nothing is being ignored; nothing was
recorded. The adapters have no code path that writes an `evidence_refs` entry.

## Finding 2 — the 185 unanswered calls are unanswered, not unlinked

185 `tool_call` events have no `tool_result` citing them as a causal parent.

Pairing provenance: `host_adapters/_common.py` builds an event id as
`{host}:{event_name}:{tool_use_id}` when the host supplies `tool_use_id`, and
falls back to a payload digest when it does not. It sets `parent_event_id` to
`{host}:{pre_event_name}:{tool_use_id}` only in the first case, and
deliberately invents no parent in the second.

Every id in this ledger has the `codex:PreToolUse:exec-…` form, so every event
came through the `tool_use_id` path. The adapter therefore had the material to
link and did not drop it. Measured: for all 185, no `PostToolUse` event exists
anywhere in the ledger with the same exec id.

| Check | Result |
| --- | --- |
| matching `PostToolUse` present but unlinked | 0 of 185 |
| orphan is the run's last event | 0 of 185 |
| orphan shares an `args_digest` with another orphan | 61 of 185 |
| tools | 171 `Bash`, 14 `apply_patch` |

The run-position distribution is flat from 0% to 100% of run progress, so
truncation at process exit does not explain it. The honest state of these
events is `CALL OBSERVED` with `RESULT UNOBSERVED`. Which host condition drops
the callback is **UNOBSERVED**: no hook-level failure record exists to read.

## Finding 3 — intent is recordable and no adapter records it

`hyodo/events.py` `EVENT_KINDS` already includes `prompt`, so the ledger
schema carries intent today. `hyodo/connect.py` installs hooks for
`PreToolUse` and `PostToolUse` only and rejects every other hook event name.
`host_adapters/codex.py` likewise maps only those two.

Codex exposes more. Its `HookEventName` vocabulary, read from the installed
binary, includes `user_prompt_submit` alongside `pre_tool_use` and
`post_tool_use`. The capability exists on both sides and nothing connects
them.

Two of two runs in this ledger therefore have no recorded intent. Reported as
`missing.runs_without_intent`, that reads as a count of 2; as coverage it is
100%. Under the five-questions model those runs answer Who, What, When, Where
and How, and leave Why unobserved.

What is **UNOBSERVED**: the payload shape of a real `user_prompt_submit` hook
event. The name is measured, the contents are not.

## Finding 4 — `apply_patch` input shape is unobserved, so the work is held

Recording a path for an `apply_patch` call would move 14 orphaned calls and
128 unclassified results out of the gutters, if the host supplies a path as
structured data.

`host_adapters/_common.py` reads `tool_input.file_path` and nothing else, so a
call shaped any other way records no path.

What was searched and what it showed:

| Source | Result |
| --- | --- |
| repository fixtures, tests, docs | one passing mention, no payload shape |
| the ledger | `args_digest` only; the raw input is not retained by design |
| Codex logs | no hook payloads retained |
| Codex binary strings | an approval-event structure keyed by path exists |

The last row is suggestive and is not the hook payload. An internal approval
model is not evidence about `tool_input`.

**Held.** The rule set for this work is explicit: if an explicit structured
path is actually observed in a hook payload, the work proceeds; if it would
require parsing patch text, it waits for a separate derived-evidence contract.
Neither branch can be chosen from a shape nobody has seen. One captured
`PreToolUse` payload for an `apply_patch` call settles it.

## Boundaries this work does not cross

These are constraints on any repair, not open questions.

- No path is extracted from a `Bash` command string. That is reading a name
  for what it did, which `graph_view.carries_measured_evidence` refuses by
  design, and it covers 1,618 of the unclassified results, so the temptation
  is proportional to the harm.
- No semantic lens is inferred from a tool name.
- No `prompt` or intent event is synthesized for a run that recorded none.
- No `evidence_refs` entry is written that the host did not supply.
- The mapping table is not widened to reduce `UNCLASSIFIED`. That count is a
  reading of the recording surface; lowering it by changing the reader would
  destroy the measurement.

Presentation may compress truth. It may not reconstruct truth. The same rule
governs recording: an adapter may record less than the host offers, and must
never record more than the host said.

## What would change these numbers

In dependency order, each gated on an observation rather than an assumption.

1. One captured `PreToolUse` payload per tool kind, which settles Finding 4
   and shows what else the host offers that the adapter drops.
2. An intent path, once a real `user_prompt_submit` payload is observed.
3. A recorded reason for the dropped `PostToolUse` callbacks, which today have
   no failure record to read.

`evidence_refs` stay absent until something in the loop has a reason to cite
evidence. That is a product question, not an adapter gap.
