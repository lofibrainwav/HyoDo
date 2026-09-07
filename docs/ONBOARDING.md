# First-use onboarding (`hyodo start`)

The desired story (GitHub issue #163, M5-C): install, connect one host, then
type one prompt. Everything below that — stdio flags, Tailscale, pairing
tokens — stays available, but it is not what a first-time operator sees.

```text
hyodo start
```

## The four steps

1. **Workspace and detected hosts.** Shows the current directory and which
   hosts already look set up (`.claude`, `.cursor`, `.vscode`, `~/.codex`,
   Claude Desktop's config directory). Detection is presence-only — it never
   reads or trusts file contents.
2. **One audience question.** "Who is reading these results?" (vibe /
   engineer / professional). Unchanged from the profile HyoDo already ships;
   see `docs/AUDIENCE.md`. A profile is presentation wording only — it never
   changes a decision, exit code, or `--json` payload shape.
3. **One "connect which host now?" question.** At most three choices
   (detected hosts, capped at two, plus "skip"). Choosing a host previews
   the exact file(s) it would write and asks one yes/no confirm before
   anything happens. `claude-code` writes both the `hyodo connect` hook
   (`.claude/settings.json`) and the MCP entry (`.mcp.json`); every other
   host only writes its MCP entry.
4. **A first prompt to try**, plus the three commands to run by hand if you
   would rather not connect a host yet.

Non-interactively (`hyodo start` with stdin that is not a TTY — scripts, CI,
`| cat`), the same four steps print as plain text with the exact commands.
Nothing is asked and nothing is written.

At most three questions in the whole interactive flow, and nothing is ever
written without an explicit yes.

## Host table

| Host | Config file | Key | Verified? |
| --- | --- | --- | --- |
| `claude-code` | `<root>/.mcp.json` | `mcpServers.hyodo` | Yes |
| `claude-desktop` | platform-specific (below) | `mcpServers.hyodo` | Yes |
| `cursor` | `<root>/.cursor/mcp.json` | `mcpServers.hyodo` | Yes |
| `vscode` | `<root>/.vscode/mcp.json` | `servers.hyodo` | Yes |
| `codex` | `~/.codex/config.toml` | `[mcp_servers.hyodo]` | No (below) |
| `chatgpt` | — | — | Always `UNOBSERVED` (below) |

`claude-desktop`'s config file path depends on the platform:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Other (documented convention, not an officially shipped install):
  `~/.config/Claude/claude_desktop_config.json`

`codex`'s `[mcp_servers.hyodo]` TOML table is a documented format, not
verified against a live install — the same caution `hyodo connect` applies
to the cursor/codex hook contracts.

`chatgpt` always reports `UNOBSERVED`: the remote connector
(`https://mcp.hyodo.app/mcp`) is not live. See
`docs/M5_REMOTE_CONNECTOR_CONTRACT.md`.

Every generated entry is the same underlying command:

```json
{"command": "hyodo", "args": ["mcp", "stdio", "--root", "<absolute root>"]}
```

No bearer token or secret ever appears in this path — the stdio adapter
needs none. Pairing tokens exist only for the advanced Tailscale bridge
(`hyodo mcp pair`, `hyodo mcp serve --paired`); see `docs/CONNECT.md` and
`docs/M5_REMOTE_CONNECTOR_CONTRACT.md`'s M5-B section.

## `hyodo mcp config <host>`

```text
hyodo mcp config <host> [--root PATH] [--write] [--json]
```

Default is print-only: shows the exact snippet and the target file path.
`--write` merges it in key-level — every other server or key already in the
file is preserved. A file HyoDo did not create itself gets a `.bak`
alongside it on its first write; running `--write` again with no other
change makes no further edits (idempotent).

VS Code and Cursor also get a documented one-click deep link
(`vscode:mcp/install?...`, `cursor://anysphere.cursor-deeplink/mcp/install?...`)
printed as text — generated from the documented URL scheme, never claimed
tested against a live install.

Exit codes: print-only is always 0 unless the host is unknown or `chatgpt`
(2, `UNOBSERVED`). `--write`: 0 on success (including "already up to
date"), 2 on an unknown/unobserved host or a write error.

## Connecting a second host

Once one host is connected, connect a second one the same way (`hyodo mcp
config <host>` or a paired bridge via `hyodo mcp pair`) and run
`hyodo mcp continuity --root <workspace>` to see both hosts sharing the same
local evidence — no second truth store, ChatGPT/remote honestly `UNOBSERVED`.
READY means integrity READY and coverage OBSERVED; run it before either host
connects and it reports `UNOBSERVED` (0/2 hosts observed), never a false
READY on an empty workspace. See `docs/M5_REMOTE_CONNECTOR_CONTRACT.md`'s
M5-D section.

## Advanced paths (unchanged, still available)

- `hyodo connect` — Claude Code hooks, pre-commit, GitHub Actions, shadow
  mode. See `docs/CONNECT.md`.
- `hyodo mcp stdio` / `hyodo mcp serve` — local and Tailscale MCP transports.
- `hyodo mcp pair` / `hyodo mcp serve --paired` — the M5-B pairing lifecycle
  (bearer token shown once, digest-only on disk). See
  `docs/M5_REMOTE_CONNECTOR_CONTRACT.md`.
- `hyodo dashboard --open` — the local evidence-graph viewer.

None of this onboarding flow changes those contracts; it only gives a
shorter default path to the same writes.
