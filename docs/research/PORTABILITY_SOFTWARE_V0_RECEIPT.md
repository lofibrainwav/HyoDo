# Software Portability v0 — final receipt

Status: **run closed**  ·  Software evidence status: **`SOFTWARE_V0_PARTIAL`**  ·
Software arm outcome: **`NO_SOFTWARE_SIGNAL_EARNED`**  ·
Core promotion: **`NOT_ELIGIBLE`**

This receipt records what the Software slice of the portability falsification
pilot measured. It changes no runtime, schema, package, or authority contract.

## Identity

```text
evidence_source_sha    0dbe5ec3bdb02f133b9d33f3ba7b0ed9c0ed4c87
research_artifact_sha  195476a773ddce0cbf1a0e78ffecdfc1e72fcee9
judge_output_sha256    e1f141055a8de4d5ca48d98153d2cb4c57709dc62bda603210090acab8f70490
```

Two SHAs, not one. `research_artifact_sha` is the commit that contains the
runner, fixtures, oracle, candidate, and results together — no file inside that
commit could name it without changing it. A reproducer checks out that commit,
not the source snapshot.

### Advisory state at freeze

Recorded because it was observed, not because it gated anything:

```text
Mutation Evidence - Core Full Run (advisory)   completed / FAILURE
  run 35622037855   15:53:56Z -> 19:37:34Z (3h 43m 38s)
  failed at "Build full-core mutation evidence"
  mutation execution completed; evidence export failed
main check totals   success 20 / skipped 2 / failure 1
                    the single failure is this advisory; required failures 0
```

## Reproduce

```bash
git checkout 195476a773ddce0cbf1a0e78ffecdfc1e72fcee9
python3 scripts/research/portability_v0.py --verify
```

`--verify` re-hashes every source and fixture, re-runs both arms **with
`oracle.json` moved off disk**, requires byte-identical output, re-scores, and
diffs against the committed results. It exits non-zero on any drift. Observed:

```text
verify ok: digests, arm outputs (oracle hidden), score, and metrics all reproduce
```

Limitation: the CLI-derived fixtures (SW-05, SW-10, SW-11, SW-12) freeze the
observed command output. `--verify` checks their frozen digests; it does not
re-execute the CLI, whose output embeds absolute paths.

## Preflight — 12/12 REPRESENTABLE

Every adversarial family in `PORTABILITY_RESEARCH_V0.md:49-60` was matched to a
real repository artifact before any fixture was built. The gate rule was: one
`NOT_REPRESENTABLE` and the arms never run.

| ID | Family | Artifact |
| --- | --- | --- |
| SW-01 | stale evidence | `docs/CURRENT_STATE.md` — line 11 `4.20.2` against line 43 `Public 4.19.5 at snapshot` (2026-09-13) |
| SW-02 | wrong subject binding | `acceptance-join-live-mismatch.json` — `validity=MISMATCH`, `relation=SELF_OTHER_CHECKOUT` |
| SW-03 | replayed / duplicated | `M1_STAGE_OBSERVATION_LIVE_READBACK_2026-09-11.md:100-105` — 6 rows, 3 distinct `observation_id` |
| SW-04 | missing claimed effect | `EVIDENCE_RECONCILIATION_2026-09-20.md` — 316 of 4,965 calls `UNOBSERVED` |
| SW-05 | unsupported conclusion | `hyodo score` — `REVIEW_SIGNAL_STRONG` + "human approval required" |
| SW-06 | ambiguous authority | `test_policy_self_report_boundary.py:75-87` |
| SW-07 | incomplete provenance | `graph-v2-join/unresolved-parent.json` |
| SW-08 | conflicting evidence | `dashboard-truth-cases.json` — `withheld_allow`: recorded `ALLOW` / presentable `UNOBSERVED` |
| SW-09 | missing human decision | `test_cli_policy_check.py` + `factory-loop.sh` |
| SW-10 | valid bounded support | `factory-loop.sh --dry-run` — 3/3 surfaces, exit 0 |
| SW-11 | valid + limitation | `hyodo check .` — 4/4 gates ran, exit 0 |
| SW-12 | near miss | `hyodo check <empty>` — 0/0 gates, exit 2 |

