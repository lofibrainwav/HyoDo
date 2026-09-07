# Score derivation (`hyodo score --from-check`)

`hyodo score` computes the HyoDo Integrity Score from five pillar values
(Benevolence, Truth, Goodness, Hyo, Beauty) that the caller supplies as
`0.0-1.0` flags. Nothing about that formula changes here. This document
covers a separate, additive path: `hyodo score --from-check`, which derives
those same five inputs from what `hyodo check`, `hyodo safe`, and the
test-integrity scan already observe about a checkout, in-process (no
subprocess calls), with full provenance for every number it produces.

This stays a **review signal**, never an approval — see `hyodo score --help`.

## Rule table

`hyodo/score_derive.py` defines `PILLAR_RULE_TABLE`, a `rule_id -> (pillar,
max_weight, description)` mapping. Every provenance row a derivation can
emit carries a `rule_id` that is a key in this table; a test
(`tests/test_score_derive.py::test_rule_table_is_total`) enforces that the
table only ever targets one of the five known pillars, and a second test
enforces that every rule_id a real derivation emits is a table entry.

| rule_id | pillar | max weight | source |
|---|---|---|---|
| `test_integrity.observed_ratio` | Truth | 70 | test-integrity scan (`total_tests` / `vacuous_tests`) |
| `check.truth_gate` | Truth | 30 | `hyodo check` Truth gate (pyright) PASS/FAIL |
| `safe.high_findings` | Goodness | 50 | `hyodo safe` high-severity finding count (penalty) |
| `safe.medium_findings` | Goodness | 30 | `hyodo safe` medium-severity finding count (penalty) |
| `safe.coverage` | Goodness | 20 | `hyodo safe` scanned/scannable file ratio |
| `check.beauty_gate` | Beauty | 100 | `hyodo check` Beauty gate (ruff lint + format) PASS/FAIL |
| `check.readme_present` | Benevolence | 40 | README.md present (not yet emitted by `hyodo check` — see Known gaps) |
| `check.start_hint_present` | Benevolence | 30 | onboarding entry point documented (not yet emitted) |
| `check.help_text_present` | Benevolence | 30 | CLI help text present (not yet emitted) |
| `hyo.config_present` | Hyo | 34 | `.hyodo/gates.toml` (Bring-Your-Own-Gates) present |
| `hyo.connect_wired` | Hyo | 33 | at least one host wired via `hyodo connect` |
| `hyo.ledger_present` | Hyo | 33 | `.hyodo/mcp-access.jsonl` access ledger present |

A pillar's value is `sum(contribution for observed rules) / sum(max_weight
for observed rules) * 100`, i.e. it is rescaled over whichever of its own
rules were actually observed — an evidence gap on one rule does not drag
the pillar toward 0.

## Coverage semantics

Each pillar reports one of three coverage states, alongside its value:

- **OBSERVED** — every rule for that pillar fired.
- **PARTIAL** — some but not all of the pillar's rules fired; the value is
  rescaled over the rules that did.
- **UNOBSERVED** — no rule for that pillar fired. The value is `None`, never
  a smuggled 0 or 100. `hyodo score --from-check` prints this pillar as
  `UNOBSERVED` and excludes it from the Eternity geometric-mean term.

When every one of the five pillars is `OBSERVED` (after any `--truth`-style
override), `hyodo score --from-check` calls the unmodified
`calculate_hygook_v5_score` and prints the usual F/S/TOTAL. When one or more
pillars are `UNOBSERVED`, the command:

- prints Eternity (S) computed only over the pillars that *were* observed
  (`geometric_mean_observed`, not the five-pillar formula),
  marks Eternity/F as `PARTIAL`, and lists which pillars were excluded;
- does **not** print a TOTAL score, since the formula requires all five
  inputs — it tells the caller which pillar(s) to supply explicitly
  (`--benevolence 0.8`, etc.) to complete it.

## Overrides

Any of `--benevolence` / `--truth` / `--goodness` / `--hyo` / `--beauty`
(and the legacy `--serenity` / `--eternity` aliases) may be passed alongside
`--from-check`. Each one replaces that single pillar's derived value; the
replacement is recorded as a provenance row with `rule_id
"override.<pillar>"`, `source "cli-flag"`, and `override: true` (both on the
row and on the pillar result), so `--json` output and the printed table both
show that the number came from a flag, not from evidence.

## Known gaps

`hyodo check` does not currently emit onboarding/DX signals (README
presence, an `hyodo start` hint, CLI help-text presence). Per the mapping
this document specifies, Benevolence therefore reports `UNOBSERVED` under
`--from-check` until `hyodo check` emits those signals — it is not defaulted
to a neutral or optimistic number. Wiring `hyodo check` to emit
`readme_present` / `start_hint_present` / `help_text_present` would let this
pillar move to `PARTIAL`/`OBSERVED` without any change to
`hyodo/score_derive.py`'s rule table.

## Calibration

Ran `hyodo score --from-check --json` (commit `b056cea3c406a9189e64344d0e5614d2914ebfbc`)
against three targets:

| Target | Benevolence | Truth | Goodness | Hyo | Beauty | Eternity | Coverage |
|---|---|---|---|---|---|---|---|
| HyoDo repo itself | UNOBSERVED | 100.0 (OBSERVED) | 19.8 (OBSERVED) | 33.0 (OBSERVED) | 100.0 (OBSERVED) | 5.7664 | PARTIAL |
| `examples/fde-evidence-spine` | UNOBSERVED | 0.0 (PARTIAL) | 100.0 (OBSERVED) | 0.0 (OBSERVED) | 0.0 (OBSERVED) | 1.7783 | PARTIAL |
| empty temp directory | UNOBSERVED | 0.0 (PARTIAL) | 100.0 (PARTIAL) | 0.0 (OBSERVED) | 0.0 (OBSERVED) | 1.7783 | PARTIAL |

Notes on reading this table:

- **Benevolence** is `UNOBSERVED` in all three rows — see Known gaps above;
  this is expected, not a bug in the run.
- The HyoDo repo's own **Goodness** (19.8) reflects that `hyodo safe`
  scanning the full HyoDo tree (fixtures included) finds high/medium
  findings above the penalty cap; this is `hyodo safe`'s own early-warning
  behavior, unchanged by this feature.
- **Truth** is `PARTIAL` for the example and the empty directory because
  neither has a Python package under a `hyodo/` directory for pyright to
  check and the test-integrity ratio rule intentionally does not fire when
  `total_tests == 0` (a "zero tests, zero vacuous" project must not read as
  a perfect 1.0).
- None of the three rows has a TOTAL, since Benevolence is `UNOBSERVED` in
  all of them — pass `--benevolence <value>` to complete the formula on any
  of them.

Re-run with `hyodo score --from-check --root <target> --json` to reproduce
or refresh this table against a newer commit.
