#!/usr/bin/env bash
set -euo pipefail

base_ref="${1:?usage: verify-ssot-drift.sh BASE [HEAD]}"
head_ref="${2:-HEAD}"

untracked="$(git ls-files --others --exclude-standard)"
if ! git diff --quiet || ! git diff --cached --quiet || [[ -n "$untracked" ]]; then
  echo "SSOT_DRIFT: worktree has unstaged or staged changes" >&2
  git status --short >&2
  exit 1
fi

git cat-file -e "${base_ref}^{commit}"
git cat-file -e "${head_ref}^{commit}"

if ! git merge-base --is-ancestor "$base_ref" "$head_ref"; then
  echo "SSOT_DRIFT: $head_ref is not based on $base_ref" >&2
  echo "Reconcile the candidate in a clean worktree before pushing." >&2
  exit 1
fi

echo "SSOT_GREEN: base=$base_ref head=$head_ref"
