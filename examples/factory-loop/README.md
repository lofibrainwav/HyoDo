# Factory loop (host-side example & Universal Skill Harness)

An unattended "software factory" takes features from a queue overnight, builds
each one on its own branch, has an independent reviewer attack it, and opens a
pull request only when the gates actually ran and passed. This directory shows
where HyoDo fits in that loop and, just as importantly, where it does not.

```text
[queue.md] -> [hyodo policy check] -> [build] -> [independent review]
           -> [hyodo check (fail-closed)] -> [hyodo event record + SARIF]
           -> [pull request] -> [a person merges]
```

## Architecture: HyoDo Core vs. Pluggable Factory Harness

- **HyoDo Core (`hyodo/`)**: Immutable, host-neutral trust, evidence, policy,
  and 6-virtue (`眞·善·美·仁·孝·永`) attestation engine. Never coupled to any
  external skill repository name or path.
- **Factory Harness (`examples/factory-loop/`)**: Replaceable host-side module
  manager (`factory/`, `adapters/`, `profiles/`, `hyodo_factory.py`) that mounts
  and unmounts external skills (`Agent Skills` `SKILL.md`, `Claude Code Plugins`
  with hooks/binaries like `gstack`, or zero-authority external evaluators like
  `JEV`) as hot-swappable parts.

```text
examples/factory-loop/
├── hyodo_factory.py          # Thin CLI entry point & backward-compatible facade
├── factory-loop.sh           # Reference unattended shell runner
├── factory/
│   ├── contracts.py          # ModuleRecord, SkillUnitSpec, PermissionBoundary
│   ├── registry.py           # .hyodo/factory/registry.toml & lock.json
│   ├── lifecycle.py          # add / enable / disable / update / rollback / remove / doctor
│   ├── router.py             # Progressive Disclosure natural-language router
│   └── runner.py             # Fault-isolated modular runner
├── adapters/
│   ├── agent_skills.py       # Standard SKILL.md / AGENTS.md loader
│   ├── claude_plugin.py      # Hook / binary / runtime plugin loader
│   └── external_evaluator.py # Zero-authority external evaluator adapter
└── profiles/
    ├── minimal.toml
    ├── development.toml
    ├── design.toml
    └── research.toml
```

## Claims (honest)

- HyoDo **runs the gates itself** (`hyodo check`). It never accepts a "tests
  passed" claim from the builder or the reviewer, so there is nothing for a
  hallucinated report to fool.
- `hyodo check` exits **0** only when at least one configured gate ran and all
  passed, **1** when a gate failed, and **2** when no executable gate ran.
  Exit 2 is UNOBSERVED. It is not a lie detector; it is the honest answer when
  there was nothing to observe. UNOBSERVED is never green.
- `hyodo policy check` evaluates one recorded event against `policy.toml`.
  HyoDo does not intercept tool calls by itself; the host (this script, an MCP
  middleware, a harness hook) must enforce a DENY.
- `hyodo event record` stores digests, not payloads, by default.
  `hyodo report --format sarif` renders a SARIF 2.1.0 file from that ledger.
- `hyodo eye` is **ephemeral** visual evidence: it deletes the capture after a
  TTL and records a perceptual hash plus a destruction proof. It does not
  attach screenshots to pull requests. If your loop needs a screenshot in the
  PR, that is host work.
- Branching, building, reviewing, opening and merging the PR are **host-owned**.
  HyoDo observes, validates, records, and measures. It never authorizes a
  merge. See [`docs/PRODUCT_BOUNDARY.md`](../../docs/PRODUCT_BOUNDARY.md).
- The trust ladder's `AUTO_RUN` stage is not authority either. The harness can
  build an approval *request* (`issue_host_approval_request`, schema
  `hyodo.factory-approval-request/v1`), but it cannot vouch for who approved
  it. `AUTO_RUN` promotion and every `auto` execution require an
  `authority_verifier` callable supplied by the host, for example one that
  checks a passkey-signed approval in the host's own approval system. Without
  one, a skill stops at `TRUSTED` / `ASK_COMMANDER`.
  `.hyodo/factory/trust_state.json` is a cache that any local process can
  rewrite. Its digest detects corruption, not forgery. Its `trust_stage`,
  `verifier_status` and `eval_verdict` can only block a run, never allow one:
  execution re-asks the host's verifier every time.
- The approval request binds the skill's `SKILL.md` hash, its permission
  boundary, the module source path, a digest of every file in the module tree
  (relative path, executable bit and content; only the module root's own
  `.git/` is left out, so nested `.git/` or `.hyodo/` directories are hashed;
  a symlink anywhere in the tree makes the module unbindable), the exact
  command the host will run (`None` for a run with no subprocess command), and
  the restrictions the host attests it enforces. Any difference blocks an
  `auto` run. A changed module tree or source path also demotes the skill's
  trust to `VERIFY`.
