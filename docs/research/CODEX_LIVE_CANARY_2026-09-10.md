# Codex live canary — an installed host reaching the ledger

## Status

`OBSERVED / MANUAL WIRING / ISOLATED HOME`

An installed Codex process emitted its own tool hooks through HyoDo and left
two canonical events. This is the first time a live host callback has been
observed; every prior host receipt fed a synthetic payload to the CLI.

## Live-canary receipt

`docs/HOST_ADAPTERS.md` requires five facts. All five:

| Fact | Value |
| --- | --- |
| installed host version | `codex-cli 0.154.0` |
| host event name | `PreToolUse`, `PostToolUse` |
| HyoDo commit | `3cd1ce9f399d07bbb404454d7342ee81fa3287cb` (tag `v4.19.2`) |
| package install mode | `pip install --no-cache-dir hyodo==4.19.2` into an empty venv; PyPI wheel, not the checkout |
| resulting canonical event | two lines, below |

```json
{"kind": "tool_call",   "event_id": "codex:PreToolUse:call_3etgvhn5",
 "tags": ["host:codex", "host_event:PreToolUse"],  "step_index": 0}
{"kind": "tool_result", "event_id": "codex:PostToolUse:call_3etgvhn5",
 "tags": ["host:codex", "host_event:PostToolUse"], "step_index": 1}
```

`call_3etgvhn5` is the tool id Codex issued. It was not chosen by the person
running the canary, which is what separates this from a fixture.

The ledger kept its privacy shape: the command survives only as
`tool.args_digest = 39704f9019ee`, and `tool.paths` / `tool.urls` are empty.

## How it was run

A separate `CODEX_HOME` under a scratch directory, so the operator's own
`~/.codex` was never read from or written to. The isolated home used a local
model over Ollama, so no account credential was involved. Sandbox `read-only`,
approval `never`.

## Negative controls

A canary that cannot fail proves nothing. Two controls:

| Control | Expected | Observed |
| --- | --- | --- |
| hooks installed but not trusted | no ledger line | `NO HOOK FIRED`, ledger absent |
| a prompt that uses no tool | ledger does not grow | 2 lines before, 2 lines after |

The first control was not designed; it happened. The first run recorded
nothing, and replacing the hook command with a logging probe is what separated
"HyoDo refused it" from "the hook never ran".

## What this measurement found

### 1. Writing the hook file is not enough

Codex will not run a hook until a trust record exists in `config.toml`:

```toml
[hooks.state."<hooks.json path>:pre_tool_use:0:0"]
enabled = true
trusted_hash = "sha256:..."
```

The key uses the snake_case event name even though `hooks.json` spells it
`PreToolUse`. The hash is over an internal serialization: hashing the command
string, the command plus newline, and the hook object as compact or sorted
JSON all fail to reproduce a recorded value, so the record cannot be
synthesized from outside.

Codex's own hook screen already separates these states:

```text
Event          Installed   Active   Review
PreToolUse     1           0        1
PostToolUse    1           0        1
```

A person approved both, and the same command then recorded both halves.

This is a product contract, not an obstacle. Any future `hyodo connect codex`
writes a file and stops there; it must report something like `CONFIGURED` and
`TRUST_PENDING` rather than "connected", and changing one character of the
command invalidates the hash and requires approval again.

### 2. `tool_result` arrives empty

Both events carry `io.output_digest = null` and `io.bytes_out = 0`. The
result half records that a tool returned, not what it returned, so
`shell.true` and `shell.false` are indistinguishable in the ledger. Adapter
fixtures supply an `output` field and therefore never showed this.

### 3. The two halves are not linked

`parent_event_id` is `null` on the `tool_result`. The pair shares a tool id
and is adjacent by `step_index`, but nothing in the event points from the
result back to the call, so a graph reader cannot join them from the event
alone.

Findings 2 and 3 are recorded here as measurements. Neither is repaired in
this change.

## What remains UNOBSERVED

- **Cursor.** Its adapter is fixture-verified and `~/.cursor/hooks.json` uses a
  flat `preToolUse` / `postToolUse` shape, but no live Cursor process has been
  observed.
- **`hyodo connect` for either host.** There is still no installer; this canary
  was wired by hand.
- **The operator's real Codex environment.** Deliberately untouched.
- **Specialized Codex paths.** Only a shell tool call was exercised. MCP calls,
  file edits, and `PermissionRequest` remain unobserved.
