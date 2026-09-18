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
`RECONCILIATION_REQUIRED` if either moved. It stops at `WAITING_APPROVAL` and
never infers approval from green CI. After an independent approved review and
an explicit authority reference, the same receipt can continue through one
squash merge and fresh `origin/main` readback:

```bash
python scripts/release/pipeline.py 4.19.9 \
  --verify --execute --wait-ci --merge --authorize-ref <human-approval-ref>
```

The authority reference is an audit pointer, not a secret. The pipeline does
not accept a score, test result, or its own plan as merge authority.

Approval is bound to the exact head too: an approved review is accepted only
when its GitHub `commit_id` equals the current PR head SHA. The merge adapter
passes that expected SHA to GitHub, so a changed head cannot be merged under an
old CI or review result.

## Pipeline contract

```text
OBSERVE → PLAN → VERIFY → CREATE_ONE_PR → WAIT_CI → WAIT_APPROVAL
→ MERGE_ONCE → READBACK_MAIN → CLOSEOUT_RECEIPT
```

Every stage is represented in one receipt. A failed stage is `BLOCKED`, a
not-yet-satisfied human gate is `WAIT`, and neither is reported as `PASS`. The
pipeline must not invent authority from a passing test.

The design follows the factory rule: one intake, one candidate, one receipt,
one integration path. If a later stage needs a different branch, repository,
or external authority, it must be represented as an explicit adapter rather
than an ad-hoc shell command.
