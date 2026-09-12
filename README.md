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

AI coding tools can move quickly, but a normal green check does not always
answer:

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

## Current public claim lock

This table is the latest **published-package** boundary. It does not describe
unreleased `main` work. For current source and measured-state readback, see
[`docs/CURRENT_STATE.md`](./docs/CURRENT_STATE.md).

| Capability | Status | Evidence boundary |
| --- | --- | --- |
| gates / ledger / friction preview | SHIPPED | Local preview/export; ledger. |
| Graph v1 | SHIPPED (site DEMO FIXTURE) | Local dashboard; fixed demo site. |
| Graph v2 join | SHIPPED | Multi-parent runtime/viewer with v1 compatibility; public site remains fixture-only. |
| Codex host adapter | SHIPPED / LIVE UNOBSERVED | Native adapter shipped; a fresh canonical live canary is separate evidence. |
| Cursor host adapter | SHIPPED / LIVE UNOBSERVED | Native adapter shipped; fresh live host observation is not yet sealed. |
| IFA v0 | SHIPPED | Observer-only information-flow attestation; never execution authority. |
| remote MCP / ChatGPT | CONTRACT ONLY | Hosted contract; runtime unobserved. |
| ACL runtime / Wisdom Reflex | RESEARCH | Hypothesis; no automatic router. |
| friction collector | NOT BUILT | No collector/uploader; transport disabled. |

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

```yaml
- uses: lofibrainwav/HyoDo/.github/actions/hyodo@vX.Y.Z
```

```bash
hyodo init && hyodo check
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
[`examples/fde-evidence-spine/`](./examples/fde-evidence-spine/) for a demo
event and [`examples/host-policies/`](./examples/host-policies/) for a
dual-host `allowed_tools` list (not a Cursor hook). Policy trust:
[docs/POLICY_TRUST.md](docs/POLICY_TRUST.md).

## Optional MCP

```bash
pip install 'hyodo[mcp]'
hyodo mcp stdio --root .                       # local stdio
hyodo mcp serve --bind tailscale --bind-ip 100.99.88.77 \
  --token "$HYODO_MCP_TOKEN" --root .          # private-network connector
```

The MCP adapter uses the same CLI contracts rather than a second engine.
SDK v1/v2 are in CI. `mcp.hyodo.app` is contract-only, not this path.

## Exit contracts

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event`, `policy` | 0 valid/ALLOW; 1 invalid/DENY; 2 unobserved; 3 ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

## Install and support

Python **3.10+**: `pipx install hyodo` or `pip install -U hyodo`.

- Docs index: [`docs/README.md`](./docs/README.md)
- Quick start: [`QUICK_START.md`](./QUICK_START.md)
- Node.js: [`docs/onboarding-nodejs.md`](./docs/onboarding-nodejs.md)
- Security: [`SECURITY.md`](./SECURITY.md);
  Issues: [GitHub Issues](https://github.com/lofibrainwav/HyoDo/issues)
- Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md);
  Changelog: [`CHANGELOG.md`](./CHANGELOG.md)

## License

MIT. See [`LICENSE`](./LICENSE).
