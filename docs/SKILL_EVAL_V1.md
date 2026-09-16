# Skill Eval v1

The HyoDo Skill Eval oracle does not execute anything. It only judges the
evidence passed to it as input.

The input contains `case`, `execution`, `evidence`, `effect_readback`,
`receipt`, and `authority`. A case's `required_evidence` is not declarative
metadata: it is the set of keys the Evidence Gate actually enforces.

The verdict is one of `PASS`, `FAIL`, `HOLD`, or `UNOBSERVED`.

- `PASS`: execution, effect readback, and the authority boundary were observed
- `FAIL`: a forbidden action, owner mismatch, or authority leakage was observed
- `HOLD`: the receipt reports success but no effect readback exists
- `UNOBSERVED`: the execution or a required piece of evidence could not be read

Every required evidence item must satisfy all of: `observed=true`, a valid
`value`, `freshness=fresh`, a producer, correlation with the current `run_id`
and `execution_id`, and `integrity=verified`.

```text
missing / observed=false / malformed / stale / uncorrelated -> UNOBSERVED
integrity mismatch / tampered                              -> FAIL
receipt success + effect state=PENDING                     -> HOLD
all required evidence present and every invariant holds    -> PASS
```

The `runtime-ownership-001` slice separates the launchd label from the
executable owner. HyoDo holds neither execution authority nor promotion
authority.
