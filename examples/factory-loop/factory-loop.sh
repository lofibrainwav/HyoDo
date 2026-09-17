#!/usr/bin/env bash
# factory-loop.sh — reference host loop for an unattended feature queue.
#
# HyoDo is a gate, not an agent runtime. Every line marked [HOST] is work the
# integrating host owns (branching, building, reviewing, opening the PR).
# Every line marked [HYODO] asks HyoDo to observe, validate, or record.
# Nothing here grants merge authority: the PR is merged by a person.
#
# Usage:
#   factory-loop.sh [--queue queue.md] [--policy policy.toml] [--dry-run]
#
# Host hooks (environment variables, all optional in --dry-run):
#   FACTORY_BUILD_CMD   command run inside the item's worktree to implement it
#   FACTORY_REVIEW_CMD  command run inside the worktree by an INDEPENDENT
#                       reviewer (separate context window, assumes bugs exist);
#                       must exit non-zero when it finds a blocking defect
#   FACTORY_PR_CMD      command that opens the pull request from the worktree
#
# Exit codes: 0 item reached PR stage, or the queue was empty ·
#             1 a gate, the reviewer, or the policy said no (FAIL / DENY) ·
#             2 something was UNOBSERVED (no gates, unapproved gate set,
#               policy unreadable, hook missing) ·
#             3 the policy asked for an operator decision (ASK) and nobody
#               is here at night.
set -euo pipefail

QUEUE="queue.md"
POLICY="policy.toml"
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --queue) QUEUE="$2"; shift 2 ;;
    --policy) POLICY="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY_RUN" = 1 ]; then say "  (dry-run) $*"; else "$@"; fi; }

# ---------------------------------------------------------------------------
# 0. [HYODO] The CLI must be observable before anything else runs.
command -v hyodo >/dev/null 2>&1 || { say "UNOBSERVED: hyodo CLI not on PATH"; exit 2; }

# 1. [HOST] Take the first open item from the queue. The queue is frozen input.
ITEM_LINE="$(grep -m1 -E '^- \[ \] `' "$QUEUE" || true)"
[ -n "$ITEM_LINE" ] || { say "queue empty: nothing to do"; exit 0; }
SLUG="$(printf '%s' "$ITEM_LINE" | sed -E 's/^- \[ \] `([^`]+)`.*/\1/')"
GATES="$(printf '%s' "$ITEM_LINE" | sed -nE 's/.*gates: (.*)$/\1/p' | tr -d '`' | tr ',' ' ')"
say "item      : $SLUG"
say "gates     : ${GATES:-<none declared>}"

# 2. [HYODO] Policy fence must be readable. A synthetic probe event is enough
#    to prove the file parses and evaluates; the real events come from the
#    host's hooks during the build. Exit 2 here means UNOBSERVED, not ALLOW.
PROBE="$(mktemp)"
cat >"$PROBE" <<JSON
{"schema_version":"hyodo.agent-event/v1","event_id":"00000000-0000-4000-8000-000000000001",
 "run_id":"00000000-0000-4000-8000-0000000000aa","ts":"$(date -u +%Y-%m-%dT%H:%M:%S+00:00)",
 "kind":"tool_call","step_index":0,"actor":"agent",
 "tool":{"name":"Read","args_digest":"000000000000","paths":["README.md"]},
 "io":{"input_digest":null,"output_digest":null,"bytes_in":0,"bytes_out":0},
 "policy":{"decision":null,"rule_id":null,"reason":null},
 "meta":{"model":"factory-probe","tags":["factory-loop","probe"]}}
JSON
set +e
hyodo policy check --file "$PROBE" --config "$POLICY" --quiet
POLICY_RC=$?
set -e
case "$POLICY_RC" in
  0) say "policy    : ALLOW (fence readable)" ;;
  1) say "policy    : DENY — the fence rejects a plain Read; fix policy.toml before running unattended"; exit 1 ;;
  3) say "policy    : ASK — the fence wants an operator decision; nobody is here at night"; exit 3 ;;
  *) say "policy    : UNOBSERVED (exit $POLICY_RC) — policy unreadable; stopping before any build"; exit 2 ;;
esac

# 3. [HOST] Isolate the item on its own branch and worktree.
ROOT="$(git rev-parse --show-toplevel)"
WORKTREE="$ROOT/.factory/$SLUG"
BRANCH="factory/$SLUG"
run git worktree add "$WORKTREE" -b "$BRANCH"
[ "$DRY_RUN" = 1 ] && WORKTREE="$ROOT"

# 4. [HOST] Build. The builder gets the item, the mock, and the policy. It does
#    not get to declare success — that is what steps 6 and 7 are for.
if [ -n "${FACTORY_BUILD_CMD:-}" ]; then
  run bash -c "cd '$WORKTREE' && $FACTORY_BUILD_CMD"
elif [ "$DRY_RUN" = 1 ]; then
  say "  (dry-run) builder: FACTORY_BUILD_CMD not set"
else
  say "UNOBSERVED: FACTORY_BUILD_CMD not set — the host must supply a builder"; exit 2
