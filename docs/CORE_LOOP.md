# HyoDo Core Loop Contract

This document is the canonical contract for HyoDo's continuous-improvement
loop. It describes an evidence and trust loop; it does not grant execution
authority to HyoDo or replace the integrating host's orchestration.

## Core loop

Every HyoDo improvement cycle follows this ordered path:

```text
Human Intent
→ Goal
→ Observe Reality
→ Six independent lens measurements
   ├─ 眞 Truth
   ├─ 善 Goodness
   ├─ 美 Beauty
   ├─ 仁 Benevolence
   ├─ 孝 Hyo
   └─ 永 Eternity
→ Gap / Friction / Unknown
→ Smallest Useful Improvement
→ Verify
→ Close
→ Lesson Candidate
→ Validate / Generalize
→ Shadow Rule / Dry Run
→ Muscle Memory
→ Better Next Action
→ Repeat
```

The six virtues are independent evidence lenses measured as a fan-out after
reality is observed, then brought together for gap and friction analysis.
They are not a serial checklist and do not imply that one lens depends on the
previous lens. HyoDo is the whole loop; 孝 is one lens within it. A score,
receipt, or lens result is not authority and must not silently authorize an
action in an integrating host.

### Required records

| Stage | Required fact |
| --- | --- |
| Human Intent | The user's stated need, actor, and capture provenance |
| Goal | A bounded outcome, owner, scope, done condition, and expiry/review date |
| Observe Reality | Timestamped source observations and explicit unavailable signals |
| Six lenses | Evidence, observation state, and rationale for each of 眞善美仁孝永 |
| Gap | Known mismatch, friction, uncertainty, and affected owner |
| Improvement | Smallest reversible change and rollback path |
| Verify | Fresh evidence tied to the changed source/runtime, not a historical receipt |
| Close | WROTE → WIRED → CONSUMED → VERIFIED → SETTLED → RETIRED → CLEAN READBACK |
| Lesson | Candidate evidence, provenance, owner, and proposed next action |

`UNOBSERVED` remains distinct from both `PASS` and `FAIL`. A missing tool is
an unobserved measurement condition unless the tool was actually executed and
returned a failure.

## Lesson promotion and Muscle Memory

A lesson may advance only through this state sequence:

```text
OBSERVATION
→ LESSON_CANDIDATE
→ VALIDATED_LESSON
→ SHADOW_RULE
→ DRY_RUN / REHEARSAL
→ MUSCLE_MEMORY
→ DEFAULT / GUARD
```

Promotion requires evidence, source/runtime provenance, an accountable owner,
a rollback procedure, and an expiry or review condition. One incident may
create a `LESSON_CANDIDATE`; it cannot directly create a default or guard.

- BB owns durable lessons and continuity projections.
- KINGDOM owns execution, agency, and action authorization.
- HyoDo owns evidence quality, validation, and trust in the promotion.

An invalid or stale measurement is not eligible for promotion. A promoted
rule remains reviewable and reversible; `MUSCLE_MEMORY` is not permanent truth.

## Closure rule

```text
DONE =
WROTE
→ WIRED
→ CONSUMED
→ VERIFIED
→ SETTLED
→ RETIRED
→ CLEAN READBACK
```

`DONE` is not synonymous with test green, merge, or deploy. At closeout,
every warning, skip, partial, stale, drift, orphan, temporary artifact,
worktree, and runtime-slot finding must be one of:

- `RESOLVED`
- `CORRECTLY_RECLASSIFIED`
- `EXPLICITLY_DEFERRED` with owner, reason, and review condition

The closeout receipt must report these counts:

```text
unresolved_warning = 0
unowned_dirty_unique = 0
unexplained_orphan = 0
stale_pointer = 0
```

An explicit deferral is reported separately from `DONE`. Suppression, output
filtering, `|| true`, and exit-code masking are never valid closure evidence.
