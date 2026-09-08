# Remaining gaps (do not merge as “fixed”)

Written so another reader can see what the review still finds thin.
Nothing here is a merge checklist. By-design limits and unfinished work
are listed separately so they are not argued as the same class.

Related: [ADOPTION.md](./ADOPTION.md), [POLICY_SYNTAX.md](./POLICY_SYNTAX.md),
[CONNECT.md](./CONNECT.md), [POLICY_TRUST.md](./POLICY_TRUST.md).
PR: do-not-merge visibility branch.

## A. By design — do not “fix” by becoming a sandbox

1. HyoDo is not a process interceptor. An agent that never calls
   `policy check` / `event record` is unconstrained.
2. DENY is a signal. The caller stops the tool. Claude Code is covered
   only after `hyodo connect claude-code --write`.
3. Integrity Score / six-virtue labels are review signals, never merge
   authority.
4. Default ledger is digest-only. Missing events cannot be denied later.
5. `hyodo safe` is early-warning pattern scan, not an audit.
6. Public MCP is loopback or authenticated Tailscale only.
7. `connect cursor` and `connect codex` stay UNOBSERVED until a verified
   hook contract exists. That is honesty, not a stub to fake.

## B. Easy to misread as stronger than it is

8. Fail-closed on *missing* policy (exit 2) is not fail-closed on a
   *wide* allowlist. A policy that lists every tool is measured ALLOW.
9. CI `hyodo check` does not see a session `.env` read that never landed
   in a commit.
10. One observed Claude session does not cover Cursor, Codex, ChatGPT, or
    `mcp.hyodo.app`.
11. Shadow mode never blocks — including missing policy and unmappable
    payload. The ledger is honest; the session is not gated.
12. Starter `.hyodo/policy.toml` from `connect` is permissive except a
    small `blocked_path_globs` list. First-run “quality gate” is thin.
13. Trust lives in untracked `.hyodo/policy-trust.json`. Teammates do not
    inherit a grant. The tracked file is only a ceiling.
14. Level 2+ without a visible ledger is UNOBSERVED. Autorun is not
    “trusted because max_level says so.”

## C. Contract mismatches other implementers will hit

15. Bare CLI: 0 ALLOW / 1 DENY / 2 UNOBSERVED / 3 ASK.
    Claude PreToolUse: exit **1 is non-blocking**. Forwarding `exit $?`
    lets DENY through. The shipped `--hook claude-code` remaps to 0/2.
16. Official Claude JSON `permissionDecision` (`allow`/`deny`/`ask`/`defer`)
    is richer than what HyoDo emits. ASK is forced to hook exit 2.
    Custom hooks that emit JSON `ask` are outside the shipped path.
17. Claude has ignored hook deny on some Task / Bash / Edit / MCP paths
    (upstream). Overlap `permissions.deny`; do not treat the hook as a
    security boundary.
18. `allowed_tools` is exact `tool.name`. Demo names (`search`) are not
    Claude (`Read`, `Bash`) or Cursor (`read_file` / `Read` depending on
    version). A dual-host policy must list both families.
19. No `Bash(rm *)` argument matcher. Command body is the host’s job.
20. `WebSearch` may carry no domain. Unlisted-domain rules may not fire;
    treat missing URL shape as unobserved, not ALLOW.
21. Hook mapping covers `file_path` / `path` / `url`. Other Claude keys
    (`command` only, notebook `cell_id`, glob patterns) may leave
    `tool.paths` empty, so `blocked_path_globs` never runs.
22. If the hook always sends `step_index: 0`, `max_steps` is dead.
23. Matcher strings are case-sensitive (`Bash` ≠ `bash`).

## D. Product surface still uneven

24. Version story drifts: PyPI/`VERSION` is 4.16.x; `install_interactive.sh`
    and some root scripts still speak v3.1.0; `ROADMAP.md` still sells
    Q1 2026 “Five Tiger Generals / ultrawork” that the public CLI does
    not ship. Readers cannot tell which file is current.
25. `ANTHROPIC_PROOF.md` still says there is no Claude-only path.
    `hyodo connect claude-code` is a Claude-only wiring path.
26. `hyodo/graph_view.py` file-tool patterns still include demo names
    (`read_file`, `write_file`, `edit`) and may miss `Read` / `Write`.
27. `gates.toml` schema is generated, not specified in a public field
    table the way `policy.toml` now is.
28. hyodo.app site pages (`connect`, `trust`, `why-hyodo`, `quickstart`)
    were not all updated on the first visibility commits.
29. Own-repo `.gitignore` ignores all of `.hyodo/`. Customer guidance
    must say the opposite split: track `policy.toml` + `gates.toml`,
    ignore `policy-trust.json` + `agent-events.jsonl`.
30. Tests still pin demo allowlists (`search`, `read_file`). Easy to
    “fix” examples and break CI or leave examples lying again.
31. No public Cursor/Codex adapter. Documented UNOBSERVED is correct;
    operators still have no official file to copy.
32. Remote MCP (`mcp.hyodo.app` / ChatGPT connector) remains unverified
    in-repo. Do not list it next to `hyodo mcp stdio` as equivalent.
33. `--full-body` exists. Default digest-only is the honest mode;
    full-body retention is a policy decision the docs mention but do
    not operationalize (retention, redaction, who may enable it).
34. Social proof is thin (public star count, issue history). That is not
    a code defect; claims pages should not imply a large installed base.

## E. What another implementer should do first

Not “build a sandbox.” In order:

1. Keep PR #203 unmerged until a human marks which of A–D are work.
2. Finish in-tree pointers: README, CONNECT, CHANGELOG Unreleased,
   starter-policy comments, site pages.
3. Add a `step_index` counter to the Claude hook path or document that
   `max_steps` is inert without one.
4. Publish a `gates.toml` field table next to POLICY_SYNTAX.
5. Either implement Cursor with a real captured payload fixture, or
   delete aspirational Cursor copy from marketing pages.
6. Collapse version narrative to one number everywhere readers look
   (`VERSION`, README badge, install scripts, ROADMAP “current”).

## F. Out of scope for this repo

- Claude/Cursor hook enforcement bugs.
- Making Integrity Score an approver.
- Fabricating a Cursor hook schema.
- Treating unobserved hosts as covered because Claude was wired.