fi

# 5. [HOST] Independent review. Different process, different context window,
#    starts from the assumption that the build is wrong. A reviewer that shares
#    the builder's context is not independent and its PASS is not evidence.
if [ -n "${FACTORY_REVIEW_CMD:-}" ]; then
  if ! run bash -c "cd '$WORKTREE' && $FACTORY_REVIEW_CMD"; then
    say "reviewer found a blocking defect: item stays open on branch $BRANCH"; exit 1
  fi
elif [ "$DRY_RUN" = 1 ]; then
  say "  (dry-run) reviewer: FACTORY_REVIEW_CMD not set"
else
  say "UNOBSERVED: FACTORY_REVIEW_CMD not set — a build without an independent review is not evidence"; exit 2
fi

# 6. [HYODO] Fail-closed gates. HyoDo runs the gates itself; it never trusts a
#    "tests passed" claim from the builder or the reviewer.
#    exit 0 = every configured gate ran and passed
#    exit 1 = a gate ran and failed            -> item stays open
#    exit 2 = no executable gate ran (UNOBSERVED) -> item stays open, loop stops
#    A gate command set nobody approved is skipped in a non-interactive shell
#    and counts as UNOBSERVED. Approve it once, interactively, before the night.
#    This script does not set HYODO_GATES_TRUST_ALL; that would be a fake green.
if [ "$DRY_RUN" = 1 ]; then
  say "  (dry-run) hyodo check --quiet   (in $WORKTREE)"
else
  set +e
  (cd "$WORKTREE" && hyodo check --quiet)
  CHECK_RC=$?
  set -e
  case "$CHECK_RC" in
    0) say "gates     : PASS" ;;
    1) say "gates     : FAIL — item stays open on branch $BRANCH"; exit 1 ;;
    *) say "gates     : UNOBSERVED (exit $CHECK_RC) — no evidence, not green; stopping the loop"; exit 2 ;;
  esac
fi

# 7. [HYODO] Record what happened as an audit event (digest-only by default)
#    and render the SARIF 2.1.0 report from the local ledger.
RESULT="$(mktemp)"
#    uuidgen and shasum are absent from minimal images (alpine, *-slim). A
#    pipeline reports its LAST command's status, so `uuidgen | tr || echo ...`
#    never reaches its fallback: it yields an empty value, HyoDo rejects the
#    event as invalid_field, and the case below would misreport that rejection
#    as a policy DENY -- sending the morning operator to policy.toml instead of
#    the missing tool. `|| true` keeps `set -o pipefail` from killing the run
#    before the fallback is applied.
EVENT_ID="$(uuidgen 2>/dev/null | tr 'A-Z' 'a-z' || true)"
[ -n "$EVENT_ID" ] || EVENT_ID="00000000-0000-4000-8000-000000000002"
ARGS_DIGEST="$(printf 'hyodo check --quiet' | { shasum -a 256 2>/dev/null || sha256sum 2>/dev/null; } | cut -c1-12 || true)"
[ -n "$ARGS_DIGEST" ] || ARGS_DIGEST="000000000000"
cat >"$RESULT" <<JSON
{"schema_version":"hyodo.agent-event/v1","event_id":"$EVENT_ID",
 "run_id":"00000000-0000-4000-8000-0000000000aa","ts":"$(date -u +%Y-%m-%dT%H:%M:%S+00:00)",
 "kind":"tool_result","step_index":1,"actor":"agent",
 "tool":{"name":"Bash","args_digest":"$ARGS_DIGEST","paths":[]},
 "io":{"input_digest":null,"output_digest":null,"bytes_in":0,"bytes_out":0},
 "policy":{"decision":null,"rule_id":null,"reason":null},
 "meta":{"model":"factory-loop","tags":["factory-loop","gate-result","$SLUG"]}}
JSON
if [ "$DRY_RUN" = 1 ]; then
  say "  (dry-run) hyodo event record --file $RESULT --policy $POLICY --root $WORKTREE"
else
  set +e
  hyodo event record --file "$RESULT" --policy "$POLICY" --root "$WORKTREE"
  RECORD_RC=$?
  set -e
  case "$RECORD_RC" in
    0) ;;
    1) say "record    : DENY — the gate-result event violates the fence; item stays open"; exit 1 ;;
    3) say "record    : ASK — operator decision required before this evidence counts"; exit 3 ;;
    *) say "record    : UNOBSERVED (exit $RECORD_RC) — ledger append not observed"; exit 2 ;;
  esac
fi
run hyodo report --format sarif --root "$WORKTREE"

# 8. [HOST] Open the PR with the evidence. Merge is a human decision; HyoDo's
#    receipts and scores are review signals, never approval.
if [ -n "${FACTORY_PR_CMD:-}" ]; then
  run bash -c "cd '$WORKTREE' && $FACTORY_PR_CMD"
else
  say "PR        : FACTORY_PR_CMD not set — open the pull request from $WORKTREE by hand"
fi
say "done      : $SLUG reached PR stage; queue item stays [ ] until a person merges"
