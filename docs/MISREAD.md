# Easy to misread

HyoDo is not a runtime sandbox. These remaining honesty gaps are easy to
over-read as stronger than what the code measures. A DENY still has to be
enforced by the caller. Where a longer doc already states the contract,
this page only points at it. Host-side mapper limits (what `tool_input`
keys become `tool.paths` / `tool.urls`) are in
[`HOST_CONTRACT.md`](./HOST_CONTRACT.md).

## Missing policy is fail-closed; a wide allowlist is not

A missing or invalid `.hyodo/policy.toml` is `UNOBSERVED` (exit 2) —
`hyodo/policy.py::try_load_policy`. The reason is `policy_missing` when
the file is absent and `policy_invalid` when the TOML does not parse.
That is not deny-by-default once a policy exists.

`allowed_tools` is an exact-name allowlist. Unset means no tool
restriction. A name on the list is measured `ALLOW` (blocked-path and
trust rules still apply). Listing every tool the host uses is a measured
allowlist, not a fail-closed gate.

## CI `hyodo check` does not see a session `.env` read

`hyodo check` runs quality gates on the checkout (BYOG, the HyoDo preset,
or `--general`). It does not replay agent tool calls. A session read of
`.env` that never landed in a commit is not in the CI tree; the local
ledger (`.hyodo/agent-events.jsonl`) is untracked. Session policy is
`hyodo policy check` / `hyodo event record`, not `hyodo check`.

## One observed Claude session is not other hosts

Already covered: [`docs/CONNECT.md`](./CONNECT.md) (`cursor` / `codex`
hooks stay `UNOBSERVED`), [`docs/ONBOARDING.md`](./ONBOARDING.md)
(ChatGPT always `UNOBSERVED`),
[`docs/M5_REMOTE_CONNECTOR_CONTRACT.md`](./M5_REMOTE_CONNECTOR_CONTRACT.md)
(`https://mcp.hyodo.app/mcp` is not live). One Claude Code hook session
reaching `OBSERVED` does not cover Cursor, Codex, ChatGPT, or
mcp.hyodo.app.

## Shadow mode never blocks

Already covered: [`docs/CONNECT.md`](./CONNECT.md#shadow-mode). Shadow
still evaluates and records (`policy.shadow: true`); the session is not
gated. Missing policy and unmappable payload stay non-blocking under
`--shadow`.

## Starter `policy.toml` is permissive

`hyodo connect claude-code` writes a starter only when the file is
absent (`hyodo/connect.py::build_starter_policy`). `allowed_tools` and
`max_steps` are commented out. The only live restriction is
`blocked_path_globs`: `.env`, `*.pem`, `id_rsa*`, `.hyodo/**`.

## Trust grants are local and untracked

Already covered: [`docs/POLICY_TRUST.md`](./POLICY_TRUST.md) and
[`docs/CONNECT.md`](./CONNECT.md#what-to-commit). Grants live in
untracked `.hyodo/policy-trust.json`. Teammates do not inherit a grant.
Tracked `[trust] max_level` is a ceiling only.

## Level 2+ without a visible ledger is `UNOBSERVED`

Already covered: [`docs/POLICY_TRUST.md`](./POLICY_TRUST.md). Autorun is
not "trusted because `max_level` says so." Level 2+ with external
variables and no observed ledger is `UNOBSERVED`
(`autorun_level2` / `autorun_level3`). A missing or damaged grant file
is `trust_grant_unobserved`.
