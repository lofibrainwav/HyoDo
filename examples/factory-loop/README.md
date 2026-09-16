# Factory loop (host-side example)

An unattended "software factory" takes features from a queue overnight, builds
each one on its own branch, has an independent reviewer attack it, and opens a
pull request only when the gates actually ran and passed. This directory shows
where HyoDo fits in that loop and, just as importantly, where it does not.

```text
[queue.md] -> [hyodo policy check] -> [build] -> [independent review]
           -> [hyodo check (fail-closed)] -> [hyodo event record + SARIF]
           -> [pull request] -> [a person merges]
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

## Files

| File | Owner | What it is |
|---|---|---|
| `queue.md` | host | Frozen feature contracts: goal, non-goals, mock, gate names. |
| `policy.toml` | host, evaluated by HyoDo | Night-shift fence: `max_steps`, `allowed_tools`, `blocked_path_globs`. |
| `factory-loop.sh` | host | Reference runner. `[HOST]` lines are yours to replace; `[HYODO]` lines call the CLI. |

## Quick try

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
