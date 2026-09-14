# SSOT workflow and collision guard

HyoDo work must keep one explicit candidate head. Parallel lanes may inspect or
prepare independent changes, but integration is serial and starts from the
current `origin/main`.

## Required sequence

1. Read `origin/main`, candidate `HEAD`, and worktree status before starting.
2. Give each lane an isolated worktree and a narrow write-set.
3. Reconcile the candidate onto the current `origin/main` in a clean worktree.
4. Run `scripts/verify-ssot-drift.sh origin/main HEAD` before pushing.
5. Let the `SSOT Drift Guard` workflow verify the exact PR head against the PR
   base SHA.
6. Treat missing or stale remote evidence as `UNOBSERVED`, not green.

## Local hook

Enable the repository hook once per worktree:

```bash
git config core.hooksPath .githooks
```

The pre-push hook refuses to push a dirty worktree or a candidate that is not
based on `origin/main`. It does not delete, stash, reset, or merge changes.
