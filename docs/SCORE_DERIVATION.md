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
| `check.readme_present` | Benevolence | 40 | `hyodo/dx_signals.py::collect_dx_signals` — non-empty README.md present |
| `check.start_hint_present` | Benevolence | 30 | `collect_dx_signals` — onboarding start/setup command documented |
| `check.help_text_present` | Benevolence | 30 | `collect_dx_signals` — CLI help text present |
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

`hyodo check` now emits the three onboarding/DX signals Benevolence
consumes, via `hyodo/dx_signals.py::collect_dx_signals`:

- **`readme_present`** — a `README.md` (case-insensitive `readme.*`
  accepted) exists at the project root and is non-empty (> 200 bytes of
  stripped text).
- **`start_hint_present`** — the README, `CONTRIBUTING.md`,
  `docs/ONBOARDING.md`, or `docs/GETTING_STARTED.md` mentions a recognized
  project-level start/setup command (`hyodo start`, `npm start`,
  `make setup`, `pip install -e`, `uv sync`, `cargo run`,
  `docker compose up`) inline or in a fenced code block, or carries a
  "Getting started" / "Quick start" / "Installation" heading immediately
  followed by a code block.
- **`help_text_present`** — the project declares a CLI entry point
  (`[project.scripts]` in `pyproject.toml`, `bin` in `package.json`, or
  `[[bin]]` in `Cargo.toml`). When the checkout is HyoDo itself, the
  collector imports HyoDo's own Typer app in-process and confirms every
  registered command carries non-empty help text; for any other project it
  never imports or executes the declared binary, and instead looks for a
  `--help`/usage mention in the README alongside the entry point.

Each signal is a plain boolean with evidence (the matching file/line or
command) recorded in `dx_signals.evidence`; detection is fully offline and
deterministic, and `hyodo check` never shells out or runs a project's own
binary to compute it. Because all three keys are always emitted as booleans
once `hyodo check` runs, Benevolence coverage is always `OBSERVED` under
`--from-check` (its value may still be `0.0`/`PARTIAL`-looking in the
0-100 range when some signals are false — see the calibration table below).

What remains unobserved: `collect_dx_signals` checks for *presence* of an
onboarding entry point and help declaration, not documentation *quality*
(whether the start hint actually works, whether the help text is accurate
or complete, or whether the README covers more than the minimum). That is
a deliberate scope boundary, not a bug — see `hyodo/dx_signals.py` module
docstring.

## Calibration

Ran `hyodo score --from-check --json` (commit
`c9b1624b93ab49622d05b8865726bf3c0e2eec83`) against three targets, now that
`hyodo check` emits the three Benevolence DX signals:

| Target | Benevolence | Truth | Goodness | Hyo | Beauty | Eternity | F | TOTAL |
|---|---|---|---|---|---|---|---|---|
| HyoDo repo itself | 100.0 (OBSERVED) | 100.0 (OBSERVED) | 19.8 (OBSERVED) | 33.0 (OBSERVED) | 100.0 (OBSERVED) | 6.4377 | 43.19 | 68.88 |
| `examples/fde-evidence-spine` | 40.0 (OBSERVED) | 0.0 (PARTIAL) | 100.0 (OBSERVED) | 0.0 (OBSERVED) | 0.0 (OBSERVED) | 2.1506 | 19.75 | 25.46 |
| empty temp directory | 0.0 (OBSERVED) | 0.0 (PARTIAL) | 100.0 (PARTIAL) | 0.0 (OBSERVED) | 0.0 (OBSERVED) | 1.5849 | 15.58 | 17.75 |

Notes on reading this table:

- **Benevolence** is now `OBSERVED` in all three rows (previously
  `UNOBSERVED` for all three — see the "Known gaps" history above): the
  HyoDo repo itself has a README with an inline `hyodo start` mention and
  an in-process-importable Typer app with help text on every command
  (100.0); the example checkout has a README but no recognized start hint
  and no CLI entry point declared (40.0, README only); the empty temp
  directory has none of the three (0.0). All three still report `OBSERVED`
  coverage because `collect_dx_signals` always returns a definite boolean
  for each signal — there is no third "could not tell" state at the signal
  level, only true/false with evidence.
- Every row now has a **TOTAL**, since all five pillars have a value (even
  where Truth/Goodness are `PARTIAL` for the sparser targets, `PARTIAL`
  still means "a number was computed," not "excluded" — only `UNOBSERVED`
  pillars are excluded and block the TOTAL). No `--benevolence` override
  was needed for any of the three rows.
- The HyoDo repo's own **Goodness** (19.8) reflects that `hyodo safe`
  scanning the full HyoDo tree (fixtures included) finds high/medium
  findings above the penalty cap; this is `hyodo safe`'s own early-warning
  behavior, unchanged by this feature.
- **Truth** is `PARTIAL` for the example and the empty directory because
  neither has a Python package under a `hyodo/` directory for pyright to
  check and the test-integrity ratio rule intentionally does not fire when
  `total_tests == 0` (a "zero tests, zero vacuous" project must not read as
  a perfect 1.0).

Re-run with `hyodo score --from-check --root <target> --json` to reproduce
or refresh this table against a newer commit.
