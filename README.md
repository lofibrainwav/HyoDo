# HyoDo

**Local evidence verification for AI-assisted work. See what ran, what the
evidence supports, and what remains unknown.**

HyoDo is an open-source Python tool that runs on your computer. It reuses the
tests and linters your project already has, reports their results, and marks
missing evidence `UNOBSERVED`. That means there is not enough evidence to say
whether a check passed or failed. HyoDo helps people review work. HyoDo does
not run or authorize agents. It does not approve merges or deployments.

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://img.shields.io/github/license/lofibrainwav/HyoDo)](./LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/lofibrainwav/HyoDo/badge)](https://scorecard.dev/viewer/?uri=github.com/lofibrainwav/HyoDo)

## What changes when you use HyoDo

A normal green CI summary can tell you that something passed. It does not
always tell you what never ran. HyoDo keeps those cases separate instead of
turning missing evidence green.

Conceptually, if tests and lint ran but no security gate was observed:

| What happened | What HyoDo means |
| --- | --- |
| Tests ran and passed | Evidence supports `PASS` |
| Lint ran and passed | Evidence supports `PASS` |
| No security gate ran | Evidence remains `UNOBSERVED` |

`UNOBSERVED` means HyoDo does not have enough evidence to call the result a
pass or a failure. That distinction is the product: show what was actually
observed, then leave the decision to a person.

## Why HyoDo exists

HyoDo helps you inspect AI-assisted work: which project checks ran, what they
found, and what remains unknown. Its guiding idea, Hyo (孝), is that technology
should respect people's time and choices, and carry its share of the burden
instead of passing it back to them. HyoDo records evidence; people decide what
to do with it.

AI coding tools can move quickly, but a normal green check does not always
answer:

- Did the check actually run?
- Did the agent touch only approved tools and paths?
- Was missing or unreadable evidence treated as a pass?

HyoDo makes those boundaries explicit with local evidence, policy-evaluation
results, and fail-closed verification status.

## First 10 minutes

The canonical first-use path is one command after installation:

```bash
pipx install hyodo
cd your-project
hyodo start
```

`hyodo start` shows the workspace and detected hosts, asks at most three
questions, previews every write, and changes nothing without an explicit yes.
Host connection is optional; you can skip it and use HyoDo only as a local
verification tool.

Prefer direct commands instead?

```bash
hyodo safe --strict
hyodo init
hyodo check
hyodo dashboard --open
```

`safe` works immediately. `init` detects supported project checks and writes
`.hyodo/gates.toml`; `check` runs those gates. The first interactive `check`
may ask you to approve the exact detected commands before HyoDo executes them.
If that command set changes, approval is required again. In non-interactive
contexts an unseen command set is not silently executed or reported as green.
No detected tooling means no invented passing gate. See
[`docs/GATES_SYNTAX.md`](./docs/GATES_SYNTAX.md) for the full contract.

`hyodo init` does not create `.hyodo/policy.toml`. That file appears only when
you configure agent policy (for example, when `hyodo connect claude-code
--write` creates a starter policy because none exists) or when you author one
yourself. Commit `.hyodo/gates.toml`, and commit `.hyodo/policy.toml` if your
team uses it; keep generated runtime evidence out of version control. See
[what to commit](docs/CONNECT.md#what-to-commit) for the exact split.

If local verification is all you need, you can stop here. Hooks, agent policy,
and MCP are optional integrations.

## Go deeper only when you need it

| Need | HyoDo surface |
| --- | --- |
| Early-warning safety scan | `hyodo safe` |
| Reuse existing project checks | `hyodo init` → `hyodo check` |
| Local agent evidence log | `hyodo event record` |
| Tool / path / step policy | `hyodo policy check` |
| Schema / eval / evidence report | `hyodo schema`, `eval`, `report` |
| Local evidence panel | `hyodo dashboard --open` |
| Optional MCP adapter | `hyodo mcp stdio` / `serve` |

## Boundaries and current status

HyoDo provides local checks and evidence contracts; it does not grant execution
authority or turn missing evidence into a pass. `hyodo safe` is an early-warning
scan, not a full security audit, and callers must enforce DENY decisions. By
default, HyoDo stores evidence digests and receipts; raw prompt and tool bodies
are retained only when an operator explicitly opts into full-body storage. See the
[product boundary](./docs/PRODUCT_BOUNDARY.md), [measured state snapshot](./docs/CURRENT_STATE.md),
and [security model](./SECURITY.md) for the authoritative details.
The legacy HyoDo Integrity Score command is advisory only. It retains a
five-input geometric-mean method for compatibility.
HyoDo's replacement evaluation model is being updated; it does not define the
six reference values as one canonical score. The current package does not yet
provide a general per-axis evaluator. Current source status may differ from
the latest published package.

## Use your existing CI

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

```yaml
- uses: lofibrainwav/HyoDo/.github/actions/hyodo@vX.Y.Z
```

`init` detects existing test and lint tooling. Empty or malformed gate
configuration exits **2**, not **0**. See the [gate configuration reference](./docs/GATES_SYNTAX.md).

## Hooks and SARIF

Pin a signed release containing the hooks (`v4.11.0` predates them):

```yaml
- repo: https://github.com/lofibrainwav/HyoDo
  rev: vX.Y.Z
  hooks: [{id: hyodo-check}, {id: hyodo-safe-strict}]
```

`hyodo report --format sarif` writes a SARIF 2.1.0 visibility report.
Measured DENY and unreadable-ledger conditions become alerts; `hyodo check`
remains the fail-closed gate for missing or unmeasured quality evidence.

## Optional agent evidence

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
hyodo schema check --schema agent.schema.json --payload step.json --json
```

Default event storage is digest-only. See
[`examples/fde-evidence-spine/`](./examples/fde-evidence-spine/) for a demo
event and [`examples/host-policies/`](./examples/host-policies/) for a
dual-host `allowed_tools` list (not a Cursor hook). Policy trust:
[docs/POLICY_TRUST.md](docs/POLICY_TRUST.md). For an unattended feature queue
that calls these gates from a host loop, see
[`examples/factory-loop/`](./examples/factory-loop/).

## Optional MCP

```bash
pip install 'hyodo[mcp]'                       # pipx: pipx install --force 'hyodo[mcp]'
hyodo mcp stdio --root .                       # local stdio
hyodo mcp serve --bind tailscale --bind-ip 100.99.88.77 \
  --token "$HYODO_MCP_TOKEN" --root .          # private-network connector
```

The extra has to land in the same environment that runs `hyodo`; a pipx
install is isolated, so `pip install 'hyodo[mcp]'` after `pipx install hyodo`
installs into a different interpreter and the SDK stays missing.

The MCP adapter uses the same CLI contracts rather than a second engine. It is
not an MCP gateway, traffic proxy, or central authorization layer, and
`mcp.hyodo.app` is contract-only, not this path.

## Install and support

Python **3.10+**: `pipx install hyodo` or `pip install -U hyodo`.

- Docs index: [`docs/README.md`](./docs/README.md)
- Command contracts and first-run steps: [`QUICK_START.md`](./QUICK_START.md)
- Node.js: [`docs/onboarding-nodejs.md`](./docs/onboarding-nodejs.md)
- Security: [`SECURITY.md`](./SECURITY.md);
  Issues: [GitHub Issues](https://github.com/lofibrainwav/HyoDo/issues)
- Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md);
  Changelog: [`CHANGELOG.md`](./CHANGELOG.md)

## License

MIT. See [`LICENSE`](./LICENSE).
