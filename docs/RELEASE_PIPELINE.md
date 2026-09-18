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

This creates or reuses one PR, waits for checks on the exact head SHA, and
stops at `WAITING_APPROVAL`. It never infers approval from green CI. After an
independent approved review and an explicit authority reference, the same
receipt can continue through one squash merge and fresh `origin/main`
readback:

```bash
python scripts/release/pipeline.py 4.19.9 \
  --verify --execute --wait-ci --merge --authorize-ref <human-approval-ref>
```

The authority reference is an audit pointer, not a secret. The pipeline does
not accept a score, test result, or its own plan as merge authority.

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
