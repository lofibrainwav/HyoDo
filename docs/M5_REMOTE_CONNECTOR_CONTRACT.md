# M5 Remote Connector Contract

Status: M5-A contract only. This document does not claim a live remote service.

HyoDo keeps one product invariant across local and remote use:

> The HyoDo CLI remains the source of gate, policy, and evidence truth.

The remote connector exists to make attachment simple for ChatGPT, Claude, and
other MCP hosts without creating a second verification stack.

## North Star

**Connect once. Use any AI. Keep one Reality.**

Normal onboarding should feel like:

```text
Connect HyoDo
→ authenticate
→ pair workspace
→ tools appear
→ ask naturally
```

The operator should not need to learn bearer tokens, Tailscale addresses, MCP
JSON, or local port numbers for the normal path.

## Machine contract

`hyodo mcp contract --json` emits `hyodo.connector-contract/v1`.

Until M5-B serves and probes the endpoint, it must report:

```text
status       CONTRACT_ONLY
availability UNOBSERVED
```

The declared connector address is `https://mcp.hyodo.app/mcp` and the target
transport is streamable HTTP.

Authorization targets the MCP 2026-07-28 line:

- OAuth 2.0 Protected Resource Metadata (RFC 9728)
- OAuth / OpenID Connect authorization-server discovery
- Client ID Metadata Documents preferred over new DCR implementations
- RFC 9207 issuer validation
- refresh-token support for persistent host connections

The contract is declarative. DNS, OAuth, routing, and workspace reachability
must each be measured before availability can become observed.

## Ownership boundary

Cloud-side responsibilities are limited to identity, discovery, and routing.
Project execution remains local:

```text
ChatGPT / Claude
      ↓ OAuth
mcp.hyodo.app
      ↓ authenticated routing
paired device / workspace
      ↓
local HyoDo CLI
```

The remote path must not introduce arbitrary shell access, default source-code
upload, a public workstation listener, or a duplicate policy engine.

Digest-only evidence remains the default. Raw prompt/output storage still
requires explicit operator consent.

An unreachable or revoked workspace is `UNOBSERVED`, never PASS. HyoDo policy
signals remain evidence for the host/user; they never become human approval.

## M5-B — local bridge

M5-B proves the *local half* of the route described above: a paired,
root-locked workspace served over an authenticated loopback (or Tailscale)
route, whose revoke/disconnect states are measured and reported honestly.
It does not stand up `https://mcp.hyodo.app/mcp` — that address is still not
live, and `availability` in the machine contract stays `UNOBSERVED`.

What is measured:

- **Pairing lifecycle.** `hyodo mcp pair --root <workspace>` creates an
  untracked `.hyodo/pairing.json` record (`hyodo.pairing/v1`) and prints a
  32-byte urlsafe bearer token exactly once. Only the token's sha256 digest
  is ever written to disk. `hyodo mcp revoke` (alias `unpair`) and
  `hyodo mcp pairing show` read and update that same file.
- **Paired serving.** `hyodo mcp serve --bind loopback --paired` (and
  `--bind tailscale --paired`) verifies every request's bearer token against
  the pairing record instead of a static `--token`. The record is re-read on
  every request, so a revoke takes effect on the very next call — no restart
  required. A revoked pairing returns `401 {"state": "REVOKED"}`, no pairing
  file returns `401 {"state": "UNPAIRED"}`, and a present-but-unreadable file
  fails closed as `503 {"state": "UNOBSERVED"}` — never a silent PASS. The
  existing `HYODO_MCP_TOKEN` / `--token` path keeps working unchanged when
  `--paired` is not passed.
- **Contract reflection.** `hyodo mcp contract --root <workspace> --json`
  adds a `bridge` object — `{"pairing", "workspace_id", "root", "listener",
  "last_seen_at"}` — computed from that workspace's pairing file. `status`
  becomes `PAIRED_LOCAL` only when `bridge.pairing == "PAIRED"`; otherwise it
  stays `CONTRACT_ONLY`. Calling `build_connector_contract()` with no root
  stays a pure function and reports `bridge.pairing == "UNPAIRED"` without
  touching the filesystem.

What stays `UNOBSERVED`:

- Remote `availability` — DNS, OAuth, and routing for
  `https://mcp.hyodo.app/mcp` are not probed by this slice. The contract
  carries a `reasons` entry, `remote_not_probed`, to say so explicitly.
- `bridge.listener` reports `"loopback"` exactly when `bridge.pairing` is
  `PAIRED`, and `"none"` otherwise. This is a deterministic function of the
  local pairing state, not a live socket probe — the pairing record does not
  persist which listener it was created for, and a live probe on a fixed
  port risks a false positive from an unrelated local process. A dedicated
  live-reachability probe (loopback and Tailscale) is future work, not part
  of this contract's semantics today.

No new tool was added, no served tool runs a shell or reads/writes an
arbitrary path, and no second policy or gate engine was introduced — every
served tool still shells out to the `hyodo` CLI exactly as before. Digest-only
evidence remains the default.

M5-C local onboarding shipped; remote availability still UNOBSERVED.

## Current capabilities

The contract advertises only the tools already served by the local adapter:
`get_local_context`, `hyodo_safe`, `hyodo_check`, `hyodo_event_record`,
`hyodo_policy_check`, and `hyodo_agent_rules`.

Tests bind this list to the real MCP server so connector metadata cannot silently
drift from the served tool surface.
