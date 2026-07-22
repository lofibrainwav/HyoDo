# HyoDo MCP Connector Architecture (Design v1)

**Status:** Design SSOT — not a delivery promise.  
**Date:** 2026-07-22  
**Applies to:** public package (PyPI) + kingdom dogfood (Tailscale host)  
**Depends on:** HyoDo CLI ≥ 4.4.0 (evidence spine, BYOG, fail-closed exits)

This document defines how HyoDo becomes an **optional MCP connector** that
LLMs (Cursor, Claude Desktop/Code, Codex, etc.) can attach to — on the same
machine or, with explicit opt-in, across a private network (e.g. Tailscale) —
**without** replacing the CLI, breaking offline use, or inventing cloud claims.

---

## 1. Goals

| ID | Goal |
| --- | --- |
| G1 | **One core, many hosts** — CLI remains the only gate executor; MCP is a thin adapter. |
| G2 | **Public-safe by default** — install remains useful with zero network, zero MCP, zero auth. |
| G3 | **Connector address when needed** — remote clients get a stable URL + token, not a marketing story. |
| G4 | **Family / multi-machine** — Julie (or any second device) can attach over Tailscale without Vercel. |
| G5 | **Honest claims** — tools are opt-in; models must call them; no “auto-enlightenment”. |
| G6 | **FDE continuity** — agent steps can still flow into `event` / `policy` ledgers. |
| G7 | **Extensible** — new tools and transports without forking the CLI. |

## 2. Non-goals (explicit)

| ID | Non-goal | Why |
| --- | --- | --- |
| N1 | Replace Cursor/Claude as an agent runtime | HyoDo is a **gate**, not an orchestrator. |
| N2 | Full tool-call interceptor / monkey-patch of model SDKs | False green; framework-specific. |
| N3 | Default bind on `0.0.0.0` or public internet | Violates Hyo (data protection) and SECURITY_SURFACE. |
| N4 | Require Wallet / OAuth / SixXon for basic use | Not on public surface; not dogfood-ready as product. |
| N5 | Pull kingdom Redis / EROS pulse into public MCP | Breaks offline + thin dependency surface. |
| N6 | Vercel (or any serverless) as the gate executor | No customer FS, no BYOG tools, ephemeral. |
| N7 | “Zero-prompt understands everything” claim | MCP tools are passive until the host agent calls them. |
| N8 | Host machine Tailscale IP baked into the package | Each user brings their own network. |
| N9 | Automatic write of secrets into remote ledgers | Digest-only default stays. |

---

## 3. Personas and success

| Persona | Success looks like |
| --- | --- |
| **Public solo developer** | `pip install hyodo` → CLI works; optional MCP stdio on same machine. |
| **FDE on customer laptop** | Local gates + event/policy; no outbound; air-gap friendly. |
| **Family second device (e.g. Julie)** | Tailscale member + connector URL + token; uses **host workspace**, not magic remote FS. |
| **Kingdom dogfood (Commander host)** | Same binary; Tailscale IP already online; coexists with Orca. |
| **Security reviewer** | Default loopback/stdio; remote requires token; missing token = refuse, not open. |

---

## 4. Layered product model

```text
┌─────────────────────────────────────────────────────────────┐
│  LLM hosts (Cursor / Claude / Codex / …)                    │
│  register MCP: stdio command  OR  URL + Authorization       │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   Transport T0        Transport T1       Transport T2
   stdio (local)       loopback HTTP      private net HTTP
   no URL              127.0.0.1:port     Tailscale 100.x
                            │                  │
                            └────────┬─────────┘
                                     ▼
                        ┌────────────────────────┐
                        │  hyodo-mcp (adapter)   │
                        │  auth · tool schema    │
                        │  workspace root lock   │
                        └────────────┬───────────┘
                                     │ subprocess / library
                                     ▼
                        ┌────────────────────────┐
                        │  hyodo CLI (SSOT)      │
                        │  safe · check · init   │
                        │  event · policy · …    │
                        └────────────┬───────────┘
                                     ▼
                              project files
                              .hyodo/*
```

**Invariant:** Every mutation of quality truth goes through the **CLI contracts**
already tested on PyPI. MCP must not reimplement gate logic.

---

## 5. Progressive disclosure (public + family)

| Stage | User action | What activates | Network |
| --- | --- | --- | --- |
| **A. Taste** | `pip install hyodo` | CLI only | none |
| **B. Attach (same machine)** | Register MCP stdio pointing at `hyodo-mcp` | Core tools | none |
| **C. Deepen workspace** | `hyodo init` (± optional agent-rules pack) | BYOG gates.toml; optional rules snippet | none |
| **D. Connector address** | `hyodo mcp serve --token …` | Prints **Connector URL** | loopback or Tailscale **opt-in** |
| **E. Second device** | Client registers URL + token | Same host tools, remote LLM UI | private net only |

