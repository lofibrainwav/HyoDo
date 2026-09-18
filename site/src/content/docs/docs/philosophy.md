---
title: From values to evidence
description: How HyoDo turns its reference values into observable evidence, clear uncertainty, and bounded decisions.
---

## 1. Why this exists

When an AI says "done," HyoDo helps show what was checked and what remains
unknown. It is an open framework for examining human–AI work through evidence,
not a moral judge or an agent runtime. HyoDo records what it can observe; the
integrating host still owns orchestration and action authority.

## 2. Six reference values

| Pillar | KO / Hanja | Technical meaning | Evidence |
| --- | --- | --- | --- |
| Truth | 진 / 眞 | Type / static correctness | Command gate |
| Goodness | 선 / 善 | Tests + safety stability | Command gate + `safe` |
| Beauty | 미 / 美 | Lint / format | Command gate |
| Benevolence | 인 / 仁 | Public-surface integrity | Native AST |
| Hyo | 효 / 孝 | Consent + context + privacy | Policy + host/access ledger |
| Eternity/Yeong | 영 / 永 | Long-term continuity evidence | History ledger |

Command gates (Truth, Goodness, Beauty) run tools the project already owns —
`hyodo init` absorbs them into `.hyodo/gates.toml`. Native collectors
(Benevolence, Hyo, Yeong) are never replaced by a shell command; when they
are unavailable, they are reported as "Not measured," not silently skipped.

The philosophical scope of Benevolence (仁) includes other-awareness,
relationship awareness, and sensitivity to participants, roles, and context.
Its current measurable proxy is narrower: public usability, API/onboarding
clarity, and user-facing failure visibility. Public usability is one proxy for
仁, not 仁 itself.

In HyoDo, Hyo (孝) is the idea that technology should respect people's time,
choices, and relationships, carry its share of the burden, and preserve
protective friction when it prevents harm. Current proxies include consent,
context alignment, privacy/data protection, and observed friction or
intervention signals. These proxies do not measure total human cost, and HyoDo
does not define a calibrated friction score or a general evaluator for all six
values.

```text
MeasuredProxy_仁 ⊂ Scope_仁
MeasuredProxy_孝 ⊂ Scope_孝
```

Neither proxy is authority. Both remain review signals with explicit
`OBSERVED` / `PARTIAL` / `UNOBSERVED` state.

### Existing score-command compatibility

- **CLI display name:** HyoDo Integrity Score.
- **Legacy command labels:** Six-Virtue Model; Trinity Gates subset.
- **Current implementation status:** the command retains the older five-input
  geometric-mean method for compatibility while HyoDo's replacement evaluation
  model is being updated; a general per-axis evaluator is not yet in the public
  package.

HYOGOOK V5 is the internal name for that older method, not HyoDo's current
evaluation model. The public CLI label remains HyoDo Integrity Score for
compatibility; HyoDo does not define its six reference values as one canonical
score.

## 3. What a score means

HyoDo does not turn its six reference virtues directly into one canonical
score. The reference model keeps an evaluation's value, confidence, evidence,
and observation state distinct, but the current public package does not yet
implement a general per-axis evaluator. Missing evidence remains
`UNOBSERVED`. That means there is not enough evidence to say whether a check
passed or failed; it is neither a pass nor a failure. The current
`hyodo score` command still combines five inputs with a geometric mean and
floors zero inputs for historical compatibility. **HYOGOOK V5** is the
internal name for that older calculation. It is advisory and is not HyoDo's
current evaluation model.

`--partial` allows missing pillars and adds `SIGNAL_CONFIDENCE_WEAK`. It
does not invent a strong signal via a silent fill-in of 1.0 for whatever was
not measured.

### Deriving the five inputs (`hyodo score --from-check`)

The legacy `hyodo score` normally requires the caller to supply all five V5
pillar
values by hand. `hyodo score --from-check [--root R] [--json]` derives
those same five inputs instead, in-process (no subprocess calls), from
what `hyodo check`, `hyodo safe`, and the test-integrity scan already
observed about a checkout. `hyodo/score_derive.py` defines a literal
`PILLAR_RULE_TABLE` (`rule_id -> pillar + max weight`) so every number has
a named source, and each pillar reports its own coverage —
`OBSERVED` / `PARTIAL` / `UNOBSERVED` — alongside its value. An
`UNOBSERVED` pillar reports `None`, never a smuggled 0 or 100, and is
excluded from the legacy harmony aggregate term rather than defaulted; when
any pillar is `UNOBSERVED`, the command withholds the combined TOTAL score
and names which pillar(s) still need an explicit `--benevolence 0.8`-style
flag to complete it. The legacy compatibility formula is unchanged
by `--from-check` — it only proposes inputs — and the command still prints
"review signal, not automatic approval." See `docs/SCORE_DERIVATION.md`
for the full rule table and a calibration run.

## 4. What HyoDo does today

The mathematics above is what an optional review score does. The exit codes
below are what every HyoDo command does, always, whether or not scoring is
in use:

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event validate` | `0` valid · `1` invalid · `2` unreadable input |
| Policy result | `0` ALLOW · `1` DENY · `2` UNOBSERVED · `3` ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

Policy results come from `event record --policy` and `policy check`; an invalid
event can stop before policy evaluation.

The policy gate speaks in four decision words, documented directly in
`hyodo/policy.py`:

```python
"""Local policy gate for agent events (FDE Evidence Spine).

Policy is loadable from ``.hyodo/policy.toml`` (schema ``hyodo.policy/v1``).
Missing or malformed policy is **unobserved**, never silent ALLOW.

HyoDo emits a decision object; the agent runtime must enforce DENY.
"""

decision: str  # ALLOW | DENY | ASK | UNOBSERVED
```

`ASK` is now emitted when policy evaluation observes an external variable that
needs an operator decision. `ALLOW`, `DENY`, and `UNOBSERVED` remain live, and
trust grants are capped by the tracked policy configuration. See the
[Roadmap](/docs/roadmap/) for the 4.13.0 development cycle.

## Next

- [Quickstart](/docs/quickstart/)
- [Roadmap](/docs/roadmap/)
- [Trust](/docs/trust/)
