# Release Pipeline

HyoDo uses one release entry point for candidate intake and verification:

```bash
python scripts/release/pipeline.py 4.19.9
```

The default command is a zero-write intake. It observes the checkout, creates a
release plan, and emits one JSON receipt. It does not edit files, create a
branch, push, open a pull request, or merge.

After explicit human authorization, run the same pipeline with local
verification:

```bash
python scripts/release/pipeline.py 4.19.9 --verify
```

`--verify` may create local test/cache side effects through
`scripts/verify-public.sh`, but it still performs no external mutation. Push,
pull request creation, merge, publication, and post-merge readback are
available only as explicit, fail-closed adapters:

```bash
python scripts/release/pipeline.py 4.19.9 --verify --execute --wait-ci
```

By default, `--execute` requires that the current branch already exists on the
remote at exactly the planned candidate SHA. To make the pipeline own the
candidate push, add `--push-candidate`; it pushes once and immediately reads
the remote branch back before creating the PR:

```bash
python scripts/release/pipeline.py 4.19.9 \
  --verify --execute --push-candidate --wait-ci
```

The pipeline binds `candidate_sha == remote_branch_sha == pr_head_sha` before
CI, rechecks the PR and remote branch after CI, and blocks with
`RECONCILIATION_REQUIRED` if either moved. Green CI and independent review are
evidence, not merge authority. A human may authorize the exact candidate
directly:

```bash
python scripts/release/pipeline.py 4.19.9 \
  --verify --execute --wait-ci --merge \
  --authorize-ref <human-approval-ref> \
  --authorize-sha <exact-head-sha>
```

The authority reference is an audit pointer, not a secret. The SHA is the
artifact binding for that human decision. Merge requires:

```text
authorized_sha == current_pr_head == remote_candidate_sha == ci_verified_sha
```

If an independent verifier or GitHub review is absent, the receipt records
`UNVERIFIED` with a `verifier_missing` residual; it does not replace or
override Human Authority. A changed PR head invalidates the prior human
authorization and returns `RECONCILIATION_REQUIRED`.

Optional verifier evidence is also bound to the exact head when present, but
it is not a merge authority. The merge adapter passes the current expected SHA
to GitHub, so a changed head cannot be merged under an old CI or human
authorization.

## Pipeline contract

```text
OBSERVE → PLAN → VERIFY → CREATE_ONE_PR → WAIT_CI → WAIT_APPROVAL
→ MERGE_ONCE → READBACK_MAIN → CLOSEOUT_RECEIPT
```

Every stage is represented in one receipt. A failed stage is `BLOCKED`, a
not-yet-satisfied human gate is `WAIT`, and neither is reported as `PASS`. The
pipeline must not invent authority from a passing test.

Receipts use a common 5W1H envelope: `who`, `when`, `where`, `what`, `how`, and
`why`. Runtime agent/model labels are observed from the environment; absent
labels remain `UNOBSERVED`. This is provenance, not merge authority.

The design follows the factory rule: one intake, one candidate, one receipt,
one integration path. If a later stage needs a different branch, repository,
or external authority, it must be represented as an explicit adapter rather
than an ad-hoc shell command.
