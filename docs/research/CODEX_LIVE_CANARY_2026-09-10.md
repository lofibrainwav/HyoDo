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

---

# P1-B — what the host actually sends

A second observation, with a one-off probe that captured the host payload
before HyoDo's privacy boundary. The probe is over; the raw captures were
deleted and the canary hook is back to its privacy-minimized form. Only field
names, types, presence and digests are recorded here -- never a captured
value.

Two tool calls were observed, one succeeding and one failing.

## Field shape of a real Codex payload

```text
PreToolUse   cwd, hook_event_name, model, permission_mode, session_id,
             tool_input{command}, tool_name, tool_use_id, transcript_path,
             turn_id
PostToolUse  the same, plus tool_response
```

`tool_response` is a string in both the succeeding and the failing call. It is
the only field that differs between a call and its result.

## Layer judgement

| Axis | Host payload | Adapter | Canonical | Ledger |
| --- | --- | --- | --- | --- |
| output / result | OBSERVED (`tool_response`, str) | was UNOBSERVED, now OBSERVED | OBSERVED | `output_digest` |
| `exit_code` | UNSUPPORTED | no mapping | no field | — |
| success / failure / outcome | UNSUPPORTED | no mapping | no field | — |
| bytes in / out | UNSUPPORTED | not written | `0` | `0` |
| tool identity / correlation | OBSERVED (`tool_use_id`, `turn_id`) | PARTIAL (`tool_use_id` only) | OBSERVED | OBSERVED |

Two different gaps, kept apart:

- **adapter loss** — the host sent it and HyoDo dropped it: `tool_response`,
  and also `model`, `turn_id`, `permission_mode`, `transcript_path`.
- **host unsupported** — not in the payload at all, in either the succeeding
  or the failing call: `exit_code`, `status`, `success`, `outcome`, structured
  `error`, `bytes_in`, `bytes_out`.

Only the first kind is repaired here. Success and failure differ solely in the
text of `tool_response`, so distinguishing `shell.true` from `shell.false`
would mean parsing that text. That is inference, not observation, and it is
left `UNSUPPORTED_BY_HOST` rather than manufactured.

## Trust-scope semantics — `codex-cli 0.154.0`

Observed three times over, in both directions:

```text
CONFIGURED         the hook file names HyoDo
TRUST_PENDING      the host has not been told to run it
TRUSTED_ENTRYPOINT a person approved this exact command string
CONTENT_ATTESTED   UNOBSERVED
```

Changing the command stopped the hook from firing; re-approving recorded a new
`trusted_hash`; restoring the earlier command stopped it again. The approval
is therefore bound to the command string.

Whether the approval extends to content that the approved command later reads
or executes was not observed, and is recorded as `UNOBSERVED` rather than
assumed either way. This is the trust scope measured in this version, not a
vulnerability finding.

The practical consequence for HyoDo: an approved entrypoint and the mutable
content that entrypoint may later run are not the same fact, and an installer
must not report them as one.

## Live readback of the repair

```text
tool_call    codex:PreToolUse:call_7h22ksvt    output_digest  none
tool_result  codex:PostToolUse:call_7h22ksvt   output_digest  3baf75ce8847
```

The digest was recomputed independently with `content_digest` from what the
tool actually printed, and matched. A present digest alone would not have
shown that the right bytes were digested.

No raw response text appears anywhere in the ledger, and no captured payload
file remains.