- An `auto` run re-checks the permission and every binding immediately before
  each skill's process starts, not once per wave, because an earlier skill in
  the same run can change files. A command then runs with
  `CLAUDE_PLUGIN_ROOT` / `CLAUDE_SKILL_DIR` pointing at a private, read-only
  copy of the module tree whose digest matched the approval at that moment;
  the copy is re-hashed after the run and discarded, and a change to it is a
  violation. What remains open: a command that names files of the original
  module by absolute path instead of through those variables reads the
  original, which can change after the check (such a run reports
  `executed_from: ORIGINAL_PATH_REFERENCED` and `module_snapshot_coverage:
  UNOBSERVED` instead of `MODULE_SNAPSHOT`); a process running as the same
  user can make the copy writable again (that is detected afterwards, not
  prevented); and files outside the module tree are not bound at all.
- What the runner enforces, per skill, is in `boundary_enforcement` on every
  skill output: `subprocess_exec` is `ENFORCED` (pre-exec gate for host
  commands); `filesystem_write=false` is `PARTIAL` (workspace files only, by
  POSIX write bits plus snapshot rollback; `.git/`, `.hyodo/` other than
  `.hyodo/factory/`, and paths outside the workspace are not covered); `network_access=false`,
  `browser_automation=false` and declared `allowed_paths` / `allowed_tools`
  are `UNENFORCED` (proxy variables are dropped and
  `HYODO_FACTORY_NETWORK_DISABLED=1` is set, which stops nothing; the
  allowlists are never evaluated). `auto` execution is refused while a
  boundary relies on a `PARTIAL` or `UNENFORCED` restriction, unless the host
  passes `host_enforced_restrictions` (for example because it runs commands in
  a network-isolated sandbox). Only those five names are accepted; the claim
  is reported as `HOST_ATTESTED`, not as something HyoDo observed, is bound
  into the approval request, and is recorded in agent events (`meta.tags`) and
  orchestration observations (`evidence_refs`). A write that a parallel wave
  makes is rolled back and recorded once for the wave with
  `attribution=UNOBSERVED`, because which skill wrote it is not observable.
- Every skill command runs in its own process group, and the whole group is
  killed when the skill exits (`descendants_killed_after_exit: true` when
  something was still running). Then `.hyodo/factory/` (registry, lock, trust
  cache, `host_taste.json`) is compared with its state before the skill ran:
  any change, including a planted symlink, is rolled back and recorded as
  `factory_state_write_forbidden`. This holds for read-only and write-allowed
  skills, and also when the wave ends in an exception. It does not cover a
  process that left the skill's process group (for example with `setsid`) or
  any other process running as the same user: such a process can still write
  there later, and that is not detected.
- `hyodo_factory.py run` exits `0` only when every routed skill actually
  executed and passed and an independent verifier (`--verify-cmd`) ran and
  passed, `1` on a fault, permission violation, failed build or failed/held
  verifier, and `2` (UNOBSERVED) otherwise. The result's `run_verdict` says
  which.
- `--selective` / `selective_activation=True` is task-scoped: it enables only
  the task's skills for the run and restores every module's and skill's
  previous `enabled` flag afterwards, also when the run raises. The run lock
  is held from before the activation until after the restore. A failed
  restore is reported (`registry_state_after_run: RESTORE_FAILED`, verdict
  `FAIL`) and the run's result is still returned.
- Personal Taste provenance is reported as it is: only rules from
  `.hyodo/factory/host_taste.json` or explicit feedback are `HOST_CONFIGURED`
  and handed to subprocesses as `HYODO_HOST_PERSONAL_TASTE_JSON`. A chosen
  profile's rules are `PROFILE_DEFAULT`. Gap analysis without `--profile` uses
  no profile (`"profile": "auto"`).
- `add` and `update` record each module's origin in `lock.json` (`origin`):
  source path, git remote URL (userinfo, query string and fragment removed),
  commit, dirty flag, and the module tree digest. `doctor` reports
  `module_tree_drift` and `module_origin_drift` for enabled modules and lists
  every module's state in `module_provenance` (`UNCHANGED`, `DRIFTED`,
  `UNRECORDED`, `UNBINDABLE`). An unrecorded or unbindable module, or an
  empty registry (`no_modules_registered`), makes `doctor` report
  `UNOBSERVED` with a warning; the CLI exits `0` HEALTHY, `1` DEGRADED, `2`
  UNOBSERVED. Nothing here verifies how many external repositories or skills
  exist anywhere; no such count is claimed.
- A run that is killed leaves `.hyodo/factory/run.lock` behind. The lock
  records the owner's pid and host; when that pid no longer exists on this
  host, the next run fails with `STALE_RUN_LOCK:<pid>` and `doctor` reports
  `stale_run_lock:<pid>` (plus `selective_activation_not_restored:<run_id>`
  if a `--selective` run was killed). Recover with
  `python examples/factory-loop/hyodo_factory.py --root <workspace> recover-stale-lock`:
  it removes the lock only when the owner is provably gone (same host, pid not
  running), restores the flags a killed `--selective` run left, and appends a
  receipt to `.hyodo/factory/lock_recoveries.jsonl`. A lock from another host
  or a running pid is never removed.
