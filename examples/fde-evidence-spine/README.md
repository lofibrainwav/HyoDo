# FDE Evidence Spine (HyoDo Phase 1)

Minimal examples for the opt-in agent event ledger and local policy gate.

## Claims (honest)

- HyoDo validates events, appends an audit ledger, and can stamp ALLOW/DENY.
- HyoDo is **not** a full tool-call interceptor or agent runtime.
- DENY must be enforced by the caller (FDE script, MCP middleware, agent loop).
- Default storage is **digest-only**; use `--full-body` only when raw text retention is accepted. Who may enable it, that HyoDo does not rotate or redact the ledger, and that a client cannot self-upgrade: [`docs/FULL_BODY.md`](../../docs/FULL_BODY.md).
- `allowed_tools` in this example uses demo names (`search`, `read_file`).
  For a dual-host copy file (Claude Code + Cursor/demo names) see
  [`examples/host-policies/`](../host-policies/). That file is not a
  Cursor/Codex hook adapter; `hyodo connect cursor` stays UNOBSERVED.

## Quick try

```bash
# From a HyoDo checkout with editable install:
hyodo event validate --file examples/fde-evidence-spine/sample-tool-call.json

hyodo policy check \
  --file examples/fde-evidence-spine/sample-tool-call.json \
  --config examples/fde-evidence-spine/policy.toml

# Record under a temp root (writes .hyodo/agent-events.jsonl)
mkdir -p /tmp/hyodo-fde-demo
cp examples/fde-evidence-spine/policy.toml /tmp/hyodo-fde-demo/.hyodo/policy.toml
hyodo event record \
  --file examples/fde-evidence-spine/sample-tool-call.json \
  --root /tmp/hyodo-fde-demo \
  --policy /tmp/hyodo-fde-demo/.hyodo/policy.toml
```

## Exit codes

| Command | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| `event validate` | valid | invalid | unreadable input | not applicable |
| `event record` | recorded (+ ALLOW or no policy) | invalid or DENY | unreadable / policy unobserved / append fail | ASK |
| `policy check` | ALLOW | DENY | unobserved (missing policy or invalid event) | ASK |

## Adapter sketch (caller-owned)

```text
for each agent step:
  build event JSON (prefer digests over full bodies)
  hyodo event record --file step.json --policy .hyodo/policy.toml --json
  if exit == 1 and decision == DENY: stop agent
  if exit == 2: treat as unobserved — do not pretend safe
  if exit == 3 and decision == ASK: obtain operator decision before continuing
```

Trust is explicit and local. It is capped by `[trust].max_level` and is never
granted by the tracked policy file alone:

```bash
hyodo policy trust grant --level 2 --root .
hyodo policy trust show --root . --json
```
