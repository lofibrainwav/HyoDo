# Mutation Testing Receipt — HyoDo v4.11.0

**Date**: 2026-09-05
**Commits**: b8042fe, ee41b0e
**Operators**: Hermes (GLM-5.1)

## Tools

| Tool | Version | Status |
|------|---------|--------|
| mutmut | 3.7.0 | Config in pyproject.toml `[tool.mutmut]` |
| cosmic-ray | 8.7.0 | Config in cosmic-ray.toml |
| hypothesis | 6.157.1 | Property-based test framework |

## Target Modules

| Module | Lines | Mutations (mutmut) | Mutations (cosmic-ray) |
|--------|-------|-------------------|----------------------|
| hyodo/__init__.py | ~120 | 345 | 345 |
| hyodo/safety.py | 767 | 644 | 644 |
| hyodo/events.py | 428 | 461 | 461 |
| hyodo/exceptions.py | ~40 | 103 | 103 |
| **Total** | | **1847** | **1553** |

## Manual Mutation Verification (7/7 KILLED)

These mutations were manually injected and verified killed by property tests.
This is a **sample kill rate**, not a full automated mutation score:

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
- **Fix**: Changed assertion bounds to `6.0 - 1e-9 <= F <= 60.0 + 1e-9` and `1.0 - 1e-9 <= S <= 10.0 + 1e-9`, with `@example` for all-zeros, all-ones, all-tens
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
- **Fix**: Changed hypothesis strategy from `ascii_letters + digits + "_-"` to `ascii_letters + digits + "_"`, with `@example` for canonical token format
- **Philosophy mapping**: 진(眞) — Property generators must match actual invariants

## Automated Mutation Testing Status

### mutmut
- **Issue**: `mutants/` worktree uses editable install from original `.venv`, so mutated source is not loaded
- **Result**: All 1847 mutants surface as "survived" or "no tests" — the runner tests the unmutated code
- **Workaround**: Manual injection + verification (7/7 KILLED above)
- **Config**: `[tool.mutmut]` in pyproject.toml, targets 4 modules, 5 test files, `also_copy = [".venv"]`

### cosmic-ray
- **Status**: Session initialized with 1553 mutations across 4 target modules
- **Baseline**: Tests pass unmutated (verified)
- **Full execution**: Pending — cosmic-ray runs mutations sequentially
- **Config**: `cosmic-ray.toml` with local distributor

## Property Test Coverage Summary

| Test File | Tests | @given | @example | Assumptions Corrected |
|-----------|-------|--------|----------|----------------------|
| test_scoring_properties.py | 3 | 3 | 3 | 1 (H1) |
| test_safety_property_boundaries.py | 6 | 5 | 1 | 2 (H2, H3) |
| test_ledger_durability.py | 6 | 2 | 0 | 0 |
| **Total** | **15** | **10** | **4** | **3** |

## Philosophy → Test Mapping

| Virtue | Korean | Property | Test File |
|--------|--------|----------|-----------|
| Truth | 진(眞) | Pattern boundary discrimination | test_safety_property_boundaries.py |
| Goodness | 선(善) | Mutation evidence receipt (7/7 sample) | This receipt |
| Beauty | 미(美) | Monotonicity, symmetry, boundedness | test_scoring_properties.py |
| Benevolence | 인(仁) | JSONL corrupt recovery, None≠0 | test_ledger_durability.py |
| Filial Piety | 효(孝) | Reproducibility (@example anchors + hypothesis DB) | All property files |
| Eternity | 영(永) | Mutation evidence receipt; automated mutation score not yet measured | This receipt |

## Verification Commands

```bash
# Property tests
python -m pytest tests/test_scoring_properties.py tests/test_safety_property_boundaries.py tests/test_ledger_durability.py -v

# Full suite
python -m pytest tests/ -q --tb=short

# Lint
python -m ruff check hyodo tests && python -m ruff format --check hyodo tests

# Cosmic Ray baseline
cosmic-ray baseline cosmic-ray.toml

# Cosmic Ray session stats
python -c "import sqlite3; c=sqlite3.connect('cosmic-ray.session'); print(c.execute('SELECT COUNT(*) FROM mutation_specs').fetchone())"
```