Stage D/E never auto-start on `pip install`.

### Optional agent-rules pack (Stage C)

- **Default `hyodo init`:** only `.hyodo/gates.toml` (today’s contract — preserve).
- **Opt-in:** `hyodo init --agent-rules` writes a **small, reviewed** snippet
  (e.g. `.hyodo/agent-rules.md` + documented copy targets for Cursor/Claude).
- Does **not** inject kingdom Redis, EROS thresholds, or AUTO_RUN.
- Philosophy names always dual-mapped to engineering terms (Truth=types, etc.).

---

## 6. Transports (T0–T2)

| ID | Name | Listener | URL example | Auth | Default |
| --- | --- | --- | --- | --- | --- |
| **T0** | stdio | process stdin/stdout | — | process isolation | **Yes (MCP)** |
| **T1** | loopback HTTP/SSE | `127.0.0.1` only | `http://127.0.0.1:8769/mcp` | token **recommended** | opt-in |
| **T2** | private-net HTTP/SSE | **explicit** Tailscale IP or `tailscale0` | `http://100.x.x.x:8769/mcp` or MagicDNS | token **required** | opt-in |

### Bind policy (fail-closed)

| Bind target | Allowed when |
| --- | --- |
| stdio | always for MCP package |
| `127.0.0.1` | `--bind loopback` (T1) |
| Tailscale IP (e.g. `100.109.255.2`) | `--bind tailscale` **or** `--bind-ip 100.x` + token |
| `0.0.0.0` / public interface | **Forbidden** in v1 public design (would need separate security RFC + Commander approval) |

Dogfood note (not packaged): Commander host measured 2026-07-22 —
`jays-macbook-pro` at Tailscale `100.109.255.2`, co-located with Orca.
Each public user substitutes **their** node IP.

### Port defaults

| Service | Port | Notes |
| --- | --- | --- |
| Dashboard (existing) | 8768 | loopback only; unchanged |
| MCP HTTP | **8769** | avoid clash with dashboard |
| Override | `--port` | always allowed |

### Connector URL print format (operator UX)

On successful serve:

```text
HyoDo MCP connector ready
  transport: tailscale
  url:       http://100.109.255.2:8769/mcp
  token:     <shown once; store in secret manager>
  workspace: /path/to/project
  tools:     get_local_context, hyodo_safe, hyodo_check, …
```

Clients copy **url + token**. No silent open endpoint.

---

## 7. Authentication and authorization

### 7.1 Public v1 auth: shared bearer token

- Generate cryptographically random token (`secrets.token_urlsafe(32)`).
- Store only a **hash** on disk (e.g. `.hyodo/mcp-token.sha256`), or require
  env `HYODO_MCP_TOKEN` each run (operator choice).
- Every HTTP request: `Authorization: Bearer <token>` exact match (constant-time).
- Missing/invalid token → **401**, no tool execution.
- stdio T0: no bearer (local process trust); optional workspace path lock still applies.

### 7.2 Explicitly deferred (not v1 public)

- OAuth / SixXon Wallet login  
- Per-user RBAC  
- mTLS  
- Kingdom Redis session  

These may appear later as **optional** profiles without becoming install defaults.

### 7.3 Workspace lock

- Serve is always bound to a **single workspace root** (`--root`).
- Tools refuse path escape (`..`, absolute paths outside root).
- Remote clients cannot re-point root without host restart + new token rotation.

---

## 8. Core tool surface (v1)

Minimal set — empty-feeling product is wrong; bloated toolbox is wrong.
**Core only** on attach; more tools behind explicit enable flags later.

| Tool name | Maps to | Side effects | Pillar map |
| --- | --- | --- | --- |
| `get_local_context` | git status, short diff, root path, optional recent log paths | read-only | Truth (situation) |
| `hyodo_safe` | `hyodo safe --json` | read-only scan | Goodness |
| `hyodo_check` | `hyodo check` (user gates or preset) | runs project tools | Truth/Goodness/Beauty |
| `hyodo_event_record` | `hyodo event record` | append ledger | Yeong |
| `hyodo_policy_check` | `hyodo policy check` | none (or with record via event) | Goodness / Hyo |
| `hyodo_score` | `hyodo score …` | none | review signal only |

### Tool contract rules

