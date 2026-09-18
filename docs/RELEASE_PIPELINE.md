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
pull request creation, merge, publication, and post-merge readback remain
separate authority-bound stages until their adapters are added to this single
pipeline entry point.

## Pipeline contract

```text
OBSERVE → PLAN → VERIFY → HUMAN REVIEW → INTEGRATE → REMOTE GATE → MERGE → READBACK
```

The current implementation owns `OBSERVE`, `PLAN`, and optional local
`VERIFY`. A failed stage is `BLOCKED`, never `PASS`, and the receipt records the
next action. The pipeline must not invent authority from a passing test.

The design follows the factory rule: one intake, one candidate, one receipt,
one integration path. If a later stage needs a different branch, repository,
or external authority, it must be represented as an explicit adapter rather
than an ad-hoc shell command.
