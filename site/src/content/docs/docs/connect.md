---
title: Connect
description: Wire a coding harness to HyoDo's gates instead of copy-pasting config by hand — dry run by default.
---

## What it does

`hyodo connect` writes the config a coding harness needs to call HyoDo's
gates — it never re-implements a gate; every file it writes calls a
`hyodo` command that already ships (`policy check`, `event record`,
`check`, `safe`). With no target, it detects harnesses present in this
checkout and writes nothing. Default is dry run; nothing is written until
`--write` is passed.

```bash
hyodo connect claude-code --write
```

Supported targets: `claude-code` (Claude Code hooks), `pre-commit`,
`github-actions`. `cursor` and `codex` report `UNOBSERVED` — no verified
hook contract, so `connect` never fabricates a config format.

## What is stored

- `.hyodo/connect.json`: which targets were written, when, shadow or
  enforced, and the digest of every file `connect` wrote.
- A `.bak` alongside any file HyoDo did not create itself, on its first
  write.
- `hyodo connect claude-code --write` also bootstraps `.hyodo/policy.toml`
  when no policy file exists yet, and tracks its digest in `connect.json`
  the same way it tracks `.claude/settings.json` (so `--status` reports
  drift on it too). The starter policy is permissive by default — every
  restriction ships commented out — apart from an uncommented
  `blocked_path_globs` list (`.env`, `*.pem`, `id_rsa*`, `.hyodo/**`). It
  is a starting point for an operator to tighten, not a gate by itself. An
  existing policy file — HyoDo's own or the operator's — is never
  overwritten.

## What is never stored

- Anything HyoDo does not own inside a target file — other hooks, other
  pre-commit repos, other keys are left untouched.
- A silently-blocked decision: Claude Code's `PreToolUse` hook can only
  express exit 0 or 2, so `ASK` and `UNOBSERVED` are enforced as a hard
  block the moment the hook is installed — a real behavior change, not a
  report shown later. Shadow mode (`--shadow`) evaluates and records the
  real decision but always exits 0, for a disturbance-free on-ramp.

## Exit codes

| Outcome | Exit |
| --- | --- |
| Dry run, or `<target>` preview | 0 |
| `--write` succeeded (including "already up to date") | 0 |
| Confirmation declined without `--yes` | 1 |
| Unknown/unsupported target, or a write error | 2 |
| `--status`: in sync | 0 |
| `--status`: a written file drifted from its recorded digest | 2 |

## Full reference

[docs/CONNECT.md](https://github.com/lofibrainwav/HyoDo/blob/main/docs/CONNECT.md)
covers every target's exact writes and the Claude Code hook contract.

## Next

- [Skills](/docs/skills/)
- [Trust](/docs/trust/)
