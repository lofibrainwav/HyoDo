# Independent Judge receipt — Software Portability v0

Verdict: **`SOFTWARE_V0_PARTIAL`**

- Contract: [`PORTABILITY_JUDGE_CONTRACT_V0.md`](./PORTABILITY_JUDGE_CONTRACT_V0.md)
  (frozen in the measurement commit, before this verdict existed)
- `evidence_source_sha`: `0dbe5ec3bdb02f133b9d33f3ba7b0ed9c0ed4c87`
- `research_artifact_sha`: `195476a773ddce0cbf1a0e78ffecdfc1e72fcee9`
- `judge_output_sha256`: `e1f141055a8de4d5ca48d98153d2cb4c57709dc62bda603210090acab8f70490`

The judge ran in a fresh context with no access to the builder's verdict,
recommendation, or desired outcome. The digest above is of the verdict summary
as received, so a reader can distinguish a faithful transcription from an edited
one.

## What the judge confirmed

- **Digests.** All 10 native sources recomputed at `evidence_source_sha` match
  `MANIFEST.json`. No drift.
- **Fixture honesty.** All 12 fixtures represent their sources faithfully:
  quotes verbatim, counts matching, no selection that reverses a source's
  meaning.
- **Oracle-freedom.** `run_arm()` never opens `ORACLE_PATH`; only `score()`
  does. `--verify` reproduced both arms byte-identically with the oracle file
  hidden, and the working tree was clean afterwards.
- **Decision rule.** Applied by hand to the measured numbers, the judge reached
  `NO_SOFTWARE_SIGNAL_EARNED` independently, matching `metrics.json`.
- **Package boundary.** Primary diff falls entirely inside `docs/research/**`
  and `scripts/research/**` — no HOLD. Secondary diff against `v4.20.2` for
  `hyodo schemas VERSION pyproject.toml` is **empty**.
- **Domains.** Professional and Creative remain `UNOBSERVED`; no artifact claims
  otherwise.

## Open finding 1 — SW-09 oracle disagreement

Three independent readings of the same evidence disagree, and all three are
preserved rather than reconciled:

```text
bounded claim: "the item may proceed without a separate operator decision"
evidence:      loop_halts_on_ask=true, cli_exit_code_for_ask=3,
               operator_decision_recorded=false

frozen oracle   UNOBSERVED   the claimed effect - the item proceeding -
                             was never measured
independent     BLOCKED      the loop halting is positive evidence that it
judge                        did not proceed, i.e. active contradiction
baseline arm    AMBIGUOUS    ASK defers to an operator and no operator acted,
                             so the approval boundary is unresolved
```

The oracle is **not** amended. It was frozen before the arms ran, and editing it
to match a later reading would destroy the only property that makes it an
oracle. The disagreement is the finding.

What it indicates: the "missing human decision" family does not partition
cleanly into the four states. Whether a halted action counts as *unmeasured*
(nothing happened to observe) or *contradicted* (we positively observed it not
happening) is a real boundary question in the state definitions, not a
tie-breaking accident — the precedence ladder was applied identically by both
parties and still produced different answers, because they disagreed about which
conditions the evidence satisfies at all.

## Open finding 2 — SW-03 preflight completeness gap

The judge found a stronger executable source for the replay family that the
preflight search did not surface:

```text
tests/test_orchestration_observation.py:115
  test_duplicate_sidecar_for_event_is_visible_and_first_wins
  asserts issues == [{"observation_id": "obs-j-2",
                      "reasons": ["duplicate_observation_event_id:J"]}]
```

Verified independently: the test exists at that line, mechanically exercises
duplicate-id detection and first-occurrence-wins through `join_adapter_events()`,
and passes (29 passed across the three policy/observation test files).

The shipped SW-03 fixture is not wrong — it is `REPRESENTABLE`, and the judge
confirmed it represents its source honestly. But it is a **prose narrative that
describes** the duplicate-row measurement, where an **executable contract that
mechanically enforces** it was available. `preflight.json`'s
`rejected_alternative` for SW-03 lists only the graph-v2-join cycle fixtures and
never considered this test.

This is the same failure mode as the earlier `examples/`-only search, recurring
after it was supposedly corrected: the search scope widened to `tests/` for the
two families that had nothing, and was not re-run for the families that already
had *something*. A source that is good enough stops the search.

The fixture is not swapped. Rebuilding SW-03 after seeing the judge's report
would be fitting the experiment to its review.

## Why PARTIAL and not GREEN or INVALID

Not `INVALID`: there was no leakage, no fixture dishonesty, no scope violation,
and reproducibility was confirmed by execution rather than by assertion. The
experiment produced an honest negative result.

Not `GREEN`: `GREEN` should mean no material open questions, and two remain —
an unresolved disagreement about SW-09's state and a demonstrated incompleteness
in the preflight search for SW-03.

`PARTIAL` closes the run. It does not reopen the Software lane.
