# Host contract (`hyodo connect claude-code`)

HyoDo evaluates a mapped event and emits `ALLOW` / `DENY` / `ASK` /
`UNOBSERVED`. It does not intercept the process. The host must enforce
the decision, and the mapper only copies a few `tool_input` keys.

This page is what an implementer hits after `hyodo connect claude-code
--write`. Wiring and exit codes stay in [`CONNECT.md`](./CONNECT.md).
First-run host detection is in [`ONBOARDING.md`](./ONBOARDING.md).
A dual-host `allowed_tools` copy file (not a hook adapter) is at
[`examples/host-policies/`](../examples/host-policies/).

Citations below are current `main` (`hyodo/connect.py`, `hyodo/policy.py`,
`hyodo/events.py`, `hyodo/cli/main.py`).

## Split of responsibility

| Surface | What HyoDo does | What the host still owns |
| --- | --- | --- |
| PreToolUse / PostToolUse | Map payload → `hyodo.agent-event/v1`, evaluate `.hyodo/policy.toml`, remap hook exit 0/2 | Whether the tool actually stops; overlap `permissions.deny` |
| `allowed_tools` | Exact, case-sensitive `tool.name` membership | Sending the real host name (`Read`, not `search`) |
| `Bash` / command body | Hash `tool_input.command` into `args_digest` | Argument / glob / `rm` policy |
| `WebFetch` / `WebSearch` | Domain rules only when `tool.urls` (and `tool.method`) are declared | Supplying a URL shape; host-side domain blocks |
| `blocked_path_globs` | `fnmatch` against mapped `tool.paths` | Declaring `file_path`; keys HyoDo does not copy |

## The hook is not a security boundary

`hyodo connect claude-code` writes only HyoDo-owned hook entries in
`.claude/settings.json` (`hyodo/connect.py` `build_claude_code_settings`).
It does not write Claude `permissions.deny`. Policy evaluation itself is
a signal: "HyoDo emits a decision object; the agent runtime must enforce
DENY" (`hyodo/policy.py` module docstring; same contract in
`hyodo/events.py`).

An inventory note that Claude Code has ignored hook deny on some Task /
Bash / Edit / MCP paths is **upstream**. This repository does not
reproduce that host bug. Treat it as a host-owned risk: overlap
`permissions.deny` with `policy.toml`, and do not treat the PreToolUse
hook as a sandbox.

On the shipped path, a measured `DENY` / `ASK` / `UNOBSERVED` is remapped
to hook exit 2 (`hyodo/cli/main.py` `policy check` with
`--hook claude-code`). Exit 2 is still only as strong as the host's
willingness to honor it.

## `allowed_tools` is exact `tool.name`

`evaluate_policy` denies a tool event when `tool.name` is missing from
the tuple, using Python membership — not a family, glob, or
case-fold (`hyodo/policy.py` `evaluate_policy`, `rule_id`
`tool_not_allowed`). `Bash` is not `bash`. `Read` is not `read_file`.
Demo / fixture names (`search`, `read_file`) are not Claude Code names
(`Read`, `Bash`).

Do not copy a second allowlist into this page. Trim
[`examples/host-policies/claude-and-cursor.policy.toml`](../examples/host-policies/claude-and-cursor.policy.toml)
to the hosts you actually run. That file is an allowlist, not proof that
`connect cursor` is observed.

## No `Bash(rm *)` argument matcher

There is no command-body rule in `hyodo.policy/v1`.
`map_claude_code_hook_payload` reads `tool_input.command` only to set
`tool.args_digest` (`hyodo/connect.py`). The string is not kept, is not
a path, and is not matched against globs. A policy cannot express
"deny `rm -rf`" inside HyoDo; that is the host's job (Claude
`permissions`, a matcher more specific than `*`, or a wrapper around
the shell).

The connect tests feed `"command": "rm -rf /"` as a Bash payload
(`tests/test_connect.py`). HyoDo still only sees a digest plus
`tool.name == "Bash"`.

## Missing URL shape is not `ALLOW`

`WebSearch` and `WebFetch` are built-in web tools
(`hyodo/policy.py` `_BUILTIN_WEB_TOOLS` / `_is_web_classified`). The
mapper copies `tool_input.url` into `tool.urls` (domain + path/query).
It does not copy `query`, and it never sets `tool.method`.

When `[web]` is configured:

- no `tool.urls`, or a URL entry with an empty domain, or `tool.method`
  is `None` → `UNOBSERVED`, `rule_id` `web_boundary_undeclared`
  (`hyodo/policy.py` `evaluate_policy`)
- `web_domain_unlisted:<domain>` is appended only after a non-empty
  domain string is present. An unlisted-domain rule cannot fire on a
  search that never declared a URL.

When `[web]` is **not** configured (the starter policy from `connect`
does not include it), a `WebSearch` / `WebFetch` call is still not
`ALLOW`: it is an `ask_tools:<name>` external variable and evaluates to
`ASK` at the default trust level. Missing URL shape is unobserved
coverage, not a green light.

A mapped URL whose `urlsplit` netloc is empty fails event validation
(`hyodo/events.py` `validate_event` requires a non-empty `domain`) and
`policy check --hook claude-code` exits 2 as `UNOBSERVED`, not 0.

## `blocked_path_globs` only sees mapped `file_path`

The mapper copies these `tool_input` keys, and no others:

| `tool_input` key | Mapped to | Typical Claude tools |
| --- | --- | --- |
| `file_path` | `tool.paths` | `Read`, `Write`, `Edit` |
| `url` | `tool.urls` | `WebFetch` |
| `command` | `tool.args_digest` only | `Bash` |

A remaining-gap inventory listed `path` next to `file_path`. That is
**false on current main**: `map_claude_code_hook_payload` does not read
`path`, `glob`, `pattern`, `notebook_path`, `cell_id`, or `query`.
`validate_event` then defaults missing `tool.paths` to `[]`
(`hyodo/events.py`).

`blocked_path_globs` runs only when `tool.paths` is a non-empty list
(`hyodo/policy.py` `evaluate_policy`). Empty paths skip the glob. The
default is therefore `ALLOW` on a name-allowed tool that never declared
a path — including `Bash`, `Glob`/`Grep` with only `pattern`, and
`NotebookEdit` with `cell_id`. `WebSearch` is not in that set: it is a
built-in web tool, so missing URL shape is `ASK` (no `[web]`) or
`UNOBSERVED` (with `[web]`), never `ALLOW`.

Opt-in `require_declared_paths = true` turns that silence into
`UNOBSERVED` (`rule_id` `data_boundary_undeclared`) instead of `ALLOW`.
It is off by default so legitimate no-path tools are not all flagged
(`hyodo/policy.py` `PolicyConfig.require_declared_paths`).

## Already true on this path

Do not re-open these as if they were still missing:

- Bare CLI exits 0/1/2/3 are remapped to Claude PreToolUse 0/2 on
  `--hook claude-code` (`hyodo/cli/main.py`). Forwarding raw
  `exit $?` is still wrong for a *custom* hook that does not use that
  flag.
- `step_index` is `count_run_events(root, session_id)`, not a payload
  field (`hyodo/connect.py` `map_claude_code_hook_payload`). `max_steps`
  is not inert on the shipped hook path.