SW-06 and SW-09 are executable contracts, so they cleared a stricter bar: exact
identity, semantic alignment with the bounded claim, **focused execution
readback (PASS)**, and a written record of what the assertion does not prove.

A first pass searched only `examples/` and concluded those two families had no
artifact. That was wrong — a statement about the adequacy of a search, not about
the repository. The correction is preserved in `preflight.json`.

## Oracle

Frozen before either arm ran, with precedence `UNOBSERVED` > `AMBIGUOUS` >
`BLOCKED` > `SUPPORTED`. Precedence selects the scored state without discarding
the rest: every further condition observed is kept in `secondary_findings`.

`BLOCKED` here is a local research label. It is not a HyoDo or KINGDOM action
gate and must not be promoted outside this receipt.

| ID | primary | secondary |
| --- | --- | --- |
| SW-01 | `BLOCKED` | |
| SW-02 | `BLOCKED` | |
| SW-03 | `BLOCKED` | |
| SW-04 | `UNOBSERVED` | |
| SW-05 | `BLOCKED` | |
| SW-06 | `AMBIGUOUS` | `BLOCKED` |
| SW-07 | `BLOCKED` | |
| SW-08 | `BLOCKED` | |
| SW-09 | `UNOBSERVED` | `AMBIGUOUS` |
| SW-10 | `SUPPORTED` | |
| SW-11 | `SUPPORTED` | |
| SW-12 | `UNOBSERVED` | |

## Results

| ID | oracle | baseline | candidate |
| --- | --- | --- | --- |
| SW-01 | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| SW-02 | `BLOCKED` | `BLOCKED` | `AMBIGUOUS` |
| SW-03 | `BLOCKED` | `BLOCKED` | **`SUPPORTED`** |
| SW-04 | `UNOBSERVED` | `UNOBSERVED` | `UNOBSERVED` |
| SW-05 | `BLOCKED` | `BLOCKED` | `AMBIGUOUS` |
| SW-06 | `AMBIGUOUS` | `AMBIGUOUS` | `AMBIGUOUS` |
| SW-07 | `BLOCKED` | `BLOCKED` | `AMBIGUOUS` |
| SW-08 | `BLOCKED` | `BLOCKED` | **`SUPPORTED`** |
| SW-09 | `UNOBSERVED` | `AMBIGUOUS` | `UNOBSERVED` |
| SW-10 | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` |
| SW-11 | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` |
| SW-12 | `UNOBSERVED` | `UNOBSERVED` | `UNOBSERVED` |

```text
                baseline   candidate   delta
false_green            0           2      +2
false_block            0           0       0
ambiguity              1           3      +2
```

## Structural verification proxies

```text
                              baseline   candidate
required_source_lookups             13          13
required_cross_checks                8          12
required_context_boundaries         13          12
unresolved_required_fields           0          17
instrumentation_steps                4          12
adapter_exception_cost              12           0
```

Counted by the runner from the run against a rubric frozen with the candidate.
Nothing here is estimated, and nothing here is described as human behavior.

```text
human_verification_time = UNOBSERVED
  order effects and AI-operator execution are not human study data
wrong_reliance_events   = UNOBSERVED
  reliance is a human behavior; this run had no human subject
```

A real burden result needs a counterbalanced human study. That is out of scope
here and is named as a limitation rather than approximated.

## Decision rule

Frozen in `candidate.json` before the arms ran, and applied independently by the
judge to the same numbers:

```text
candidate false_green <= baseline          2 <= 0     FAIL
candidate false_block <= baseline          0 <= 0     pass
candidate ambiguity   <= baseline          3 <= 1     FAIL
at least one burden metric improves        yes        pass
no burden metric worsens                   3 worsen   FAIL
adapter_exception_cost not increased       12 -> 0    pass
HARD FLOOR candidate false_green == 0      2          FAIL

=> NO_SOFTWARE_SIGNAL_EARNED
```

## What the null result means