- `hosts` inspects local connect/MCP configuration plans only. It never runs a
  host, so `live_contract` is `UNOBSERVED` and `verified_live_contract` is
  `false` for every host.

## Files

| File | Owner | What it is |
|---|---|---|
| `queue.md` | host | Frozen feature contracts: goal, non-goals, mock, gate names. |
| `policy.toml` | host, evaluated by HyoDo | Night-shift fence: `max_steps`, `allowed_tools`, `blocked_path_globs`. |
| `factory-loop.sh` | host | Reference shell runner. `[HOST]` lines are yours to replace; `[HYODO]` lines call the CLI. |
| `hyodo_factory.py` | host | Modular skill harness CLI (`add`, `list`, `enable`, `disable`, `update`, `rollback`, `remove`, `doctor`, `route`, `discover`, `hosts`, `run`, `recover-stale-lock`) and 6-lens workspace bridge. |

## Modular Skill Lifecycle CLI (`hyodo_factory.py`)

```bash
# Discover compatible skill packages across external roots or catalogs
python examples/factory-loop/hyodo_factory.py discover "security" --search-root /path/to/skills --root .

# Attach external skill repositories or evaluators (auto-detects adapter)
python examples/factory-loop/hyodo_factory.py add /path/to/gstack --root .
python examples/factory-loop/hyodo_factory.py add /path/to/mattpocock-skills --root .

# List installed modules and active sub-skills
python examples/factory-loop/hyodo_factory.py list --root .

# Enable only a specific sub-skill (plus its required intra-module dependencies)
python examples/factory-loop/hyodo_factory.py enable gstack/qa --only --root .

# Disable a module or sub-skill
python examples/factory-loop/hyodo_factory.py disable gstack/qa --root .

# Update or rollback a module atomically
python examples/factory-loop/hyodo_factory.py update gstack --root .
python examples/factory-loop/hyodo_factory.py rollback gstack --root .

# Verify dependencies, content digests, script syntax, and path containment
python examples/factory-loop/hyodo_factory.py doctor --root .

# Inspect host connection and support matrix (Claude Code, Cursor, Codex, Antigravity)
python examples/factory-loop/hyodo_factory.py hosts --root .

# Route a natural-language task using Progressive Disclosure and slot deduplication
python examples/factory-loop/hyodo_factory.py route "Audit root cause and run browser QA" --root .

# Execute a modular run with isolated subprocesses and independent verification
python examples/factory-loop/hyodo_factory.py run "Implement feature with TDD" --verify-cmd "pytest -q" --root .

# Detach a module and clean up registered hooks and manifest entries
python examples/factory-loop/hyodo_factory.py remove gstack --root .
```

## Quick try (`factory-loop.sh`)

```bash
# From a checkout that has .hyodo/gates.toml (run `hyodo init` first):
cp examples/factory-loop/queue.md examples/factory-loop/policy.toml .
bash examples/factory-loop/factory-loop.sh --dry-run
```

The dry run prints every step without creating a worktree or running a build.

Before the first unattended run, approve the gate command set once, with a
person watching: run `hyodo check` interactively in the checkout and accept
the commands it shows. In a non-interactive shell HyoDo skips gates whose
command set nobody has approved and reports UNOBSERVED (exit 2). The runner
never sets `HYODO_GATES_TRUST_ALL=1` for you; pre-approving every command
blindly is exactly the kind of green this loop exists to refuse.

A real run needs three host hooks:

```bash
FACTORY_BUILD_CMD='your-agent build --item csv-export' \
FACTORY_REVIEW_CMD='your-agent review --adversarial --fresh-context' \
FACTORY_PR_CMD='gh pr create --fill' \
bash examples/factory-loop/factory-loop.sh
```

What the exit codes mean for the night shift:

| Exit | Meaning | What the loop does |
|---|---|---|
| 0 | item reached the PR stage, or the queue was empty | move to the next item, or stop |
| 1 | reviewer, a gate, or the policy said no (FAIL / DENY) | leave the branch, keep the item open |
| 2 | UNOBSERVED (no gates, unapproved gate set, no policy, no hook) | stop the loop; a person looks in the morning |
| 3 | the policy answered ASK (operator decision required) | stop the loop; a person decides in the morning |

DENY, ASK, and UNOBSERVED are three different answers and the loop keeps them
apart, exactly as `hyodo policy` does (`0` ALLOW · `1` DENY · `2` UNOBSERVED ·
`3` ASK).

## What this example deliberately leaves out

- A builder or reviewer implementation. HyoDo is model-agnostic; the loop
  works with any agent that can run inside a worktree. The reviewer must run in
  a separate process with a fresh context, assuming the build is wrong.
- Screenshot attachment or visual diffing in the PR.
- Anything that marks a queue item done. A person does that after the merge.
