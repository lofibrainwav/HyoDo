# Adoption holes (honest)

This page is the third-party review turned into an operator checklist.
HyoDo remains local-first and fail-closed **after it is invoked**. Gaps
below are the cases where a green feeling outruns a measured decision.

## What HyoDo does not close by itself

1. **The agent can skip the gate.** HyoDo is not a process interceptor.
   If the host never calls `hyodo policy check` / `event record`, nothing
   is DENY'd.
2. **DENY is a signal.** The caller stops the agent. On Claude Code,
   `hyodo connect claude-code --write` is that caller: it maps decisions
   onto PreToolUse exit 0 / 2. Without that wiring, `policy check` exit 1
   is only a log line.
3. **Partial observation looks like safety.** `hyodo connect cursor` and
   `codex` stay `UNOBSERVED` until a verified hook contract exists.
   ChatGPT / `mcp.hyodo.app` are the same class. An observed Claude
   session does not cover an unobserved host.
4. **CI ≠ session.** `hyodo check` proves repository gates ran. It does
   not see a `.env` read that never landed in a commit.
5. **The ledger is self-reported.** Default storage is digest-only.
   Events the agent never emits cannot be denied after the fact.
6. **Wide allowlists are measured ALLOW.** Fail-closed rejects missing
   policy (exit 2). It does not reject a policy that lists every tool.
7. **`hyodo safe` is early-warning**, not a security audit.

## Do not pass HyoDo CLI exits to Claude unchanged

Bare CLI contract for `policy check` / `event record`:

| HyoDo | Meaning |
| --- | --- |
| 0 | ALLOW |
| 1 | DENY |
| 2 | UNOBSERVED |
| 3 | ASK |

Claude Code PreToolUse:

| Claude | Meaning |
| --- | --- |
| 0 + no JSON | no hook decision; **not** an approve |
| 0 + `permissionDecision: "deny"` / `"ask"` / `"allow"` | official JSON decision |
| **2** | block (stderr or JSON reason) |
| **1 and other codes** | **non-blocking error** — the tool still runs |

So `exit $?` after `hyodo policy check` is wrong: HyoDo DENY (1) becomes
a Claude non-blocking error.

What this package actually ships (`--hook claude-code`, installed by
`hyodo connect claude-code`):

| HyoDo decision | Hook exit |
| --- | --- |
| ALLOW | 0 |
| DENY | 2 |
| ASK | 2 (harness cannot pause; ASK is enforced as block) |
| UNOBSERVED | 2 |
| unreadable payload | 2 |

Shadow mode (`--shadow`) always exits 0 and records the real decision.
See [CONNECT.md](./CONNECT.md).

Official Claude JSON `permissionDecision` (`allow` / `deny` / `ask` /
`defer`) is richer than exit 0/2. HyoDo's shipped hook path still uses
0/2 so ASK cannot leak through as "ask the human later" on a harness
that will not wait. If you write a custom hook, do **not** forward
HyoDo's raw 1/3; translate.

Host bugs (deny ignored for some Task/Edit/MCP tools) are outside this
repo. Overlap Claude `permissions.deny` with `policy.toml`.

## Event mapping the hook already performs

`hyodo policy check --stdin --hook claude-code` maps:

- `tool_name` → `tool.name` (no aliasing)
- `tool_input.file_path` / `path` → `tool.paths`
- `tool_input.url` → `tool.urls`
- `session_id` → `run_id` and `actor_id`
- `tool_use_id` → `event_id`

`step_index` still has to come from the session. A hook that always
sends `0` makes `max_steps` useless.

## Minimum prove-it sequence

After `hyodo connect claude-code --write`:

1. `Read` a normal file → ALLOW / exit 0 → tool runs
2. `Read` `.env` → DENY `data_boundary` → hook exit 2 → tool blocked
3. Move `.hyodo/policy.toml` aside → UNOBSERVED → hook exit 2
4. Call `Bash` with `ask_tools` set → ASK → hook exit 2 unless you
   intended shadow mode

If (1) works and (2) does not, path mapping is dead.
If (3) proceeds, fail-closed is dead.

## File layout

```text
.hyodo/policy.toml          # tracked
.hyodo/gates.toml           # tracked, from `hyodo init`
.hyodo/policy-trust.json    # local grant, untracked
.hyodo/agent-events.jsonl   # local ledger, untracked
.claude/settings.json       # from `hyodo connect claude-code --write`
```
