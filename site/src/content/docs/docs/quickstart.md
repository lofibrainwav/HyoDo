---
title: Quickstart
description: Install HyoDo and run its first checks against an existing repository.
---

HyoDo adds local guardrails to a repository you already own. It does not
replace your tests, linters, or CI — it reports on what actually ran.

## 1. Install

```bash
pipx install hyodo
```

`pip install -U hyodo` also works. Python 3.10+ is required.

## 2. Run an early-warning scan

```bash
hyodo safe --strict
```

`hyodo safe` is a fast, offline, pattern-based scanner. `--strict` makes it
exit non-zero on a high-severity finding instead of only reporting.
Use `--explain` for a stored explanation, `--quiet` for only the verdict,
or `--json` for a machine-readable receipt. These flags preserve exit codes.

## 3. Absorb your existing checks

```bash
hyodo init
```

`hyodo init` detects tooling you already use — pytest, Ruff, mypy, Pyright,
npm scripts, Go, Cargo, Makefile targets — and writes `.hyodo/gates.toml`.
If nothing supported is detected, it writes a commented starter file instead
of guessing at a check that doesn't exist.

## 4. Run the gates

```bash
hyodo check
```

`hyodo check` runs the gates recorded in `.hyodo/gates.toml`. An empty or
malformed gate configuration is not treated as a pass — it exits `2`.

## 5. Connect

```bash
hyodo start
```

`hyodo start` shows detected hosts, asks one audience question, then offers
to connect one host with a preview and a single yes/no confirm. To connect a
host directly:

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
connector (`mcp.hyodo.app`) are not live yet — `hyodo mcp config chatgpt`
reports `UNOBSERVED` honestly instead of guessing at a config format.

## Exit contracts

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event` / `policy` | `0` valid/ALLOW · `1` invalid/DENY · `2` unobserved |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

Exit `2` means "not measured," not "measured and fine." A gate that never ran
does not get to look like a gate that passed.

## Next

- [Why HyoDo](/docs/why-hyodo/)
- [Philosophy → Math → Code](/docs/philosophy/)
- [Trust](/docs/trust/)
