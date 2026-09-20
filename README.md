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

## 30-second start

```bash
pipx install hyodo
cd your-project
hyodo safe --strict
hyodo init
hyodo check
```

`safe` works immediately in any repository. `init` is optional: it detects
tools you already use and writes `.hyodo/gates.toml`; `check` then runs those
gates. No detected tooling means no invented green check. See
[`docs/GATES_SYNTAX.md`](./docs/GATES_SYNTAX.md) for every `gates.toml` field.

Commit `.hyodo/gates.toml` and `.hyodo/policy.toml` (team-shared policy); keep
the rest of `.hyodo/` out of version control — see
[what to commit](docs/CONNECT.md#what-to-commit) for the `.gitignore` split.

## What it does

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
