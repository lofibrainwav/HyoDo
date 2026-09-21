# Independent Judge contract — Software Portability v0

This contract is frozen in the same commit as the measurements it governs. The
judge's verdict lands in a separate file, `PORTABILITY_JUDGE_RECEIPT_V0.md`, in
a later commit — a contract that could be edited after seeing the verdict would
not be a contract.

The builder of this experiment is not its judge.

## Input only

- the frozen protocol (`PORTABILITY_RESEARCH_V0.md`)
- `evidence_source_sha`
- `research_artifact_sha`
- the 12 frozen fixtures
- the frozen oracle
- both arm outputs
- the score output
- measurement methodology and raw receipts

## Forbidden input

- the builder's verdict
- the builder's recommendation
- any desired outcome
- any promotion request
- any "this is correct" summary
- any authority or approval token

## Permissions

READ ONLY. No fixture, oracle, measurement, or code modification.

## Procedure

1. Read each native source artifact directly at `evidence_source_sha`.
2. Verify each source digest.
3. Verify that the fixture represents its source honestly.
4. **Independently re-derive the oracle state from the source.** The builder's
   oracle is not an answer key. Apply the same precedence ladder
   (`UNOBSERVED` > `AMBIGUOUS` > `BLOCKED` > `SUPPORTED`) so that any
   disagreement is about evidence rather than about tie-breaking.
5. Compare that independent `oracle'` against the frozen oracle and report every
   disagreement.
6. Verify the arm outputs are oracle-free: no arm may have read `oracle.json`,
   and `--verify` must reproduce both arms byte-identically with the oracle file
   hidden.
7. Only then compare arm results and apply the frozen decision rule from
   `candidate.json`.

## Package boundary readback

Run both checks and paste the raw output. The bases differ on purpose: the
release tag is contaminated by unrelated commits already on `main`.

```bash
# PR scope (primary). Allowlist: docs/research/**, scripts/research/**
git diff --name-only <evidence_source_sha>..<research_artifact_sha>

# Package freeze (secondary, informational)
git diff --name-only v4.20.2..<research_artifact_sha> \
  -- hyodo schemas VERSION pyproject.toml
```

Any path outside the allowlist on the primary check is a HOLD. A non-empty
secondary result is a fact about `main` to report, not automatically this PR's
change.

## Also confirm

- Professional and Creative remain `UNOBSERVED`; no result implies otherwise.
- The preflight search is re-run independently. `NOT_REPRESENTABLE` is a claim
  about the adequacy of a search, and one such claim in this run was already
  wrong once: an earlier pass searched only `examples/` and missed the `tests/`
  policy contracts. Confirm `REPRESENTABLE` or report a missed source.

## Verdict

Exactly one of:

```text
SOFTWARE_V0_GREEN
SOFTWARE_V0_PARTIAL
SOFTWARE_V0_INVALID
```

`GREEN` does not authorize Core Candidate promotion. Core promotion is
`NOT_ELIGIBLE` for structural reasons decided before the run, and no verdict on
this run can change that.
