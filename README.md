# HyoDo

**Honest local guardrails for AI-assisted development.**

HyoDo is a model-agnostic Python CLI that helps teams prove which checks ran,
record agent actions, enforce local tool and path policy, and reuse existing
tests and linters without turning missing evidence into a green result.
Review signals never grant automatic approval. Unobserved is never green.

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://img.shields.io/github/license/lofibrainwav/HyoDo)](./LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/lofibrainwav/HyoDo/badge)](https://scorecard.dev/viewer/?uri=github.com/lofibrainwav/HyoDo)

## Why HyoDo exists

AI coding tools can move quickly, but a normal green check does not always answer:

- Did the check actually run?
- Did the agent touch only approved tools and paths?
- Was missing or unreadable evidence treated as a pass?

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
| Agent action audit trail | `hyodo event record` |
| Tool / path / step policy | `hyodo policy check` |
| Schema / eval / evidence report | `hyodo schema`, `eval`, `report` |
| Local evidence panel | `hyodo dashboard --open` |
| Optional MCP adapter | `hyodo mcp stdio` / `serve` |
| MCP diagnostics and audit | `hyodo mcp doctor`, `access-log`, `rules` |
| Onboarding, harness and host wiring | `hyodo start`, `connect`, `mcp config` |
| Lens, absorption, graph, eye | `hyodo skills`, `inspect`, `graph`, `eye` |
| Reader vocabulary, host continuity | `--audience`, `hyodo mcp continuity` |

## Honest boundaries

HyoDo is deliberately narrow:

- It is **not** a runtime sandbox or process interceptor.
- `hyodo safe` is an early-warning scanner, not a full security audit.
- A DENY result must still be enforced by the caller.
- HyoDo Integrity Score: advisory only, never approval; HYOGOOK V5 lineage.
- The public MCP server supports loopback or authenticated Tailscale binding;
  public `0.0.0.0` listeners are not supported.
- Missing, unreadable, or unmeasured evidence is never reported as healthy.
- Embeddings, model calls, capture tools, and remote inventories stay outside
  the package: HyoDo keeps digests, hashes, and receipts, never the payload.

## Use your existing CI

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install hyodo
- run: hyodo safe --strict --json
```

The composite action installs HyoDo from its pinned ref. Pin a signed release
that contains it (not `v4.11.0`); SARIF upload needs `security-events: write`.

```yaml
- uses: lofibrainwav/HyoDo/.github/actions/hyodo@vX.Y.Z
```

For project-specific gates:

```bash
hyodo init
hyodo check
```

`init` can absorb pytest, Ruff, mypy, Pyright, npm scripts, Go, Cargo, and
Makefile targets. Empty or malformed gate configuration exits **2**, not **0**.

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
[`examples/fde-evidence-spine/`](./examples/fde-evidence-spine/) for a complete
example. Policy trust levels are documented in [docs/POLICY_TRUST.md](docs/POLICY_TRUST.md).

## Optional MCP

```bash
pip install 'hyodo[mcp]'
hyodo mcp stdio --root .                       # local stdio
hyodo mcp serve --bind tailscale --bind-ip 100.99.88.77 \
  --token "$HYODO_MCP_TOKEN" --root .          # private-network connector
```

The MCP adapter uses the same CLI contracts rather than creating a second
policy engine. MCP SDK v1 and v2 are both exercised in CI.

## Exit contracts

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event`, `policy` | 0 valid/ALLOW; 1 invalid/DENY; 2 unobserved; 3 ASK |
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
cannot be shell-faked through `gates.toml`; see
[`PHILOSOPHY.md`](./PHILOSOPHY.md) for score naming and formula lineage.

## Install and support

Python **3.10+**: `pipx install hyodo` or `pip install -U hyodo`.

- Quick start: [`QUICK_START.md`](./QUICK_START.md); Node.js: [`docs/onboarding-nodejs.md`](./docs/onboarding-nodejs.md)
- Security: [`SECURITY.md`](./SECURITY.md); Issues: [GitHub Issues](https://github.com/lofibrainwav/HyoDo/issues)
- Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md); Changelog: [`CHANGELOG.md`](./CHANGELOG.md)

## License

MIT. See [`LICENSE`](./LICENSE).
