# Mutation Testing Receipt — HyoDo v4.11.0

**Date**: 2026-09-05
**Commit base**: `b059dd7` (main after #124 and #125)
**Operators**: Hermes (GLM-5.2)

## Tools

| Tool | Version | Status |
|------|---------|--------|
| mutmut | 3.7.0 | Automated run completed in an isolated worktree |
| cosmic-ray | 8.7.0 | Config and session baseline available |
| hypothesis | 6.157.1 | Property-based test framework |

## Automated mutmut Run

The run used a clean git worktree at `/tmp/hyodo-mutation-baseline`,
afresh Python 3.12 virtual environment, and `uv pip install -e
".[dev,mutation]"`. This avoids the original checkout's editable-install
ambiguity.

| Measure | Result |
|---------|--------|
| Mutations generated | 1,847 |
| Mutations with selected-test coverage | 318 |
| Killed | 163 |
| Survived | 155 |
| No selected tests | 1,529 |
| Kill rate of tested mutations | **163/318 = 51.26%** |
| Kill rate of all generated mutations | **163/1,847 = 8.83%** |

The 51.26% figure is the actionable test-suite mutation score for the
selected target tests. The 8.83% figure is the conservative all-generated
rate; it includes 1,529 generated mutations for which the selected test set
had no associated tests. Neither number is a merge authority by itself.

### Per-module result

| Module | Tested | Killed | Survived | Kill rate |
|--------|--------|--------|----------|-----------|
| `hyodo/__init__.py` | 121 | 73 | 48 | 60.33% |
| `hyodo/safety.py` | 111 | 46 | 65 | 41.44% |
| `hyodo/events.py` | 86 | 44 | 42 | 51.16% |
| `hyodo/exceptions.py` | 0 | 0 | 0 | N/A |

The durable summarizer is `scripts/mutation-score.py`. It reads mutmut
metadata without importing mutmut internals and reports both denominators.

## Manual Mutation Verification (7/7 KILLED)

These mutations were manually injected and verified killed by property tests.
This is a separate intentional sample, not the automated mutation score:

| # | Mutation | File | Killer Test |
|---|----------|------|-------------|
| M1 | `v <= 0` → `v < 0` | __init__.py:L14 | `test_geometric_mean_zero_when_any_input_is_zero` |
| M2 | SECRET_PATTERNS removed | safety.py | `test_aws_access_key_boundary_property` |
| M3 | OSError propagation in append | events.py | `test_append_unwritable_returns_false` |
| M4 | corrupt count → 0 | events.py | `test_valid_events_survive_corrupt_neighbors` |
| M5 | `to_10_scale` bounds 0→1 | __init__.py | `test_score_bounded_f_and_s_ranges` |
| M6 | Pillar permutation (asymmetry) | __init__.py | `test_score_symmetry_permutation_invariant` |
| M7 | `to_10_scale` monotonicity violation | __init__.py | `test_score_monotonicity_raising_one_pillar_never_lowers_score` |

## Boundary Assumptions Corrected (3)

Three property-model / boundary assumptions were corrected during development:

### H1: Floating-point boundary in geometric_mean
- **File**: `hyodo/__init__.py`
- **Assumption**: Boundedness assertion assumed exact `0 ≤ S ≤ 10`
- **Correction**: `geometric_mean([10.0]*5)` returns `10.000000000000002` due to IEEE 754 fifth-root rounding — assertion needs epsilon tolerance
- **Fix**: Changed assertion bounds to `6.0 - 1e-9 <= F <= 60.0 + 1e-9` and `1.0 - 1e-9 <= S <= 10.0 + 1e-9`, with `@example` for all-zeros and all-ones
- **Philosophy mapping**: 미(美) — Beauty requires mathematical rigor including floating-point limits

### H2: AWS access key regex has no end anchor
- **File**: `hyodo/safety.py`
- **Assumption**: Test expected `AKIA[0-9A-Z]{16}` to reject 17+ character strings
- **Correction**: The regex has no `$` anchor, so 17+ chars also match (prefix matching). This is a design choice, not a bug.
- **Fix**: Updated test boundary expectations to match actual pattern behavior (16+ chars match)
- **Philosophy mapping**: 진(眞) — Truth requires measuring actual behavior, not assumed behavior

### H3: GitHub token charset excludes hyphens
- **File**: `hyodo/safety.py`
- **Assumption**: Test strategy generated hyphens in token body, assuming `[A-Za-z0-9_-]`
- **Correction**: The regex `[A-Za-z0-9_]{20,}` excludes hyphens. Test strategy was generating characters outside the regex charset.
- **Fix**: Changed hypothesis strategy from `ascii_letters + digits + "_-"` to `ascii_letters + digits + "_"`
- **Philosophy mapping**: 진(眞) — Property generators must match actual invariants

## Cosmic Ray Status

- **Session baseline**: 1,553 mutations initialized across 4 target modules.
- **Unmutated baseline**: selected tests passed.
- **Full mutation execution**: not used as the primary score; the mutmut run above is the measured automated baseline.
- **Config**: `cosmic-ray.toml` with local distributor and portable `python -m pytest` command.

## Property Test Coverage Summary

| Test File | Tests | @given | @example | Assumptions Corrected |
|-----------|-------|--------|----------|----------------------|
| test_scoring_properties.py | 3 | 3 | 2 | 1 (H1) |
| test_safety_property_boundaries.py | 6 | 5 | 1 | 2 (H2, H3) |
| test_ledger_durability.py | 6 | 2 | 1 | 0 |
| **Total** | **15** | **10** | **4** | **3** |

## Philosophy → Test Mapping

| Virtue | Korean | Property | Test File |
|--------|--------|----------|-----------|
| Truth | 진(眞) | Pattern boundary discrimination | test_safety_property_boundaries.py |
| Goodness | 선(善) | Automated mutation evidence: 51.26% of tested mutants killed | This receipt |
| Beauty | 미(美) | Monotonicity, symmetry, boundedness | test_scoring_properties.py |
| Benevolence | 인(仁) | JSONL corrupt recovery, None≠0 | test_ledger_durability.py |
| Filial Piety | 효(孝) | Reproducibility (@example anchors + deterministic generation) | tests/conftest.py |
| Eternity | 영(永) | Versioned receipt with tested/all denominators | This receipt |

## Verification Commands

```bash
# Property tests
python -m pytest tests/test_scoring_properties.py tests/test_safety_property_boundaries.py tests/test_ledger_durability.py -v

# Full suite
python -m pytest tests/ -q --tb=short

# Lint
python -m ruff check hyodo tests scripts && python -m ruff format --check hyodo tests scripts

# Mutmut setup and run in an isolated checkout
uv pip install -e ".[dev,mutation]"
mutmut run
python scripts/mutation-score.py --generated 1847

# Cosmic Ray baseline
cosmic-ray baseline cosmic-ray.toml
```