1. **JSON machine payloads** preferred for agent consumption; human summary ≤ short.
2. **Exit semantics preserved:** unobserved ≠ pass (exit 2 / structured error).
3. **Timeouts** on every subprocess (configurable; fail-closed on hang).
4. **No tool** claims automatic human approval or AUTO_RUN.
5. Optional **humility summary**: tool results may include a 3-bullet summary field;
   this does **not** constrain the host model’s chat UI.

### Explicitly not core v1 tools

- Arbitrary shell  
- Network fetch / browser  
- Wallet / payment  
- EROS Redis write  
- Full IDE “open tabs” (host-specific; optional later via host bridge)

---

## 9. Multi-machine semantics (Julie / other LLMs)

### What remote MCP **can** do

- Call host tools against the **host workspace**.
- Record agent events on the **host** ledger.
- Run host-installed linters/tests via BYOG.

### What remote MCP **cannot** do (without extra setup)

- See the client machine’s unrelated local files.
- Use tools only installed on the client.
- Bypass host policy.toml.

### Family playbook (informative)

1. Host: Tailscale up; `hyodo mcp serve --bind tailscale --token … --root ~/project`  
2. Host: share URL + token out-of-band (1Password / verbal / QR — not git).  
3. Client: same Tailscale tailnet; register MCP URL + header.  
4. Client LLM: call `get_local_context` then `hyodo_safe` / `hyodo_check`.  

**Vercel:** not part of this architecture for execution. Optional static docs only.

---

## 10. Packaging and versioning

| Artifact | Role |
| --- | --- |
| `hyodo` (PyPI, current) | CLI SSOT — always installable alone |
| `hyodo-mcp` **or** `hyodo[mcp]` extra | Optional adapter; may pull MCP SDK |
| Runtime deps of core wheel | Stay thin (`typer`, `rich`, …) — **no** MCP forced |

### Version coupling

- MCP adapter declares `Requires-Dist: hyodo>=4.4.0`
- Adapter version may track hyodo minor or ship as `hyodo` CLI subcommand
  `hyodo mcp …` implemented in optional module loaded only if deps present.

### Recommended UX

```bash
pip install 'hyodo[mcp]'     # or: pip install hyodo hyodo-mcp
hyodo mcp stdio              # T0
hyodo mcp serve --bind loopback --token-file …
hyodo mcp serve --bind tailscale --token-file …
```

If MCP deps missing: clear error + install hint (exit 2), not partial serve.

---

## 11. Security surface addendum (design-level)

Aligns with `SECURITY_SURFACE.md` and extends it:

| Threat | Control |
| --- | --- |
| LAN scanner hits open MCP | Default no listen; T2 requires token; no `0.0.0.0` |
| Token leak in chat logs | Print once; hash at rest; rotate command |
| Path traversal via tool args | Root jail |
| Remote DoS via long check | Timeouts + concurrency limit (1 heavy check default) |
| Stale “green” from client cache | Always re-run host CLI; no cache green |
| Confusion with dashboard CORS | Separate port; MCP not dashboard |
| Claim inflation | Docs + tests forbid “interceptor” / “auto approve” strings in public surface |

Hyō (data protection) native collector continues to flag non-loopback binds in
**scanned projects**; the MCP server itself must not introduce unguarded
non-loopback binds in the public package without this design’s opt-in path.

---

## 12. Observability and evidence

| Event | Where |
| --- | --- |
| Tool invocation | optional `.hyodo/mcp-access.jsonl` (digest of tool name + ok/deny + peer) |
| Gate runs | existing `history.jsonl` |
| Agent steps | existing `agent-events.jsonl` via `hyodo_event_record` |
| Auth failures | stderr + access ledger; no stack secrets |

Access ledger is append-only; default **off** for T0 to keep local friction low;
**on** for T1/T2.

---

## 13. Failure mode matrix

| # | Failure | Behavior |
| --- | --- | --- |
| F1 | MCP deps not installed | exit 2 + install hint |
| F2 | Token missing on T2 | refuse listen |
| F3 | Token invalid | 401 |
| F4 | Workspace path missing | exit 2 |
| F5 | `hyodo` binary missing | tool error JSON, not fake pass |
| F6 | Gate timeout | tool error `timeout`, not pass |
| F7 | Tailscale down / IP gone | serve fails at bind with clear message |
| F8 | Client offline from tailnet | client-side; host keeps serving |
| F9 | Concurrent check storm | queue or 429; no silent drop-as-green |
| F10 | Partial write to ledger | same as CLI: not reported as success |

---

## 14. Delivery phases (implementation order)

Each phase has acceptance tests; no phase claims the next.

### Phase M0 — Design seal (this document)

