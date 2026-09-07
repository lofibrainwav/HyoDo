# Test integrity (Phase 1-E)

`hyodo check` runs a fifth, native computation alongside its four gates: a
zero-model, zero-judgment AST scan of whether the project's own tests observe
anything. It answers "does the type checker pass" (Truth's existing pyright
gate) *and* "do the tests that are supposed to prove correctness actually
observe anything" — a fact about the AST, not an opinion about intent.

```text
hyodo check --strict-tests
```

## What is observed

`hyodo/test_integrity.py` walks `test_*.py`/`*_test.py` files (pytest's own
discovery convention) for `test_*` functions — module-level or inside a
`Test*`-named class — and flags four AST-visible categories, reusing
`hyodo/safe/anti_gaming.py`'s existing rule ids (HYO-SAFE-010/011/012) where
its findings overlap:

| Category | Trigger |
| --- | --- |
| `no_assertion` | no `assert`, no `assert*`-named call (`self.assertEqual`, `np.testing.assert_*`), and no `pytest.raises`/`pytest.warns` context manager anywhere in the function |
| `constant_assertion` | every `assert` in the function is a literal-truthy or equal-literal comparison — only flagged when *every* assertion is trivial |
| `no_target_reference` | the function never names a symbol the module imported from the project's own package; suppress a known false positive (fixture-only tests) with `# hyodo: allow-vacuous` on the `def` line |
| `unexplained_skip` | `@pytest.mark.skip`/`skipif`/`xfail` with no `reason=` |

`vacuous_tests` counts unique functions flagged `no_assertion` or
`constant_assertion` only — the two categories that mean a test genuinely
cannot have caught a regression. `no_target_reference` and `unexplained_skip`
still appear in `findings` but are not counted toward that number.

## What UNOBSERVED means

A project with no discoverable `test_*.py`/`*_test.py` files reports
`total_tests: 0`, `vacuous_tests: 0` — that is UNOBSERVED, not a pass and not
a failure. `hyodo check` prints `Test integrity: UNOBSERVED (no
pytest-convention tests found)` in that case, matching the same "unenforced is
not the same as passing" rule the rest of HyoDo applies to policy and ledger
evidence.

## Exit contract

Without `--strict-tests`, the scan is purely additive: one line in text mode
and a `test_integrity` object in `check --json`
(`scanned_files`/`total_files`/`total_tests`/`vacuous_tests`/`findings`). It
never joins the `results`/`executed`/`failed` gate list, so `check`'s existing
0/1/2 exit contract and its "N/4 gates ran" counting are unchanged.

With `--strict-tests`: if the Truth gate (pyright) would otherwise `PASS` but
`vacuous_tests > 0`, that gate's status flips to `FAIL` with a combined
message. This makes vacuous tests fail the Truth gate without inventing a
fifth named gate that would change `ran`/`total` for every existing consumer.

## Mutation testing (BYOG, not new code)

1-E does not ship a mutation-testing tool as new public API. HyoDo's own CI
already treats mutation testing as advisory evidence
(`.github/workflows/mutation.yml`, `cosmic-ray`, `scripts/mutation-score.py`);
an adopter absorbs the same signal as a Bring-Your-Own-Gate:

```toml
schema = "hyodo.gates/v1"

[gates.mutation-score]
pillar = "goodness"
# Wrap cr-rate (or mutmut's own summary) in a small script that exits
# non-zero when the surviving-mutant share is above the threshold the
# operator has explicitly adopted for this project.
command = "scripts/mutation-gate.sh --max-survived-pct 15"
timeout = 1800
```

This keeps mutation testing exactly where HyoDo's own CI keeps it today:
advisory, operator-owned, and never silently converted into a threshold HyoDo
invented on the adopter's behalf.

## Known limitation

`no_target_reference` is a heuristic with a known false-positive shape:
fixture-driven tests that only reference the project's package through a
fixture parameter. That is an accepted cost, not a bug to fix by tracing
fixture bodies (which would require import-graph resolution beyond a
single-file AST walk) — use `# hyodo: allow-vacuous` on the `def` line.
