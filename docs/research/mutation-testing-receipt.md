# Mutation Testing Receipt — HyoDo v4.11.0

**Date**: 2026-09-05
**Commit base**: `b059dd7` (main after #124 and #125)
**Operators**: Hermes (GLM-5.2)

## Tools

| Tool | Version | Status |
|------|---------|--------|
| mutmut | 3.7.0 | Automated isolated-worktree run completed; status-aware readback required |
| cosmic-ray | 8.7.0 | Config and independent CI automation available in PR #126 |
| hypothesis | 6.x | Property-based test framework; explicit examples are durable regressions |

The `mutation` optional dependency pins mutmut 3.7.0 and Cosmic Ray 8.7.0.
Mutation status semantics are version-sensitive and must be revalidated before
those pins move.

## Automated mutmut Run

The initial run used a clean git worktree at `/tmp/hyodo-mutation-baseline`, a
fresh Python 3.12 virtual environment, and `uv pip install -e ".[dev,mutation]"`.
That isolation removed the editable-install ambiguity seen in the first mutmut
attempt.

### Initial legacy summary — provisional

The first summarizer reported:

| Measure | Initial result |
|---------|----------------|
| Mutations generated | 1,847 |
| Classified as tested | 318 |
| Classified as killed | 163 |
| Classified as survived | 155 |
| Legacy tested kill rate | 51.26% |
| Legacy all-generated rate | 8.83% |

**Do not treat those derived rates or the former `1,529 no-tests` label as the
sealed mutation score yet.** A follow-up audit found two classification defects
in the legacy summarizer:

1. exit code `-24` was counted as killed, while mutmut 3.7.0's final status map
   classifies it as `timeout`;
2. every generated mutant outside killed/survived was collapsed into
   `no-tests`, mixing true no-test outcomes with not-checked, timeout, skipped,
   type-check, segfault, interrupted, and suspicious outcomes.

`scripts/mutation-score.py` now preserves each mutmut 3.7.0 status separately,
fails if any target metadata file is missing, and treats `--generated` only as
an assertion against metadata rather than as a denominator override.

### Required sealing readback

Run the status-aware summarizer against the preserved or freshly generated
`mutants/` metadata:

```bash
python scripts/mutation-score.py --mutants-dir mutants --generated 1847
```

The final receipt must copy the resulting per-status totals before this PR is
considered mutation-score complete. Until then the initial values above are
historical observations, not merge authority.

## Manual Mutation Verification (7/7 KILLED)

These mutations were manually injected and verified killed by focused property
or regression tests. This is a separate intentional sample, not the automated
mutation score:

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

Three property-model / boundary assumptions were corrected during development.
They are not presented as three production-code bugs.

### H1: Floating-point boundary in geometric_mean

- **File**: `hyodo/__init__.py`
- **Assumption**: Boundedness assertion assumed exact scorer bounds.
- **Correction**: fifth-root floating-point rounding can produce a tiny epsilon above 10.
- **Fix**: assertions use epsilon tolerance and explicit all-zero/all-one examples.
- **Philosophy mapping**: 미(美) — mathematical claims include floating-point limits.

### H2: AWS access key regex has no end anchor

- **File**: `hyodo/safety.py`
- **Assumption**: the test expected `AKIA[0-9A-Z]{16}` to reject a longer suffix.
- **Correction**: the regex intentionally prefix-matches 16 or more suffix characters.
- **Fix**: boundary expectations now match the shipped pattern behavior.
- **Philosophy mapping**: 진(眞) — tests measure actual contracts, not assumptions.

### H3: GitHub token charset excludes hyphens

- **File**: `hyodo/safety.py`
- **Assumption**: the generator included hyphens in the token body.
- **Correction**: the regex body is `[A-Za-z0-9_]{20,}`.
- **Fix**: the property generator uses the actual invariant charset.
- **Philosophy mapping**: 진(眞) — generators match the contract they exercise.

## Cosmic Ray Status

- The original local session initialized 1,553 mutations across four core modules.
- PR #126 adds a separate automated Cosmic Ray evidence lane.
- Cosmic Ray and mutmut use different mutation operators and test-selection
  mechanics, so their rates are complementary evidence rather than interchangeable
  scores.

## Property Test Coverage Summary

| Test File | Tests | @given | @example | Assumptions Corrected |
|-----------|-------|--------|----------|----------------------|
| test_scoring_properties.py | 3 | 3 | 2 | 1 (H1) |
| test_safety_property_boundaries.py | 6 | 5 | 1 | 2 (H2, H3) |
| test_ledger_durability.py | 6 | 2 | 1 | 0 |
| **Total** | **15** | **10** | **4** | **3** |

## Philosophy → Test Mapping

| Virtue | Korean | Property | Evidence |
|--------|--------|----------|----------|
| Truth | 진(眞) | Pattern boundary discrimination | safety property tests |
| Goodness | 선(善) | Mutation outcomes classified without denominator drift | status-aware receipt |
| Beauty | 미(美) | Monotonicity, symmetry, boundedness | scoring property tests |
| Benevolence | 인(仁) | JSONL corrupt recovery, None≠0 | ledger durability tests |
| Filial Piety | 효(孝) | Explicit committed regression examples | `@example` anchors |
| Eternity | 영(永) | Version-pinned tooling + versioned receipt | this receipt |

## Verification Commands

```bash
# Property tests
python -m pytest tests/test_scoring_properties.py tests/test_safety_property_boundaries.py tests/test_ledger_durability.py -v

# Mutation summarizer contract
python -m pytest tests/test_mutation_score.py -v

# Full suite
python -m pytest tests/ -q --tb=short

# Lint
python -m ruff check hyodo tests scripts && python -m ruff format --check hyodo tests scripts

# Mutmut setup and run in an isolated checkout
uv pip install -e ".[dev,mutation]"
mutmut run
python scripts/mutation-score.py --mutants-dir mutants --generated 1847

# Cosmic Ray baseline
cosmic-ray baseline cosmic-ray.toml
```