- [x] Goals / non-goals  
- [x] Transports, auth, tools, multi-machine  
- [ ] Issue opened; roadmap linked  

### Phase M1 — stdio MCP (public opt-in)

**Ship:** T0 + core tools wrapping CLI.  
**Accept:**

1. Cold install `hyodo[mcp]`  
2. Host registers stdio; `get_local_context` returns workspace root  
3. `hyodo_safe` returns JSON; exit contracts match CLI  
4. Core wheel without `[mcp]` still installs and runs CLI  

### Phase M2 — loopback connector URL

**Ship:** T1 `serve --bind loopback`, token recommended.  
**Accept:**

1. Prints `http://127.0.0.1:8769/mcp`  
2. Request without token rejected if token configured  
3. Port conflict with 8768 handled  

### Phase M3 — private-net / Tailscale bind

**Ship:** T2 `--bind tailscale` or `--bind-ip`, token **required**.  
**Accept:**

1. Binds only to given Tailscale IP (dogfood: Commander host)  
2. Second machine on same tailnet can list/call tools with token  
3. Without token: no useful data  
4. Docs: family second-device playbook  

### Phase M4 — polish (optional)

- MagicDNS name in printout  
- `hyodo mcp doctor` (tailscale up? token? port free?)  
- Access ledger default-on for T2  
- Optional agent-rules pack for init  

### Parallel (unchanged FDE CLI roadmap)

- FDE Phase 2 schema · 3 eval · 4 report remain CLI-first; MCP tools wrap when ready.

---

## 15. Claim language (public copy guardrails)

| Allowed | Forbidden until true |
| --- | --- |
| Optional MCP adapter for LLM hosts | “Install and AI automatically knows your kingdom philosophy” |
| Connector URL for private networks | “Cloud MCP on Vercel runs your gates” |
| Token-gated remote tools | “Zero-config remote access” |
| Wraps local `hyodo` CLI | “Full agent interceptor” |
| Digest-default ledgers | “Encrypted multi-tenant SaaS audit” |

Update `EXTERNAL_CLAIM_AUDIT.md` when M1 ships.

---

## 16. Relationship to existing surfaces

| Surface | Relationship |
| --- | --- |
| CLI 4.4.0 | Unchanged SSOT |
| Dashboard :8768 | Unrelated port; loopback only |
| Evidence spine | Tools call `event`/`policy` |
| ROADMAP | MCP adapter promoted from vague follow-up to phased M1–M4 |
| kingdom-cmd MCP | Pattern reference only; **no** Redis dependency copy |
| SixXon workspace | Philosophy inspiration; **not** a runtime dependency |
| Orca | Coexists on host; no coupling |
| Vercel | Docs hosting only (optional) |

---

## 17. Open decisions (require Commander only if changing defaults)

| # | Decision | Design default |
| --- | --- | --- |
| D1 | Package name `hyodo[mcp]` vs separate `hyodo-mcp` | Prefer `hyodo[mcp]` + `hyodo mcp` CLI |
| D2 | MCP protocol: SSE vs streamable HTTP | Follow current MCP SDK recommended remote transport at implement time |
| D3 | Token at-rest | Hash file under `.hyodo/` + chmod 600 |
| D4 | Allow `0.0.0.0` ever | No in v1 |
| D5 | Agent-rules in default init | No; opt-in flag only |

---

## 18. Acceptance checklist (definition of “no regrets”)

A release is complete for connector work only when:

1. Public CLI without MCP still green (regression).  
2. T0 works on clean machine.  
3. T1/T2 never listen without explicit serve.  
4. T2 refuses missing token.  
5. Path jail tested.  
6. Docs state multi-machine = host workspace semantics.  
7. Claim audit has no “auto philosophy / Vercel gates / interceptor” falsehoods.  
8. Dogfood: Commander Tailscale host serves; second device can call one tool.  
9. `verify-pypi` / CI matrix still pass for chosen packaging.  
10. SECURITY_SURFACE updated to match shipped code (not this design alone).

---

## 19. Summary for operators

- **Public today:** CLI only (4.4.0).  
- **Public design:** optional MCP; local first; remote only with token; Tailscale recommended for multi-machine.  
- **Commander dogfood:** this Mac’s Tailscale IP is the natural T2 host next to Orca.  
- **Not Vercel-executed.**  
- **Not Wallet-gated in v1.**  
- **Extensible** via tools + transports without rewriting gates.

---

## Document control

| Version | Date | Change |
| --- | --- | --- |
| v1 | 2026-07-22 | Initial full design (public + Tailscale family + non-goals) |

When implementation starts, open a HyoDo issue referencing this file and tick Phase M0 remaining boxes.
