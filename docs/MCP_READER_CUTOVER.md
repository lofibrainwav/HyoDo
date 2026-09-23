# MCP reader cutover

A runtime is not promoted when the pointer moves. It is promoted when every
live reader has converged on the new slot.

## Why this exists

A `hyodo mcp stdio` reader resolves `--root` once, when it starts. If the host
later repoints a runtime symlink (for example `.../current`), readers that were
already running keep measuring the old slot. Pinning is deliberate: a session
whose target changed silently between two calls would be worse. Before this
gate, though, a stale reader could not be seen from outside the process, and it
kept answering as though it were current.

## What a reader does

- **Registers itself at startup** in `~/.hyodo/runtime/mcp-readers/<pid>.json`
  (override with `HYODO_MCP_READER_DIR`). The record holds PID, process start
  time, parent PID and host, server and Python version, configured and resolved
  root, and runtime commit. Normal exit removes the record. Before a new reader
  registers, startup GC also removes records whose PID/process-start identity
  is provably retired, covering SIGTERM, SIGKILL, crash, and reboot residue
  without treating an unobservable process identity as dead.
- **Checks its pin on every call.** If the configured root now resolves
  elsewhere (`root_moved`), no longer resolves (`configured_root_unresolvable`),
  the package file it imported now carries a different version
  (`code_replaced`), or that file can no longer be read (`code_unobservable`),
  the reader is `STALE`. Measurement tools (`hyodo_check`,
  `hyodo_safe`, `hyodo_policy_check`, `hyodo_event_record`,
  `hyodo_agent_rules`) then return exit code `2` with
  `STALE_RUNTIME_RECONNECT_REQUIRED`. `get_local_context` keeps working and
  reports the reader state under `reader`.
- **Attributes access rows.** Each `.hyodo/mcp-access.jsonl` row carries
  `server_pid`, `server_started_at`, `server_version`, and `runtime_commit`.
  Rows written before these fields existed read back as `null`.

## Census

```bash
hyodo mcp census --expect-root ~/.kingdom/runtime/hyodo/current \
  --from board-OLD --expect-version 4.21.4 --receipt promotion-census.json --json
```

The census joins registrations with the live process table. A reader instance
is identified by PID and process start time, so a reused PID never inherits an
old record.

| Reader state | Meaning |
|---|---|
| `CURRENT` | Registered, pinned to the promoted slot (and commit/version, when judged) |
| `STALE` | Registered, pinned elsewhere or on another commit/version |
| `UNKNOWN` | Live, but has no registration (for example it predates this gate) |
| `RETIRED` | Registration whose process exited or whose PID was reused (counted only) |

`cutover_status` is `PROMOTION_COMPLETE` (exit 0) only when
`stale + unknown = 0`; otherwise `PROMOTION_INCOMPLETE` (exit 1). If the process
table cannot be read the result is `UNOBSERVED` (exit 2). Zero live readers is an
observed, complete cutover.

## Boundary

HyoDo observes and records. It never restarts, kills, or reconfigures a reader,
and the census result is evidence for the host's promotion decision, not the
decision. The host owns the promotion: switching the pointer, reconnecting its
sessions, and refusing to call a promotion complete while the census says
otherwise.

A registration is observation evidence written by the reader itself, **not a
tamper-proof attestation**. A hostile process running as the same user could
forge or delete one. HyoDo does not defend against a hostile local host.

Readers started before this gate cannot register or check their pin. They show
up as `UNKNOWN`, and only the owning host can retire them (in Claude Code:
`/mcp` → `hyodo` → Reconnect).
