# afo_core → private repository separation plan

This document records how the extended `afo_core/` tree is separated out of the
public HyoDo repository, preserving its history in a private repository.

## Status

- **Public removal**: done in the public-surface cleanup PR (a normal `git rm`
  deletion commit — **no history rewrite, no force push**).
- **Private extraction**: not yet executed. It can be run at any time from the
  public repository's history (see below), because a normal deletion keeps the
  `afo_core` blobs in the git history.

## Why a normal deletion is safe

- The public `hyodo/` package does **not** import `afo_core` (verified).
- The published sdist/wheel already exclude `afo_core` (hatch `only-include`).
- The 10 tracked symlinks under `afo_core/` all point **inside** `afo_core`
  (relative targets such as `afo_core/AFO/api -> ../api`). None reach the public
  tree, so `git rm -r afo_core` removes them cleanly with no dangling symlink
  left behind elsewhere.

## History-preserving extraction (run later, in a scratch clone)

Do **not** run these against the primary working clone. Use a fresh mirror so
the public repository's history is never rewritten.

```bash
# 1. Fresh mirror of the public repo (history intact, including afo_core)
git clone --no-local /path/to/HyoDo afo-core-extract
cd afo-core-extract

# 2. Keep only afo_core in history (requires git-filter-repo)
#    https://github.com/newren/git-filter-repo
git filter-repo --path afo_core/ --path-glob 'afo_core/**'

# 3. Point at the new PRIVATE remote and push
git remote add private git@github.com:<owner>/afo-core-private.git
git push private --all
git push private --tags
```

`git subtree split --prefix=afo_core -b afo-core-history` is an alternative when
`git-filter-repo` is unavailable, but `filter-repo` is preferred for a clean,
history-complete result.

## Verify the private repo before relying on it

- `git log --oneline` in the private repo shows `afo_core` history.
- The 10 symlinks resolve inside the extracted tree.
- No public-only files (`hyodo/`, `tests/`, root docs) leaked into the private
  repo.

## Out of scope (explicitly deferred)

- **Purging `afo_core` from the public repo's past commits** requires a public
  history rewrite (`git filter-repo` on the public repo + force push). That is
  intentionally **not** part of this stage. The public working tree no longer
  contains `afo_core`; the old blobs remain reachable only through history.
- Any secret rotation is **not** required here: the secret scan over the whole
  repository (including `afo_core`) found **no real credentials** — every match
  was a synthetic test fixture for the `hyodo safe` scanner.
