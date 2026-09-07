# `hyodo connect`

Wire a coding harness to HyoDo's gates instead of copy-pasting config by hand.
`connect` never re-implements a gate: every file it writes *calls* a `hyodo`
command that already ships in this package (`policy check`, `event record`,
`check`, `safe`).

Default is dry run. Nothing is written until you pass `--write`.

```text
hyodo connect [<target>] [--write] [--yes] [--shadow] [--status] [--root PATH] [--json]
```

- No target: detect harnesses present in this checkout; writes nothing.
- `<target>`: preview (or, with `--write`, perform) that target's writes.
- `--status`: report drift between what `connect` wrote and what's on disk.

## Targets

| Target | File | What it does |
| --- | --- | --- |
| `claude-code` | `.claude/settings.json` | Adds a `PreToolUse` hook (`hyodo policy check --stdin --hook claude-code`) and a `PostToolUse` hook (`hyodo event record --stdin --hook claude-code`) |
| `pre-commit` | `.pre-commit-config.yaml` | Adds the `hyodo-check` repo entry from this project's own `.pre-commit-hooks.yaml` |
| `github-actions` | `.github/workflows/hyodo.yml` | A workflow calling the `.github/actions/hyodo` composite action |
| `cursor` | — | **UNOBSERVED** — no verified hook contract; `connect` never fabricates a config format |
| `codex` | — | **UNOBSERVED** — same reason |

Every file HyoDo did not create itself gets a `.bak` alongside it on its first
write; everything HyoDo does not own in that file (other hooks, other
pre-commit repos, other keys) is left untouched. Running `--write` twice with
no other change makes no further edits.

The `pre-commit` and `github-actions` targets always enforce (`--shadow` has
no effect on them); only the Claude Code `PreToolUse` gate has a shadow mode.

## Shadow mode

```
hyodo connect claude-code --shadow --write
```

installs the same hooks, but the generated `PreToolUse` command carries an
extra `--shadow` flag. In shadow mode, `hyodo policy check` (and `hyodo event
record`) still evaluate the real policy and print/record the real decision —
stamped `policy.shadow: true` in the ledger — but the hook **always exits 0**,
so nothing is blocked. It's the on-ramp for trust level 0: the evidence graph
fills in while the operator keeps working undisturbed.

Leave shadow mode with a fresh, non-shadow write:

```
hyodo connect claude-code --write
```

## The Claude Code hook contract

Claude Code's `PreToolUse` hook only understands two outcomes: exit 0
(proceed) or exit 2 (block, with the reason on stderr). It has no native
"pause and ask a human" signal. Because of that, **`ASK` and `UNOBSERVED` are
enforced as a hard block** the moment this hook is installed — a real
behavior change, not merely a report shown later. `PostToolUse` cannot block
at all (the tool already ran); `hyodo event record --hook claude-code` is
fire-and-forget there and always exits 0 once the ledger append succeeds.

| HyoDo decision | Hook exit code |
| --- | --- |
| `ALLOW` | 0 |
| `DENY` | 2 |
| `ASK` | 2 (a harness that cannot express a third outcome enforces ASK as blocked) |
| `UNOBSERVED` | 2 |
| malformed/unparseable hook payload | 2 |

## Exit codes

`connect` (dry run, no target, or `<target>` preview): always 0 — a preview
cannot fail. `connect <target> --write`: 0 on success (including "already up
to date"), 1 if a per-target confirmation was declined without `--yes`, 2 on
an unknown/unsupported target or a write error. `connect --status`: 0 in
sync, 2 when a written file has drifted from its recorded digest
(`UNOBSERVED`).

State lives at `.hyodo/connect.json` (schema `hyodo.connect/v1`): which
targets were written, when, shadow or enforced, and the digest of every file
`connect` wrote — the source `--status` reads back.

## Known limitation

The pre-commit `rev` and the GitHub Actions composite-action ref are pinned
to this checkout's own version string (`v<version>`). `connect` runs with no
network access and cannot confirm that tag is a published, signed release in
`lofibrainwav/HyoDo` — verify it before relying on it in CI.
