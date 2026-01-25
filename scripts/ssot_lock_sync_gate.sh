#!/usr/bin/env bash
set -euo pipefail

fail=0
ts="$(date +%Y%m%d_%H%M%S)"
root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "${root}" ]; then
  echo "FAIL: not a git repo"
  exit 1
fi
cd "${root}"

evidence_dir="${root}/docs/ssot/evidence/SSOT_LOCK_SYNC_GATE_${ts}"
mkdir -p "${evidence_dir}"

ruff_target="${SSOT_RUFF_TARGET:-.}"
allow_ahead="${SSOT_ALLOW_AHEAD:-false}"

abs_re="${SSOT_ABS_PATH_REGEX:-(${root}|/Users/[^/]+/AFO_Kingdom)}"

allow_untracked_re_base="${SSOT_UNTRACKED_ALLOWLIST_REGEX:-^(docs/ssot/evidence/|artifacts/|tools/dgm/|\\.bruin\\.yml$)}"
allowlist_file="${SSOT_UNTRACKED_ALLOWLIST_FILE:-}"
apply_allowlist="${SSOT_APPLY_UNTRACKED_ALLOWLIST:-false}"
allowlist_outfile="${SSOT_ALLOWLIST_OUTFILE:-docs/ssot/allowlists/untracked_allowlist_regex.txt}"

join_or_regex() { awk 'NF && $0 !~ /^[[:space:]]*#/ {print}' "$1" 2>/dev/null | paste -sd'|' -; }
escape_regex_exact() {
  # Simple escaping for sed - avoid complex regex operators
  printf '%s' "$1" | sed 's/[.[\]*+?^$|()\\]/\\&/g'
}

run_capture() {
  local name="$1"; shift
  local out="${evidence_dir}/${name}.out.txt"
  local err="${evidence_dir}/${name}.err.txt"
  set +e
  "$@" >"${out}" 2>"${err}"
  local rc=$?
  set -e
  echo "${rc}"
}

run_capture_shell() {
  local name="$1"
  local cmd="$2"
  local out="${evidence_dir}/${name}.out.txt"
  local err="${evidence_dir}/${name}.err.txt"
  set +e
  bash -lc "${cmd}" >"${out}" 2>"${err}"
  local rc=$?
  set -e
  echo "${rc}"
}

{
  echo "AS_OF=${ts}"
  echo "GIT_ROOT=${root}"
  echo "RUFF_TARGET=${ruff_target}"
  echo "ABS_PATH_REGEX=${abs_re}"
  echo "ALLOW_AHEAD=${allow_ahead}"
  echo "ALLOWLIST_FILE=${allowlist_file}"
  echo "APPLY_ALLOWLIST=${apply_allowlist}"
  echo "ALLOWLIST_OUTFILE=${allowlist_outfile}"
  echo ""
} > "${evidence_dir}/summary.txt"

# 1) Ruff
ruff_pass=0
if ! command -v ruff >/dev/null 2>&1; then
  echo "RUFF=FAIL (ruff_not_found)" >> "${evidence_dir}/summary.txt"
  fail=1
else
  rc_ver="$(run_capture ruff_version ruff --version)"
  # Safely handle multiple targets or targets with spaces
  rc_chk="$(run_capture_shell ruff_check "cd \"${root}\" && time ruff check ${ruff_target} --quiet")"
  if [ "${rc_ver}" != "0" ] || [ "${rc_chk}" != "0" ]; then
    echo "RUFF=FAIL (version_rc=${rc_ver}, check_rc=${rc_chk})" >> "${evidence_dir}/summary.txt"
    fail=1
  else
    echo "RUFF=PASS" >> "${evidence_dir}/summary.txt"
    ruff_pass=1
  fi
fi

# 2) ABS_PATH (code/config only, exclude evidence/artifacts)
abs_hits_file="${evidence_dir}/abs_path_hits.out.txt"
abs_err_file="${evidence_dir}/abs_path_hits.err.txt"
set +e
git grep -nE "${abs_re}" -- \
  '*.py' '*.sh' '*.ts' '*.tsx' '*.js' '*.jsx' '*.json' '*.yml' '*.yaml' '*.toml' \
  | grep -vE "(^docs/|^artifacts/|^.claude/|^.cursor/|/evidence/|/results/|/analysis_results/|legacy/|kingdom_dashboard.js|^scripts/|^tests/|^tools/|/scripts/|/tests/|/tools/)" \
  >"${abs_hits_file}" 2>"${abs_err_file}" || true
abs_rc=$?
set -e

abs_pass=0
if [ "${abs_rc}" = "0" ]; then
  abs_hits="$(wc -l < "${abs_hits_file}" | tr -d ' ')"
  if [ "${abs_hits}" = "0" ]; then
    echo "ABS_PATH=PASS" >> "${evidence_dir}/summary.txt"
    abs_pass=1
  else
    echo "ABS_PATH=FAIL (hits=${abs_hits})" >> "${evidence_dir}/summary.txt"
    fail=1
  fi
else
  echo "ABS_PATH=PASS" >> "${evidence_dir}/summary.txt"
  abs_pass=1
