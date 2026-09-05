# HyoDo

**Honest local guardrails for AI-assisted development.**

HyoDo is a model-agnostic Python CLI that helps teams prove which checks ran,
record agent actions, enforce local tool and path policy, and reuse existing
tests and linters without turning missing evidence into a green result.

Review signals never grant automatic approval. Unobserved is never green.

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://github.com/lofibrainwav/HyoDo/blob/main/LICENSE)](./LICENSE)

## Why HyoDo exists

AI coding tools can move quickly, but a normal green check does not always answer:

- Did the check actually run?
- Did the agent touch only approved tools and paths?
- Was missing or unreadable evidence treated as a pass?
- Can the project keep using its existing pytest, Ruff, npm, Go, or Rust checks?

HyoDo makes those boundaries explicit with local evidence, policy decisions,
and fail-closed exit contracts.

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
gates. No detected tooling means no invented green check.

## What it does

| Need | HyoDo surface |
| --- | --- |
| Early-warning safety scan | `hyodo safe` |
| Reuse existing project checks | `hyodo init` → `hyodo check` |
| Agent action audit trail | `hyodo event record` |
| Tool / path / step policy | `hyodo policy check` |
| Schema / eval / evidence report | `hyodo schema`, `eval`, `report` |
| Local evidence panel | `hyodo dashboard --open` |
| Optional MCP adapter | `hyodo mcp stdio` / `serve` |
| MCP diagnostics and audit | `hyodo mcp doctor`, `access-log`, `rules` |

## Honest boundaries

HyoDo is deliberately narrow:

- It is **not** a runtime sandbox or process interceptor.
- `hyodo safe` is an early-warning scanner, not a full security audit.
- A DENY result must still be enforced by the caller.
- HYOGOOK V5 is a review signal, never an automatic approval decision.
- The public MCP server supports loopback or authenticated Tailscale binding;
  public `0.0.0.0` listeners are not supported.
- Missing, unreadable, or unmeasured evidence is never reported as healthy.

That scope is intentional: the tool should be useful locally without requiring
a hosted service, model provider, or remote control plane.

## Use your existing CI

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

The bundled composite action installs a pinned hyodo and runs `hyodo check`.
Set `upload-sarif: "true"` with `security-events: write` for Security tab upload:

```yaml
- uses: lofibrainwav/HyoDo/.github/actions/hyodo@v4.11.0
```

For project-specific gates:

```bash
hyodo init
hyodo check
```

`init` can absorb pytest, Ruff, mypy, Pyright, npm scripts, Go, Cargo, and
Makefile targets. Empty or malformed gate configuration exits **2**, not **0**.

## Hooks and SARIF

Add the pre-commit hooks from `.pre-commit-hooks.yaml`:

```yaml
- repo: https://github.com/lofibrainwav/HyoDo
  rev: v4.11.0
  hooks: [{id: hyodo-check}, {id: hyodo-safe-strict}]
```

`hyodo report --format sarif` writes a SARIF 2.1.0 report for
`github/codeql-action/upload-sarif`; unmeasured evidence is never reported as
an empty alert set.

## Optional agent evidence

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
hyodo schema check --schema agent.schema.json --payload step.json --json
```

Default event storage is digest-only. See
[`examples/fde-evidence-spine/`](./examples/fde-evidence-spine/) for a complete
example.

## Optional MCP

Local stdio:

```bash
pip install 'hyodo[mcp]'
hyodo mcp stdio --root .
```

Private-network connector:

```bash
hyodo mcp serve --bind tailscale --bind-ip 100.99.88.77 \
  --token "$HYODO_MCP_TOKEN" --root .
```

The MCP adapter uses the same CLI contracts rather than creating a second
policy engine. MCP SDK v1 and v2 are both exercised in CI.

## Exit contracts

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event` / `policy` | `0` valid/ALLOW · `1` invalid/DENY · `2` unobserved |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

## Engineering model

HyoDo's internal review model maps six evidence areas:

| Area | Pillar | Measured by |
| --- | --- | --- |
| Static types | Truth (眞 / 진) | Command gate |
| Tests + safety | Goodness (善 / 선) | Tests + `safe` |
| Lint / format | Beauty (美 / 미) | Command gate |
| Public surface | Benevolence (仁 / 인) | Native AST scan |
| Data privacy | Hyo (孝 / 효) | Native consent/data scan |
| Audit trail | Yeong (永 / 영) | Local ledger |

Command gates can be absorbed from existing tooling. Native evidence pillars
cannot be shell-faked through `gates.toml`. See
[`PHILOSOPHY.md`](./PHILOSOPHY.md) for the HYOGOOK V5 review model.

## Install and support

Python **3.10+**: `pipx install hyodo` or `pip install -U hyodo`.

- Quick start: [`QUICK_START.md`](./QUICK_START.md)
- Security: [`SECURITY.md`](./SECURITY.md); Issues: [GitHub Issues](https://github.com/lofibrainwav/HyoDo/issues)
- Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Changelog: [`CHANGELOG.md`](./CHANGELOG.md)

## License

MIT. See [`LICENSE`](./LICENSE).
