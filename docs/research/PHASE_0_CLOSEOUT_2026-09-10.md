# Phase 0 closeout

Phase 0 asked whether real execution can be observed well enough to build on.
It closes here with its residual named rather than quietly carried.

`CLOSED` means measured and read back on `main`. `ACCEPTED RESIDUAL` means a
gap that stays open on purpose, because closing it would mean manufacturing
evidence. `KNOWN CAPABILITY GAP` means the producer's own limit, recorded so it
can be worked on deliberately instead of discovered again.

## CLOSED

| item | evidence |
| --- | --- |
| SSOT / ROADMAP drift gate | `ROADMAP.md` had been three releases behind; `check_roadmap_sync` fails closed on a stale baseline or a missing release entry |
| public release evidence reconciliation | Evidence Pack v1's five `HOLD` rows measured against the published 4.18.0 artifacts and appended, not overwritten |
| target-run isolation capability separation | KINGDOM capability `OBSERVED` (#779); Run #3's use of it `UNOBSERVED`, kept as two rows |
| Codex real-host callback | an installed `codex-cli 0.154.0` emitted its own hooks; `host:codex` on two canonical events |
| output truth digest | `tool_response` mapped to `io.output_digest`; digest recomputed from the tool's actual output and matched |
| causal parent | `PostToolUse` names the `PreToolUse` it answers; resolves as a graph edge, `unresolved_ref` when the call is absent |
| host model provenance | `meta.model` carries what the host reported, on both halves of a call |
| sensor coverage matrix | read from the producer, the contract and the bridge -- `SENSOR_COVERAGE_MATRIX.md` |

## ACCEPTED RESIDUAL

**Historical Run #2 / #2b standalone receipt files are `MISSING`.**

Both runs exist as prose in the technical roadmap. No standalone receipt was
ever written, and this stays open deliberately:

- copying prose into receipt files changes the format of a claim without adding
  a measurement;
- executing a run today would not produce a Run #2 or #2b receipt -- it would
  produce a new run wearing an old name;
- so the past is not reconstructed and not pretended to be reconstructed.

Phase 0 is not held open for this. A residual named in the closeout is honest;
a residual carried silently into the next phase is not.

## KNOWN CAPABILITY GAPS

Producer limits, not HyoDo defects. Recorded as inputs to later
capability-gap work, and **not to be repaired merely to make Phase 0 look
greener**:

| gap | cause |
| --- | --- |
| stage boundaries excluded | emitted as `execution:trace:stage-started` / `stage-finished`, dropped by the bridge contract's allowlist |
| reviewer verdict excluded | emitted on `governance:review:*` and `work:review:*`, outside the allowlisted `execution:trace:*` |
| iteration absent from the trace payload | a task iterates up to three times in producer logic; `task-finished` carries no attempt information |
| retry / rework / resource conflict | no producer vocabulary at all; the contract's reads were deleted rather than left permanently false |
| producer model metadata | KINGDOM's trace channels carry no model or provider field; `UNSUPPORTED`, unlike the Codex case which was a missed read and was repaired |

## Anti-drift repair candidate

The observation contract's comments state that `coder.js` never sets `ok` or
`status`, and that failure mapping is therefore "presently inert". The current
producer sends both, on `task-finished` and `run-finished`. The comment is
`CONTRADICTED` by producer reality.

This is a comment correction, and it belongs on its own. It must not be bundled
with a change to what the code does -- a stale comment and a behaviour change
landing together is how the next reader loses the ability to tell which was
which.

## What closing Phase 0 does not mean

It does not mean observation is complete. The gaps above are real and listed.
It means the baseline is measured, its limits are written down, and the next
phase starts from a record that says what is true rather than what would look
finished.
