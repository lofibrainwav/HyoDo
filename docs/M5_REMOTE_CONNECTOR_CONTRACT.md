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

## M5-D — cross-model continuity

Issue #163's M5-D acceptance line: after one host runs `get_local_context`,
`hyodo_check`/`hyodo_safe`, and records an evidence event, "a second
supported AI host can connect to the same project evidence without creating
another truth store."

Honesty first: ChatGPT cannot be driven from this repository, and the remote
connector above stays contract-only. M5-D does not claim a live ChatGPT ↔
Claude handshake. What it proves locally is **host-independence**: two
distinct MCP clients — the stdio adapter and the paired loopback HTTP bridge,
each with its own caller identity — read and write the *same* workspace
truth (`.hyodo/agent-events.jsonl`, `.hyodo/policy.toml`,
`.hyodo/mcp-access.jsonl`) and observe identical results, with no second
store appearing anywhere under the workspace root.

`hyodo mcp continuity --root <workspace> --json` (`hyodo.continuity/v1`) is
the read-only receipt:

- **Truth store inventory.** The agent-event ledger and the MCP access
  ledger (required paths, may not exist yet) plus the policy file and the
  pairing file (both optional — absence is not a failure), each with a
  `sha256:` digest so two reads of the same workspace can be compared
  byte-for-byte.
- **Caller identities — two sources.** `source: "mcp"` rows are grouped
  from `.hyodo/mcp-access.jsonl`'s `caller_id` field. The stdio transport
  never sets one (`create_server`'s default, `run_stdio` never passes one),
  so every stdio session groups under the literal label
  `stdio (no pairing)`. A paired HTTP bridge caller always carries its
  pairing's `workspace_id` (`_create_http_app` passes it as `caller_id`
  when `paired=True`), grouped as `paired:<workspace_id>`. These are the
  only two shapes the access ledger can hold today; each identity's
  receipt row lists the distinct tool names it called. `source: "hook"`
  rows are grouped from `.hyodo/agent-events.jsonl`'s `actor_id` field
  instead: any event with `actor: "agent"` and a non-empty `actor_id` —
  the shape `hyodo connect claude-code` installs — counts as its own
  host, labeled `hook:<actor_id>`, even though it never touches the
  access ledger at all. Its row carries `calls` and `shadow`
  (`true`/`false`/`"mixed"`, from that event's `policy.shadow` flag) in
  place of `tools`. A shadow-mode event still counts the host as
  observed — nothing was enforced, but the host was seen. `hosts.by_source`
  reports the split as `{"mcp": N, "hook": M}`.
- **Cross-caller continuity.** Whether `hyodo_event_record` calls from
  different callers land in the one agent-event ledger — a per-caller call
  count next to the ledger's single digest, so "two callers, one file" is
  checkable rather than asserted.
- **`hosts observed: N/2 expected`.** Never a probability. `2` is the
  ceiling this slice measures — one stdio caller and one paired caller — not
  a claim about how many hosts a future deployment might pair.
- **`remote: UNOBSERVED` (`remote_not_probed`), always.** Identical semantics
  to the connector contract above: this receipt never touches DNS, OAuth, or
  `https://mcp.hyodo.app/mcp`.

Integrity and coverage are two different facts, reported as two separate
fields so "nothing is broken" can never be misread as "continuity is
connected":

- **`integrity_status`** is `READY` when every *present* store parses
  cleanly, and `CORRUPT` when any present store is unreadable or corrupt.
  An empty workspace has nothing to be corrupt, so it is `integrity_status:
  READY`.
- **`coverage_status`** is `OBSERVED` when at least the expected number of
  distinct hosts were seen — combining `mcp` and `hook` sources — *and* the
  agent-event ledger is present and readable *and* either the access
  ledger is present and readable or at least one `hook` host was observed;
  `PARTIAL` when some but not all of that holds (one host observed, or a
  required store missing); `UNOBSERVED` when zero hosts were observed and
  none of the four stores exist yet. A workspace observed only through
  Claude Code hooks — no MCP caller ever ran — can therefore still reach
  `OBSERVED` once it has `expected_hosts` distinct `actor_id`s, without an
  access ledger existing at all.
- **`status`** (kept for compatibility) is `READY` only when
  `integrity_status` is `READY` **and** `coverage_status` is `OBSERVED`.
  **READY means integrity READY and coverage OBSERVED; an empty root is
  UNOBSERVED** — a brand-new workspace with 0/2 hosts observed and no
  `.hyodo` stores at all used to read `status: READY` (nothing present was
  broken), which is a false green: it reads as "continuity connected" when
  it means "nothing present is broken". `reasons` explains which of
  `hosts_unobserved`, `hosts_partial`, `agent_events_absent`,
  `access_ledger_absent`, `pairing_absent`, or `policy_absent` applies, in
  addition to the corrupt/invalid reasons above.

Exit `0` means overall `status` is `READY`. Exit `2` means `UNOBSERVED`,
whether that is because a store is corrupt (`integrity_status: CORRUPT`) or
because coverage was never observed (`coverage_status` `PARTIAL` or
`UNOBSERVED`) — a present-but-corrupt `.hyodo/agent-events.jsonl` fails this
way, never silently as zero events, and neither does an empty root fail
silently as READY.

`hyodo mcp contract --json` additively folds the same receipt in as
`"continuity": {"local": "OBSERVED"|"UNOBSERVED", "remote": "UNOBSERVED"}` —
no existing contract key changes shape.

## Current capabilities

The contract advertises only the tools already served by the local adapter:
`get_local_context`, `hyodo_safe`, `hyodo_check`, `hyodo_event_record`,
`hyodo_policy_check`, and `hyodo_agent_rules`.

Tests bind this list to the real MCP server so connector metadata cannot silently
drift from the served tool surface.
