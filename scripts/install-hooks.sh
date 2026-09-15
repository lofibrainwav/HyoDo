#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "HOOK_INSTALL_ERROR: run this script from inside a Git worktree" >&2
  exit 1
}
cd "$repo_root"

hooks_dir="$repo_root/.githooks"
if [[ ! -x "$hooks_dir/pre-push" ]]; then
  echo "HOOK_INSTALL_ERROR: .githooks/pre-push is missing or not executable" >&2
  exit 1
fi

current_hooks_path="$(git config --get core.hooksPath || true)"
if [[ -n "$current_hooks_path" && "$current_hooks_path" != ".githooks" ]]; then
  echo "HOOK_INSTALL_CONFLICT: core.hooksPath is already set to '$current_hooks_path'" >&2
  echo "Review that hook configuration before replacing it with .githooks." >&2
  exit 1
fi

git config --local core.hooksPath .githooks
configured_hooks_path="$(git config --local --get core.hooksPath)"
if [[ "$configured_hooks_path" != ".githooks" ]]; then
  echo "HOOK_INSTALL_ERROR: core.hooksPath readback was '$configured_hooks_path'" >&2
  exit 1
fi

echo "HOOK_INSTALL_GREEN: core.hooksPath=$configured_hooks_path"
