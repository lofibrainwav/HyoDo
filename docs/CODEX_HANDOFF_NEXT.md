# Implementer notes

This file used to be the 4.4.0 Codex queue (dated 2026-07-22). That queue
is finished on the local surface. Do not re-implement `hyodo mcp stdio`,
loopback/Tailscale serve, pairing, doctor, `schema check`, `eval`, or
`report`.

Current public version: the root `VERSION` file. Start from
[`docs/README.md`](./README.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Shipped locally

- Quality gates: `hyodo safe`, `init`, `check`, `score`
- Evidence: `event`, `policy`, `schema check`, `eval`, `report`
- Local MCP: `hyodo mcp stdio`, `serve --bind loopback|tailscale`, `pair`,
  `doctor`, `continuity`
- Local graph: `hyodo dashboard` `GET /graph` from `.hyodo/agent-events.jsonl`
- Claude Code hooks: `hyodo connect claude-code`

## Not shipped / not equivalent

- `https://mcp.hyodo.app/mcp` and ChatGPT: contract-only, `UNOBSERVED`.
  Not a path next to `hyodo mcp stdio`. See
  [`M5_REMOTE_CONNECTOR_CONTRACT.md`](./M5_REMOTE_CONNECTOR_CONTRACT.md).
- Cursor / Codex hook adapters: `UNOBSERVED`. Copy file only:
  [`examples/host-policies/`](../examples/host-policies/).
- Public `/evidence-graph/`: 14-event demo fixture by default. Optional
  local `hyodo.evidence-graph/v1` file in the browser. No remote ledger.
  Live ledger: `hyodo dashboard` at `/graph`.
- Integrity Score: review signal, never merge or deploy authority.

## Honesty docs

[`HOST_CONTRACT.md`](./HOST_CONTRACT.md), [`MISREAD.md`](./MISREAD.md),
[`FULL_BODY.md`](./FULL_BODY.md), [`CLAIMS.md`](./CLAIMS.md).

Demo `search` / `read_file` names in tests are fixtures on purpose.

## Out of scope

- Binding `0.0.0.0` / a public internet MCP listener
- Treating unobserved hosts as covered because Claude Code was wired
- Fabricating a Cursor hook schema
- Making Integrity Score an approver
