---
description: "[Simple] Safety and risk early-warning scan"
allowed-tools: Read, Glob, Grep, Bash(git diff:*), Bash(hyodo:*)
impact: LOW
tags: [simple, safety, security, beginner]
mode: simple
alias: strategist
---

# /safe - safety scan

Looks for **high-risk signals** in the current change first. (Advanced: `/strategist`)

`/safe` and `hyodo safe` are early-warning tools. They do not replace a full security
scanner, SAST, dependency audit, or human security review.

## Usage

Agent slash command:

```text
/safe
/safe "path/to/file"
```

Vendor-neutral CLI:

```bash
hyodo safe
hyodo safe path/to/file_or_dir
hyodo safe --strict
```

## What it checks

| Item | Looks for |
|------|-----------|
| Secrets | API key / token / private key patterns |
| Dangerous commands | `rm -rf`, `DROP DATABASE`, force push, etc. |
| Production impact | migration, deploy, schema-change signals |
| Rollback hint | presence of rollback/migration wording (not a guarantee) |

## Default behavior

1. If a path is given, read that file/directory.
2. If no path is given, scan `git diff HEAD` (or `git status` if empty).
3. Print matches with a risk score.

## Example output

```text
Safety scan result:
source: git diff HEAD

OK Secrets exposure
OK Dangerous commands
WARN Production impact
OK Rollback signal

Risk: caution (15/100)
-> Proceed only after explicit review
```

## Risk levels

| Score | Meaning | Action |
|-------|---------|--------|
| 0-10 | low | Candidate to proceed — final approval is human |
| 11-30 | caution | Review, then proceed |
| 31+ | high | Review required |

---

*For deeper analysis use `/strategist` or `SECURITY.md`.*
