# Host Observation Contract

What HyoDo's host adapters actually record, what they leave unrecorded, and
which of those gaps are closable with evidence the host already supplies.

This document reports measurements. Where a shape was not observed it says so
rather than describing what it probably is. The counts below were reported
from one local ledger of 3,845 events written by the Codex adapter. They
describe that sample, not all installations or current host behavior.
The ledger, capture
window, host binary version, and reproducible measurement receipt are not
published here, so external reproduction of those counts is **UNOBSERVED**.
Source inspection can verify the adapter behavior described below; it cannot
independently verify the private sample counts.

This is an observation report under [the product
boundary](./PRODUCT_BOUNDARY.md).
HyoDo records and validates supplied evidence; the integrating host owns
execution, callback delivery, recovery, and authorization. No host repair or
KINGDOM runtime completion is implied by this report.

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

## Finding 2 — 185 calls have no matching result in the sampled ledger

185 `tool_call` events have no `tool_result` citing them as a causal parent.

Pairing provenance: `hyodo/host_adapters/_common.py` builds an event id as
`{host}:{event_name}:{tool_use_id}` when the host supplies `tool_use_id`, and
falls back to a payload digest when it does not. It sets `parent_event_id` to
`{host}:{pre_event_name}:{tool_use_id}` only in the first case, and
deliberately invents no parent in the second.

The reported call ids have the `codex:PreToolUse:exec-…` form, consistent
with the `tool_use_id` path. The adapter therefore had the material to
link and did not drop it. Measured: for all 185, no `PostToolUse` event exists
anywhere in the ledger with the same exec id.

| Check | Result |
| --- | --- |
| matching `PostToolUse` present but unlinked | 0 of 185 |
| orphan is the run's last event | 0 of 185 |
| orphan shares an `args_digest` with another orphan | 61 of 185 |
| tools | 171 `Bash`, 14 `apply_patch` |

The reported orphans occur throughout run progress, rather than only at the
end of a run. This does not establish why the results are missing. The state
is `CALL OBSERVED` with `RESULT UNOBSERVED`. Whether callback delivery, adapter
processing, persistence, or another condition caused the gap is **UNOBSERVED**:
no hook-level failure record is available in this report.

## Finding 3 — intent exists in the schema, but not the inspected hooks

`hyodo/events.py` `EVENT_KINDS` already includes `prompt`, so the ledger
schema carries intent today. `hyodo/connect.py` installs hooks for
`PreToolUse` and `PostToolUse` only and rejects every other hook event name.
At the time of this measurement, `hyodo/host_adapters/codex.py` likewise
mapped only those two.

Codex exposes more. Its `HookEventName` vocabulary, read from the installed
binary, includes `user_prompt_submit` alongside `pre_tool_use` and
`post_tool_use`. That vocabulary alone does not establish a supported, enabled
hook or a working end-to-end intent path.

Two of two runs in this ledger therefore have no recorded intent. Reported as
`missing.runs_without_intent`, that reads as a count of 2; as coverage it is
100%. Under the five-questions model those runs answer Who, What, When, Where
and How, and leave Why unobserved.

At the original audit time, the payload shape of a real
`user_prompt_submit` hook event was **UNOBSERVED**. The follow-up below
records the later observation without changing that historical finding.

### Local candidate follow-up

The Codex adapter now accepts `UserPromptSubmit` through the existing CLI
dispatch. Its field contract is based on the installed Codex 0.155.1 native
`user-prompt-submit.command.input` schema, with isolated adapter and graph
tests. That initial implementation evidence did not establish live delivery.
A subsequent local observation at 2026-09-20T05:59:41Z captured one native
human submission, followed by six directly linked actions and six results.
The ledger, verification API, and existing browser view were checked against
the same event identity. This establishes one local input chain, not coverage
of other seats or a general `hyodo connect` installation guarantee. No
historical requests were reconstructed or inserted.

Prompt bodies are reduced to input digests. Session and turn identity must
come from the host. Transcript paths are not event IDs and must not be placed
in `evidence_refs`. A recorded prompt does not establish acceptance, an
execution contract, fulfillment, or trust.

Tool-result observation now distinguishes a supplied empty response from a
missing, null, or unsupported response using existing metadata tags. An empty
response has a digest; absent data does not. The graph and verification view
carry this distinction without changing lens evaluations or authority.
Historical events without these tags retain `UNOBSERVED` observation state.

## Finding 4 — `apply_patch` input shape is unobserved, so the work is held

An explicit structured path could provide additional classification evidence
for `apply_patch` events, subject to the classifier contract. The sample
reports 14 orphaned calls and 128 unclassified results for this tool. Recording
a path does not restore a missing result or resolve an orphan by itself.

`hyodo/host_adapters/_common.py` reads `tool_input.file_path` and nothing else,
so a call shaped any other way records no path.

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
3. Delivery and persistence evidence explaining the missing `PostToolUse`
   records; the sample alone does not establish dropped callbacks.

`evidence_refs` stay absent until something in the loop has a reason to cite
evidence. That is a product question, not an adapter gap.

## Supplying a requirement comparison

The existing `hyodo event record --file EVENT.json --root PROJECT --json`
entry point accepts a canonical `hyodo.agent-event/v1` event containing
`meta.intent_review` (`hyodo.intent-review/v1`). This is an explicit host
submission, not information inferred from a tool name or a successful exit.

The host must supply the original human prompt event ID in `intent_ref`,
`mode` (`OBSERVED` or `PROJECTED`), `target` (`interpretation`, `action`, or
`outcome`), and checks containing `id`, `dimension`, `basis`, `operator`,
`expected`, `actual`, `unit`, and `evidence_refs`. Dimensions are `goal`,
`scope`, `constraints`, and `completion`. Each evidence reference identifies
an existing result event; missing observations must remain absent or null.
The event's top-level `evidence_refs` also declares its evidence graph links.

Declare `basis: DECLARED` only for an actual user requirement. An agent's
interpretation uses `INFERRED`; hypothetical comparisons use `PROJECTED`.
Neither becomes verified fulfillment merely because the values match.
Record a new comparison after observing the result, preserving the earlier
request and result events. Do not replay missing historical prompts.

The dashboard shows these comparisons per selected run, including each
source, check state, evidence reference, and missing dimension. The detailed
event view retains expected and actual values and comparison history.
This summary does not establish a promise, accepted contract, artifact
verification, or execution authority.
