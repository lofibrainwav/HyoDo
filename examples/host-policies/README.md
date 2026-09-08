# Host `allowed_tools` copy files

`allowed_tools` matches `tool.name` exactly and is case-sensitive. Demo
names (`search`, `read_file`) are not Claude Code names (`Read`, `Bash`).
A policy that lists only one family will DENY the other.

This directory is that copy file. It is **not** a hook adapter.

- `hyodo connect claude-code` writes Claude Code hooks. That path is real.
- `hyodo connect cursor` and `hyodo connect codex` stay **UNOBSERVED**.
  HyoDo does not ship a Cursor or Codex hook contract. Do not treat this
  TOML as proof those hosts are gated.
- `hyodo mcp config cursor` writes MCP server config. That is a different
  surface from policy hooks.

Copy [`claude-and-cursor.policy.toml`](./claude-and-cursor.policy.toml) to
`.hyodo/policy.toml` and trim the list to the hosts you actually run.
The demo event under `examples/fde-evidence-spine/` still uses placeholder
names on purpose — tests pin those; do not "fix" them into Claude names.
