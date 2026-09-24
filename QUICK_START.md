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
machine-readable output. With no path it scans your uncommitted changes; a
clean checkout has nothing to scan and reports `UNOBSERVED` (exit **2** under
`--strict`), never `PASS`. In CI, where the checkout is clean, pass the tree:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe . --strict --max-files 0 --json
```

## Run existing project checks

```bash
hyodo init
hyodo check
```

`init` detects supported test and lint tools. When it finds supported tooling,
it writes `.hyodo/gates.toml`; with zero detections it writes
`.hyodo/gates.toml.example` instead, creates no live gates file, and `check`
keeps the built-in sampled fallback. Review and commit a live gates file with
your team policy. An existing config is left alone unless `--force` is given.
No detected tools means no invented passing gate; `check` exits **2** when no
executable gates run, **1** when a gate fails, and **0** only when at least one
gate ran and all passed. See the
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
