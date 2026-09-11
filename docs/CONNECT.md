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
| `claude-code` | `.claude/settings.json`, `.hyodo/policy.toml` | Adds a `PreToolUse` hook (`hyodo policy check --stdin --hook claude-code`) and a `PostToolUse` hook (`hyodo event record --stdin --hook claude-code`); also bootstraps a permissive starter `.hyodo/policy.toml` when none exists yet, so the hooks have something to evaluate from the first tool call |
| `pre-commit` | `.pre-commit-config.yaml` | Adds the `hyodo-check` repo entry from this project's own `.pre-commit-hooks.yaml` |
| `github-actions` | `.github/workflows/hyodo.yml` | A workflow calling the `.github/actions/hyodo` composite action |
| `cursor` | — | Platform hook contract AVAILABLE; HyoDo adapter BUILT for native tool hooks. `connect` does not fabricate `.cursor/hooks.json`; live canary remains **UNOBSERVED** until an installed Cursor run emits a receipt. |
| `codex` | — | Platform hook contract AVAILABLE; HyoDo adapter BUILT for native `PreToolUse`/`PostToolUse`. `connect` writes nothing and reports `UNOBSERVED`. Live canary is **OBSERVED** for `codex-cli 0.154.0` by hand-written wiring (`docs/research/CODEX_LIVE_CANARY_2026-09-10.md`); that receipt describes a manual setup, not a `connect` target. |

A dual-host `allowed_tools` copy file (Claude Code names plus Cursor/demo
names) lives at [`examples/host-policies/`](../examples/host-policies/). It
is an allowlist, not a hook adapter — copying it does not make a live
Cursor/Codex canary observed. For a native hook command, pipe the host payload
to `hyodo event record --stdin --hook cursor` or `--hook codex` (and use
`hyodo policy check --stdin --hook ...` to calculate the HyoDo decision for a
pre-action payload). Add `--native-response --json` when the caller is a
Cursor or Codex command hook and needs the host-native response envelope.
Serialization is verified by fixtures; live host enforcement remains
`UNOBSERVED` until a real callback receipt is captured. The Codex canary
observed *recording*, not enforcement: it ran `event record`, and no host was
observed honoring a returned decision.

A host may also refuse to run a hook until a person approves it. Codex does,
and it keeps that approval in `config.toml` keyed by a hash of the hook, so
writing the file is not the same as being connected. See
[`HOST_ADAPTERS.md`](./HOST_ADAPTERS.md).

The adapter boundary is documented in [`HOST_ADAPTERS.md`](./HOST_ADAPTERS.md).
Fixture tests prove `hyodo_adapter = BUILT`; they do not promote
`live_canary = UNOBSERVED` to `OBSERVED`.

Every file HyoDo did not create itself gets a `.bak` alongside it on its first
write; everything HyoDo does not own in that file (other hooks, other
pre-commit repos, other keys) is left untouched. Running `--write` twice with
no other change makes no further edits. A `.hyodo/policy.toml` that already
exists — written by HyoDo before or authored by the operator — is never
overwritten; `connect` only creates one when the file is absent.

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

**The guarantee is unconditional**: shadow never returns a blocking exit
code, even when the policy file is missing, unreadable/invalid, or the hook
payload cannot be mapped, and even if the ledger append itself fails. Every
one of those cases still prints its diagnostic to stderr — prefixed
`[SHADOW, not blocking]` — and, wherever an event exists to write it onto,
records `policy.shadow: true` with `policy.decision: "UNOBSERVED"` and the
reason (e.g. `policy_missing`), so the evidence graph shows exactly what
would have blocked instead of silently going quiet. Since `connect
claude-code` now also bootstraps a starter `.hyodo/policy.toml` (see above),
a fresh shadow install has a policy to evaluate from the start; a policy
file deleted or moved out from under it afterwards still cannot make shadow
block.

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

The mapped event also carries `actor_id`, set to the hook payload's own
`session_id` — the same value already used as `run_id`. `actor_id` is an
optional, opaque label (`hyodo.agent-event/v1`): it lets the local graph
viewer and `hyodo report --format graph` tell two agents apart within one
run instead of collapsing them into a single row, and HyoDo never derives
identity or authorization from it.

`hyodo mcp continuity` reads that same `actor_id` to count hook-wired hosts:
every distinct value recorded on an `actor: "agent"` event — including one
recorded only under `--shadow` — is a distinct observed host (`source:
"hook"`, identity `hook:<actor_id>`), even though it never appears in the
MCP access ledger. A repository onboarded only through `hyodo connect
claude-code` (no MCP client ever ran) can still reach `coverage_status:
OBSERVED` once enough distinct actors have recorded events — and in that
case its receipt's `reasons` array can be empty (nothing is blocking
`READY`) while its `notes` array still lists `access_ledger_absent` and
`hook_only_observation`, so a reader can always tell no MCP client has ever
connected even on an otherwise-`READY` receipt.

The hook is a signal, not a sandbox. What the mapper copies out of
`tool_input`, what `allowed_tools` / `blocked_path_globs` can actually
see, and what the host still has to enforce are in
[`HOST_CONTRACT.md`](./HOST_CONTRACT.md).

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

## What to commit

`.hyodo/` mixes team-shared policy with per-machine runtime state. Track the
policy files everyone should share; ignore everything `connect` and the
other HyoDo commands write as a local ledger:

| Commit (team-shared policy) | Ignore (per-machine runtime) |
| --- | --- |
| `.hyodo/policy.toml` | `.hyodo/connect.json` |
| `.hyodo/gates.toml` | `.hyodo/policy-trust.json` |
| | `.hyodo/agent-events.jsonl` |
| | `.hyodo/reports/` |
| | everything else HyoDo writes under `.hyodo/` (manifests, config, evidence exports, and similar generated files) |

A `.gitignore` that keeps the two policy files while ignoring the rest:

```gitignore
.hyodo/*
!.hyodo/policy.toml
!.hyodo/gates.toml
```

## Known limitation

The pre-commit `rev` and the GitHub Actions composite-action ref are pinned
to this checkout's own version string (`v<version>`). `connect` runs with no
network access and cannot confirm that tag is a published, signed release in
`lofibrainwav/HyoDo` — verify it before relying on it in CI.
