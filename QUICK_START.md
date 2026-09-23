# HyoDo Quick Start

Add local guardrails to an existing project without replacing its tests,
linters, or CI. HyoDo supports Python 3.10+.

## Start here

```bash
pipx install hyodo
cd your-project
hyodo start
```

`hyodo start` is the canonical first-use path. It shows the current workspace
and detected hosts, previews every write, and changes nothing without an
explicit yes. You can skip host connection and keep using HyoDo only for local
verification.

Prefer direct commands?

```bash
hyodo safe --strict
hyodo init
hyodo check
hyodo dashboard --open
```

`safe` is an early-warning scan, not a full security audit. `init` detects
supported test and lint tools and writes `.hyodo/gates.toml`. The first
interactive `check` may ask you to approve the exact detected commands before
running them; a changed command set requires approval again. In CI or another
non-interactive context, an unseen command set is not executed and cannot turn
into a passing result by omission.

Review and commit `.hyodo/gates.toml`. `hyodo init` does not create
`.hyodo/policy.toml`; that file is created only when you configure agent policy
(for example with `hyodo connect claude-code --write`) or author one yourself.
No detected tools means no invented passing gate; `check` exits **2** when no
executable gates run, **1** when a gate fails, and **0** only when at least one
gate ran and all passed. See the
[gate configuration reference](./docs/GATES_SYNTAX.md).

For CI, install HyoDo and run the same safety scan:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

## Optional integrations

Stop after `safe`, `check`, and the dashboard if that is all you need. The
surfaces below are optional and are intended for teams that also want agent
policy, host hooks, or MCP integration.

For agent event and policy checks:

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
```

Events are digest-only by default. A DENY result is evidence; the caller must
stop the agent. For an evidence panel, run `hyodo dashboard --open`. To connect
an MCP host, install the optional extra **into the same environment that runs
`hyodo`** — `pipx install --force 'hyodo[mcp]'` if you installed with pipx,
`pip install 'hyodo[mcp]'` if you installed with pip — and follow the
[host onboarding guide](./docs/ONBOARDING.md). Host support and remote connector
status are documented there; remote ChatGPT MCP remains contract-only.

## Command outcomes

| Command | Exit contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `init` | `0` config written · `1` config exists without `--force` |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event validate` | `0` valid · `1` invalid · `2` unreadable input |
| Policy result | `0` ALLOW · `1` DENY · `2` UNOBSERVED · `3` ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

`UNOBSERVED` means there is not enough evidence to say whether a check passed
or failed. It is neither a pass nor a failure.
Policy results come from `event record --policy` and `policy check`; an invalid
event can stop before policy evaluation.

Missing or unmeasured evidence is never a healthy result. Scores are review
signals, not approval. See the [product boundaries](./docs/PRODUCT_BOUNDARY.md)
and [security model](./SECURITY.md).

## Next steps

- [Product overview](./README.md)
- [Docs index](./docs/README.md)
- [Contributing and full verification](./CONTRIBUTING.md)
- [Release history](./CHANGELOG.md)