fi

# 3) GIT
run_capture git_status_sb git status -sb >/dev/null
run_capture git_diff_unstaged git diff --name-status >/dev/null
run_capture git_diff_staged git diff --cached --name-status >/dev/null

untracked_file="${evidence_dir}/git_untracked.txt"
git ls-files --others --exclude-standard > "${untracked_file}" 2>/dev/null || true

dirty_unstaged="$(wc -l < "${evidence_dir}/git_diff_unstaged.out.txt" | tr -d ' ')"
dirty_staged="$(wc -l < "${evidence_dir}/git_diff_staged.out.txt" | tr -d ' ')"

allow_untracked_re="${allow_untracked_re_base}"
if [ -n "${allowlist_file}" ] && [ -f "${allowlist_file}" ]; then
  extra="$(join_or_regex "${allowlist_file}" || true)"
  if [ -n "${extra}" ]; then
    allow_untracked_re="(${allow_untracked_re_base}|${extra})"
  fi
fi

bad_untracked_file="${evidence_dir}/git_untracked_bad.txt"
bad_untracked_count=0
bad_untracked="$(grep -Ev "${allow_untracked_re}" "${untracked_file}" 2>/dev/null || true)"
if [ -n "${bad_untracked}" ]; then
  bad_untracked_count="$(printf "%s\n" "${bad_untracked}" | wc -l | tr -d ' ')"
  printf "%s\n" "${bad_untracked}" > "${bad_untracked_file}"
else
  : > "${bad_untracked_file}"
fi

if [ "${apply_allowlist}" = "true" ] && [ "${bad_untracked_count}" != "0" ]; then
  mkdir -p "$(dirname "${allowlist_outfile}")"
  {
    echo "# added_by=ssot_lock_sync_gate ts=${ts}"
    while IFS= read -r p; do
      [ -z "${p}" ] && continue
      esc="$(escape_regex_exact "${p}")"
      echo "^${esc}$"
    done < "${bad_untracked_file}"
    echo ""
  } >> "${allowlist_outfile}"
  run_capture allowlist_git_add git add "${allowlist_outfile}" >/dev/null
fi

header_line="$(head -n 1 "${evidence_dir}/git_status_sb.out.txt" 2>/dev/null || true)"
ahead_or_behind="no"
echo "${header_line}" | grep -E '\[(ahead|behind|diverged|gone)[^]]*\]' >/dev/null 2>&1 && ahead_or_behind="yes"

git_ok=1
if [ "${dirty_unstaged}" != "0" ] || [ "${dirty_staged}" != "0" ]; then git_ok=0; fi
if [ "${bad_untracked_count}" != "0" ]; then git_ok=0; fi
if [ "${ahead_or_behind}" = "yes" ] && [ "${allow_ahead}" != "true" ]; then git_ok=0; fi

git_pass=0
if [ "${git_ok}" = "1" ]; then
  echo "GIT=PASS (unstaged=${dirty_unstaged}, staged=${dirty_staged}, bad_untracked=${bad_untracked_count}, ahead_or_behind=${ahead_or_behind})" >> "${evidence_dir}/summary.txt"
  git_pass=1
else
  echo "GIT=FAIL (unstaged=${dirty_unstaged}, staged=${dirty_staged}, bad_untracked=${bad_untracked_count}, ahead_or_behind=${ahead_or_behind})" >> "${evidence_dir}/summary.txt"
  fail=1
fi

# Sejong hints (max 3)
{
  echo ""
  echo "NEXT_ACTIONS_MAX_3:"
  n=0

  if [ "${ruff_pass}" != "1" ]; then
    echo "1) ruff 원인 파악: ruff check . --statistics"
    n=$((n+1))
  fi

  if [ "${abs_pass}" != "1" ] && [ "${n}" -lt 3 ]; then
    k=$((n+1))
    echo "${k}) 절대경로 히트 상위 확인: sed -n '1,80p' \"${evidence_dir}/abs_path_hits.out.txt\""
    n=$((n+1))
  fi

  if [ "${git_pass}" != "1" ] && [ "${n}" -lt 3 ]; then
    k=$((n+1))
    if [ "${bad_untracked_count}" != "0" ]; then
      echo "${k}) untracked 격리(옵션): SSOT_APPLY_UNTRACKED_ALLOWLIST=true ./scripts/ssot_lock_sync_gate.sh"
    else
      echo "${k}) git 정리: git status -sb && git add -A && git commit -m \"chore: sync gate cleanup\""
    fi
    n=$((n+1))
  fi
} >> "${evidence_dir}/summary.txt"

echo "" >> "${evidence_dir}/summary.txt"
echo "EVIDENCE_DIR=${evidence_dir}" >> "${evidence_dir}/summary.txt"

if [ "${fail}" = "0" ]; then
  echo "PASS: SSOT-LOCK Sync Gate"
  echo "Evidence: ${evidence_dir}"
  exit 0
else
  echo "FAIL: SSOT-LOCK Sync Gate"
  echo "Evidence: ${evidence_dir}"
  exit 1
fi
