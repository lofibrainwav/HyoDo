# Policy rule syntax (`hyodo.policy/v1`)

HyoDo policy is **not** a `[[rule]]` DSL. Declared TOML fields *are* the
rules. The evaluator attaches a `rule_id` and one of four decisions:
`ALLOW` (exit 0), `DENY` (exit 1), `UNOBSERVED` (exit 2), `ASK` (exit 3).

Event contract is separate: `hyodo.agent-event/v1`.

## Fields

| Field | Matches | Miss / omit |
| --- | --- | --- |
| `schema` | Must be `hyodo.policy/v1` | invalid policy → `UNOBSERVED` |
| `max_steps` | `step_index` hard cap (0-based) | no cap |
| `allowed_tools` | exact `tool.name` | **omit the key** = no name restriction; empty list = deny every named tool |
| `blocked_path_globs` | globs against `tool.paths` → `DENY` `data_boundary` | no path DENY |
| `ask_tools` | exact `tool.name` → external variable `ask_tools:<name>` | no ASK lift |
| `ask_threshold` | optional annotation threshold | default evaluator behavior |
| `[web].allowed_domains` | domain / `*.suffix` | unlisted → `web_domain_unlisted` (usually ASK) |
| `[web].allow_non_get` | default safe methods are GET/HEAD | |
| `[web].allow_credential_paths` | default `false` → credential-shaped URL is `DENY` | |
| `[trust].max_level` | ceiling only (0–3) | default level 1 |

Hard `DENY` always wins. Trust never softens a `DENY` and never upgrades
`ASK` into `DENY`. Trust is not granted by this file; grant lives in
untracked `.hyodo/policy-trust.json`. See [POLICY_TRUST.md](./POLICY_TRUST.md).

There is no argument matcher (`Bash(rm *)`), no regex path, and no
priority integer. Command-line shape is the host's job
(Claude Code `permissions` / hooks). HyoDo sees `tool.name`, declared
`tool.paths`, and normalized `tool.urls`.

## Evaluation order

1. Unreadable policy or event → `UNOBSERVED`
2. Hard DENY: `max_steps`, allowlist miss, `data_boundary`, credential-shaped URL
3. Collect external variables: `web_domain_unlisted`, `path_outside_root`, `ask_tools:<name>`, built-in web tools
4. Apply trust ladder (missing grant file while `[trust]` is set → `UNOBSERVED`)
5. Caller enforces the exit code

Built-in web tool names the evaluator already treats as web:
`web_fetch`, `browser`, `http`, `fetch`, `WebFetch`, `WebSearch`, plus
every `ask_tools` entry.

## Host tool names

`allowed_tools` is exact-string. The FDE demo names (`search`, `read_file`)
are **not** Claude Code or Cursor names.

Claude Code (permission / hook matcher strings):
`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `WebFetch`, `WebSearch`,
`Agent`, `Skill`, `NotebookEdit`, `PowerShell`, `AskUserQuestion`,
`ToolSearch`, `TodoWrite`.

Cursor has drifted across versions. Ship both families if the same
`policy.toml` must cover both hosts:

- older: `read_file`, `list_dir`, `grep_search`, `edit_file`,
  `run_terminal_command`, `codebase_search`, `web_search`
- newer reports: `Read`, `Write`, `StrReplace`, `Shell`, `Grep`, `Glob`,
  `SemanticSearch`, `WebSearch`, `WebFetch`, `Delete`

A ready-to-copy file:
[`examples/host-policies/claude-and-cursor.policy.toml`](../examples/host-policies/claude-and-cursor.policy.toml).

## `policy.toml` vs `gates.toml`

| File | Question | When |
| --- | --- | --- |
| `.hyodo/policy.toml` | May this tool call proceed? | each agent step |
| `.hyodo/gates.toml` | Did quality checks actually run? | commit / CI (`hyodo init` → `hyodo check`) |

Do not put host tool names in `gates.toml`. Do not treat a session
`Bash(pytest)` as proof that `hyodo check` ran.
