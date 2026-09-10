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
