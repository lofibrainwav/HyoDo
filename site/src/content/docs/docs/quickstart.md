---
title: Quickstart
description: Install HyoDo and run its first checks against an existing repository.
---

HyoDo adds local guardrails to a repository you already own. It does not
replace your tests, linters, or CI — it reports on what actually ran.

If you would rather see one finished run before installing anything, read
[A worked result](/docs/worked-example/) first: a three-file project, the exact
command, and the verbatim output with its exit code.

## What HyoDo covers, and what it does not

| | |
| --- | --- |
| **Runs on** | macOS, Linux, Windows. Python 3.10 or newer. |
| **Reads** | your checkout, and the commands you register in `.hyodo/gates.toml`. |
| **Reports** | which gates ran, what they returned, and `UNOBSERVED` when nothing ran. |
| **Does not** | run your CI, gate your merges, approve or deploy anything. |
| **Does not** | send your code or results anywhere. Everything below is local. |
| **Optional** | an MCP adapter, so a host such as Claude or Cursor can read the same evidence. Step 5. |

A HyoDo result is evidence for a decision, never the decision. The exit codes
carry that meaning literally: `0` the gates you registered passed, `1` one
failed, `2` nothing was measured.

## Before you start

- **Python 3.10 or newer.**
- **A project you already work in**, checked out locally. HyoDo reports on
  checks that already exist, so the more your project has — pytest, Ruff, mypy,
  npm scripts, Go, Cargo, Makefile targets — the more `hyodo init` finds. A
  project with no checks is not a failure; `init` writes a commented starter
  file instead of inventing a passing gate.
- **A terminal in that project's directory.** Every command below reads and
  writes relative to the current directory, so run them from the project root:

  ```bash
  cd your-project
  ```

## 1. Install

```bash
pipx install hyodo
```

`pip install -U hyodo` also works.

Whichever you choose, remember it: the optional MCP step below has to install
into the *same* environment, and pipx keeps HyoDo in an isolated one.

## 2. Run an early-warning scan

```bash
hyodo safe --strict
```

`hyodo safe` is a fast, offline, pattern-based scanner. `--strict` makes it
exit non-zero on a high-severity finding instead of only reporting.
Use `--explain` for a stored explanation, `--quiet` for only the verdict,
or `--json` for a machine-readable receipt. These flags preserve exit codes.

Output also reports what was actually scanned: a `scope` field (`diff` /
`status` / `file` / `directory` / `external` / `none`) and a `coverage`
field (`FULL` / `PARTIAL` / `UNOBSERVED`), both present in `--json` and
printed in text mode as `Scope: <scope> · Coverage: <coverage>
(<scanned>/<total> files)`. A directory scan defaults to a 40-file cap —
`Coverage: PARTIAL` with a lower scanned-of-total count means raise
`--max-files` (or pass `0` for unlimited) to see the rest.

## 3. Set up your project checks

```bash
hyodo init
```

`hyodo init` detects tools your project already uses — pytest, Ruff, mypy,
Pyright, npm scripts, Go, Cargo, and Makefile targets — and lists their
commands in `.hyodo/gates.toml`.
If nothing supported is detected, it writes a commented starter file instead
of guessing at a check that doesn't exist.

## 4. Run the gates

```bash
hyodo check
```

`hyodo check` runs the gates recorded in `.hyodo/gates.toml`. An empty or
malformed gate configuration is not treated as a pass — it exits `2`.

## 5. Optional: connect an AI coding tool

Skip this step if you only want to run project checks. `hyodo start` can help
connect a detected host; it previews the changes and asks before writing.

```bash
hyodo start
```

The MCP adapter is an optional extra, not part of the base install, and it
must land in the same environment that runs `hyodo`. Install it the way you
installed HyoDo:

```bash
# if you used pipx
pipx install --force 'hyodo[mcp]'
```

```bash
# if you used pip
pip install 'hyodo[mcp]'
```

Running `pip install 'hyodo[mcp]'` after a pipx install is the common mistake:
it installs into a different environment, and `hyodo mcp` keeps reporting the
SDK as missing. If that happens, `hyodo mcp stdio` exits `2` and prints both
paths.

Claude Code gets hook wiring plus MCP. Cursor, VS Code, Claude Desktop, and
Codex get MCP config only. Direct `hyodo connect cursor` and
`hyodo connect codex` installers are not available (`UNOBSERVED`). To write
MCP config directly, use the matching host name:

```bash
hyodo mcp config claude-code --write
```

```bash
hyodo mcp config cursor --write
```

```bash
hyodo mcp config vscode --write
```

```bash
hyodo mcp config claude-desktop --write
```

```bash
hyodo mcp config codex --write
```

No bearer token or secret ever appears in this path. ChatGPT and the remote
connector (`mcp.hyodo.app`) are not live — they are contract-only,
`UNOBSERVED`, and not a shipped path next to `hyodo mcp stdio`.
`hyodo mcp config chatgpt` reports `UNOBSERVED` honestly instead of
guessing at a config format.

### First-use trust journey

For a new Claude Code connection, observe before enforcing when possible:

```text
orientation -> shadow observation -> policy review -> enforcement
```

`hyodo connect claude-code --shadow --write` records the policy decision it
would make without blocking the host. Re-run without `--shadow` only after the
starter policy has been reviewed. A connected hook is not the same as a
hardened policy; MCP configuration is not hook coverage.

The lifecycle boundaries are separate: hooks govern tool actions, pre-commit
checks govern commits, CI checks reproducibility, and release readback verifies
the served artifact. HyoDo skill commands are verification lenses over skill
rules, not an executable skill broker or end-user menu.

## Exit contracts

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event validate` | `0` valid · `1` invalid · `2` unreadable input |
| Policy result | `0` ALLOW · `1` DENY · `2` UNOBSERVED · `3` ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

`UNOBSERVED` means there is not enough evidence to say whether a check passed
or failed. It is neither a pass nor a failure.
Policy results come from `event record --policy` and `policy check`; an invalid
event can stop before policy evaluation.

Exit `2` means "not measured," not "measured and fine." A gate that never ran
does not get to look like a gate that passed.

## Next steps

- [Why HyoDo](/docs/why-hyodo/)
- [Philosophy → Math → Code](/docs/philosophy/)
- [Trust](/docs/trust/)
