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

The adapters are pure mappers. They do not append to the ledger, evaluate
policy, or enforce a host decision. The caller remains responsible for
validation, policy, recording, and the host-specific response contract. The
CLI can therefore calculate and print a HyoDo decision for a native
pre-action payload, but this release does not yet emit Cursor's or Codex's
native allow/deny/rewrite response envelope. Native enforcement parity is
still `UNOBSERVED`/`NOT_BUILT` and must not be inferred from a mapper fixture.

## Live-canary rule

Passing adapter fixtures proves only `hyodo_adapter = BUILT`. It does not prove
`live_canary = OBSERVED`. A canary receipt must include the installed host
version, host event name, HyoDo commit, package install mode, and the resulting
canonical event. Hosted tools or specialized host paths not covered by a canary
remain `UNOBSERVED`.