The candidate's two false-greens are SW-03 (replay) and SW-08 (contradiction).
In both, **every one of the eight fields is clean**: binding is `id_match`,
freshness is `at_or_after`, the effect was observed. The evidence is still
duplicated in one case and self-contradictory in the other.

So the eight fields — protocol questions 1 through 7 — have no axis on which a
replayed observation or a pair of contradictory records differs from a sound
one. The baseline caught both, using per-fixture branches that read native keys
(`rows_after_second_pass` against `distinct_observation_ids`; `recorded` against
`presentable`).

The candidate was not useless. It removed every domain-specific branch (12 to
0), and it beat the baseline on SW-09, where `effect_observed` captured that the
item never proceeded and the baseline's branch did not. It bought that with 17
unresolved field slots and triple the instrumentation.

`PORTABILITY_RESEARCH_V0.md:141-144` warns that a small apparent core with large
domain-specific exception code is a failed abstraction. This run measured the
mirror image: the exception code genuinely vanished, and the core became blind
to two defect classes. Cheap and wrong is not an improvement over expensive and
right.

This says nothing about whether some other primitive would do better. It says
this one, pre-registered and measured, did not.

## Independent judge

Verdict **`SOFTWARE_V0_PARTIAL`** — full detail in
[`PORTABILITY_JUDGE_RECEIPT_V0.md`](./PORTABILITY_JUDGE_RECEIPT_V0.md).

The judge confirmed every digest, fixture honesty across all 12, oracle-freedom
of both arms, reproducibility by running `--verify`, the decision-rule outcome
derived independently, and the package boundary. It re-derived the oracle from
source and agreed on 11 of 12.

Two findings remain open and are preserved, not resolved:

1. **SW-09 disagreement.** Frozen oracle `UNOBSERVED`, independent judge
   `BLOCKED`, baseline arm `AMBIGUOUS` — three readings of one piece of
   evidence. The oracle is not amended; editing it to match a later reading
   would destroy the property that makes it an oracle. The finding is that the
   "missing human decision" family does not partition cleanly into four states:
   whether a halted action is *unmeasured* or *positively contradicted* is a
   real boundary question in the definitions.

2. **SW-03 preflight gap.** A stronger executable source exists at
   `tests/test_orchestration_observation.py:115`
   (`test_duplicate_sidecar_for_event_is_visible_and_first_wins`, verified
   present and passing) that the preflight search did not surface. The shipped
   fixture is honest and `REPRESENTABLE`, but it is prose describing the
   measurement where a test mechanically enforcing it was available. The fixture
   is **not** swapped — rebuilding it after reading the review would fit the
   experiment to its own review. This is the `examples/`-only failure recurring:
   the search widened only for the families that had nothing.

## Null results and limitations preserved

- `NO_SOFTWARE_SIGNAL_EARNED` — the pre-registered primitive did not earn a
  signal on the Software slice.
- SW-09's three-way disagreement is unresolved.
- SW-03's stronger source was found after the freeze and not adopted.
- `human_verification_time` and `wrong_reliance_events` are `UNOBSERVED`.
- CLI fixtures are digest-verified, not re-executed.
- One operator, one run, twelve fixtures, one domain. The fixture count is a
  falsification pilot, not evidence of generality.

## Final state

```text
Run lifecycle             RUN_CLOSED
Software lane status      CLOSED (judge PARTIAL; two open findings preserved)
Software arm outcome      NO_SOFTWARE_SIGNAL_EARNED
Candidate arm             MEASURED
Professional              UNOBSERVED
Creative                  UNOBSERVED
Core promotion            NOT_ELIGIBLE
HyoDo 4.20.2              FROZEN
runtime change            NONE
schema change             NONE
```

`CLOSED` is a scheduling fact about this run. It does not mean `GREEN`. Core
promotion was `NOT_ELIGIBLE` before the run began — survival rule #1 requires a
primitive to be independently needed in all three domains, and two of them are
`UNOBSERVED` — so no outcome here could have changed it.

---

Software Portability v0 is closed for the frozen 12-fixture pilot. It
establishes only what the Software slice measured. Professional and Creative
remain UNOBSERVED, and no HyoDo Core primitive is promoted from this result
alone.
