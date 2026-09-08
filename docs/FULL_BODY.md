# Full-body ledger retention (`--full-body`)

Default ledger storage is **digest-only**. Raw prompt and tool text is not
written to disk unless an operator opts in. That opt-in is a policy decision:
who may enable it, that the file is not rotated or redacted, and that a
client cannot raise the ceiling on its own.

Citations: `hyodo/cli/main.py` (`event record --full-body`),
`hyodo/events.py` (`strip_full_bodies`), `hyodo/mcp_server.py`
(`full_body_requested` / `full_body_applied`),
[`CONNECT.md`](./CONNECT.md) ("What to commit").

## Default: digest-only

`hyodo event record` strips full bodies unless `--full-body` is set
(`strip_full_bodies`). That removes `io.input_text`, `io.output_text`, and
`tool.urls[].path`. Digests stay. The ledger path is
`.hyodo/agent-events.jsonl`.

## Who may enable

Only the operator on the machine:

- CLI: `hyodo event record --full-body`
- MCP stdio: `hyodo mcp stdio --allow-full-body`

`--allow-full-body` is operator consent at **server start**. A connected
client passing `full_body=True` without that flag does not store raw bodies.
The adapter still records the event digest-only and reports the denial
(`full_body_requested: true`, `full_body_applied: false`,
`full_body_denied_reason`). It does not silently pretend the bodies were
kept.

`hyodo mcp serve` has no `--allow-full-body` flag. HTTP servers always start
with `allow_full_body=False`.

## Retention

HyoDo does not rotate, encrypt, or redact the ledger. Enabling full-body
means the operator accepts raw text in `.hyodo/agent-events.jsonl` until
they delete it. The path is already untracked (see
[`CONNECT.md`](./CONNECT.md#what-to-commit) and the repo `.gitignore`).

Writes pin the file to owner-read/write mode (`0o600`). That is a
permission, not encryption.

## Redaction

None in-package. HyoDo does not scrub secrets, PII, or prompt text after
`--full-body` has written them. If the bodies must not live on disk, do not
pass `--full-body` or `--allow-full-body`.
