# HyoDo Quick Start

Add local guardrails to an existing project without replacing its tests,
linters, or CI. HyoDo supports Python 3.10+.

## Install and scan

```bash
pipx install hyodo
cd your-project
hyodo safe --strict
```

`safe` is an early-warning scan, not a full security audit. Use `--json` for
machine-readable output. In CI, install HyoDo and run the same command:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

## Run existing project checks

```bash
hyodo init
hyodo check
```

`init` detects supported test and lint tools and writes `.hyodo/gates.toml`.
Review and commit that file with your team policy. An existing config is left
alone unless `--force` is given. No detected tools means no invented passing
gate; `check` exits **2** when no executable gates run, **1** when a gate fails,
and **0** only when at least one gate ran and all passed. See the
[gate configuration reference](./docs/GATES_SYNTAX.md).

## Optional integrations

For agent event and policy checks:

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
```

Events are digest-only by default. A DENY result is evidence; the caller must
stop the agent. For an evidence panel, run `hyodo dashboard --open`. To connect
an MCP host, install `pip install 'hyodo[mcp]'` and follow the
[host onboarding guide](./docs/ONBOARDING.md). Host support and remote connector
status are documented there; remote ChatGPT MCP remains contract-only.

## Command outcomes

| Command | Exit contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `init` | `0` config written · `1` config exists without `--force` |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event` / `policy` | `0` valid · `1` invalid · `2` unobserved · `3` ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

Missing or unmeasured evidence is never a healthy result. Scores are review
signals, not approval. See the [product boundaries](./docs/PRODUCT_BOUNDARY.md)
and [security model](./SECURITY.md).

## Next steps

- [Product overview](./README.md)
- [Docs index](./docs/README.md)
- [Contributing and full verification](./CONTRIBUTING.md)
- [Release history](./CHANGELOG.md)
