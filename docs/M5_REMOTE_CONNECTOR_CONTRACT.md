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

## Current capabilities

The contract advertises only the tools already served by the local adapter:
`get_local_context`, `hyodo_safe`, `hyodo_check`, `hyodo_event_record`,
`hyodo_policy_check`, and `hyodo_agent_rules`.

Tests bind this list to the real MCP server so connector metadata cannot silently
drift from the served tool surface.
