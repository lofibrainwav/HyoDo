# Native host adapters

HyoDo separates three facts for every host:

| Fact | Meaning |
|---|---|
| `platform_contract` | The host documents a hook surface. |
| `hyodo_adapter` | This package can normalize the host payload. |
| `live_canary` | This exact installed host emitted a payload through HyoDo. |

Cursor and Codex currently have documented hook contracts. HyoDo's native
adapters normalize their tool hooks into `hyodo.agent-event/v1`:

- Cursor: `preToolUse`, `postToolUse`, `beforeShellExecution`,
  `beforeMCPExecution`, `afterShellExecution`, `afterMCPExecution`, and
  `afterFileEdit`.
- Codex: `PreToolUse` and `PostToolUse`.

The adapters do not claim coverage for events that the current HyoDo v1 event
schema cannot represent. Cursor and Codex subagent lifecycle events, and
Codex `PermissionRequest`, therefore return an explicit unsupported reason;
callers must surface that as `UNOBSERVED`. They are not silently converted to
tool calls or model responses.

The observation adapters are pure mappers. They do not append to the ledger
or evaluate policy. The CLI remains responsible for validation, policy, and
recording; the native response adapters serialize a policy decision into the
host's stdout contract:

- Cursor: `--native-response` emits `permission` and optional `updated_input`.
- Codex: `--native-response` emits `hookSpecificOutput` with
  `permissionDecision`/`updatedInput` or `PermissionRequest.decision`.

This proves response serialization only. It does not prove that an installed
host invoked the command or honored the response. Native response adapter
fixtures are `BUILT`; live enforcement remains `UNOBSERVED` until a real host
receipt is captured.

## Live-canary rule

Passing adapter fixtures proves only `hyodo_adapter = BUILT`. It does not prove
`live_canary = OBSERVED`. A canary receipt must include the installed host
version, host event name, HyoDo commit, package install mode, and the resulting
canonical event. Hosted tools or specialized host paths not covered by a canary
remain `UNOBSERVED`.

## Current live-canary state

| Host | `live_canary` | Receipt |
|---|---|---|
| Codex | `OBSERVED` (manual wiring) | `docs/research/CODEX_LIVE_CANARY_2026-09-10.md` |
| Cursor | `UNOBSERVED` | adapter fixtures only; no live host observed |

An installed `codex-cli 0.154.0` emitted `PreToolUse` and `PostToolUse` through
`hyodo event record --hook codex` and left two canonical events carrying
`host:codex`. The wiring was written by hand: `hyodo connect` has no installer
for either host.

## Installing a hook is not observing one

A host can require a person to approve a hook before it runs, and Codex does.
Writing the file leaves three distinguishable states:

```text
CONFIGURED      the hook file names HyoDo
TRUST_PENDING   the host has not yet been told to run it
OBSERVED        a payload from that host reached the ledger
```

These subdivide `live_canary`; they are not a fourth provenance axis. Codex
records approval in `config.toml` under `hooks.state`, keyed by hook file path
and snake_case event name, with a hash over the hook's own serialization. The
hash cannot be reproduced from the command text, so the record cannot be
written from outside the host — approval is a human action by design.

An installer must therefore report `CONFIGURED` and `TRUST_PENDING` rather than
"connected", and must say that editing the command invalidates the approval.
