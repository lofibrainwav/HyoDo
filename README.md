# HyoDo

**Local AI agent guardrails for FDE work and CI — audit evidence,
policy DENY, fail-closed quality gates.**

Not a pre-commit clone. HyoDo helps Forward Deployed Engineers and
AI-assisted teams **prove what ran**, **block unauthorized tools**, and
**absorb your existing tests/linters** without replacing them.

Review signals never grant automatic approval. Unobserved is never green.

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://github.com/lofibrainwav/HyoDo/blob/main/LICENSE)](./LICENSE)

## Why HyoDo (vs pre-commit alone)

| Need | HyoDo |
| --- | --- |
| Agent step audit trail | `event record` → `.hyodo/agent-events.jsonl` |
| Tool / path / step policy | `policy check` (ALLOW / DENY; missing = exit 2) |
| Keep existing CI tools | BYOG `init` absorbs pytest/ruff/npm/go/… |
| Fake-green resistance | fail-closed score + SKIP ≠ PASS |
| Air-gapped / on-prem | loopback dashboard, offline-safe design |

`pre-commit` + ruff is still excellent for hooks. HyoDo adds **agent
evidence + policy gates + honest measurement** for FDE deployment defense.

## Start here (any repository)

```bash
pipx install hyodo
cd your-project
hyodo safe                 # early-warning scan, no setup
hyodo safe --strict        # exit 1 on high-severity findings
hyodo safe --json          # machine-readable findings for CI
```

```yaml
# GitHub Actions
- run: pipx install hyodo
- run: hyodo safe --strict --json
```

`hyodo safe` is an early-warning scanner, not a full security audit.

### Bring your own gates (optional)

```bash
hyodo init                 # detect tools → write .hyodo/gates.toml
hyodo check                # run absorbed gates
hyodo dashboard --open     # local evidence panel (127.0.0.1)
```

`init` reads tooling you already own (`pytest`/`ruff`/`mypy`/`pyright`,
npm scripts, `go.mod`, `Cargo.toml`, Makefile targets). It does not
reinvent them. Empty detection → commented starter (no guessing).
Malformed or zero executed gates → exit **2** (not a pass).

### Agent evidence spine (opt-in FDE)

```bash
hyodo event validate --file step.json
hyodo event record --file step.json --root . --policy .hyodo/policy.toml
hyodo policy check --file step.json --config .hyodo/policy.toml
hyodo schema check --schema agent.schema.json --payload step.json --json
```

Default storage is **digest-only**. DENY is recorded for audit; **the
caller must stop the agent** — HyoDo is a gate, not a runtime
interceptor. Examples: `examples/fde-evidence-spine/`.

`schema check` validates a local JSON payload deterministically. It returns
`0` for valid, `1` for a schema violation, and `2` when the schema or payload
cannot be observed or trusted. `--json` emits structured reasons for tools.

### Optional local MCP stdio

```bash
pip install 'hyodo[mcp]'
hyodo mcp stdio --root .
```

This starts a local standard-input/output MCP process only. It wraps the
existing `safe`, `check`, `event record`, and `policy check` CLI contracts
for the configured host workspace. It does not open a network listener or
give a client access to files outside that workspace.

## Engineering map (branding kept, terms first)

| DevSecOps label | Pillar | Measured by |
| --- | --- | --- |
| Static types | Truth (眞 / 진) | Command gate (typechecker) |
| Tests + safety | Goodness (善 / 선) | Tests + `safe` |
| Lint / format | Beauty (美 / 미) | Command gate (linter) |
| Public surface | Benevolence (仁 / 인) | Native AST scan |
| Data privacy | Hyo (孝 / 효) | Native consent/data scan |
| Audit trail | Yeong (永 / 영) | `.hyodo/history.jsonl` |

Command gates are absorbed tools. AST / ledger pillars are **never**
shell-faked. Missing sources show `Not measured`. Fail-closed geometric
mean (HYOGOOK V5 formula, philosophy V6 labels): any pillar at 0
collapses the review signal. Detail: [PHILOSOPHY.md](./PHILOSOPHY.md).

## Local instrument panel

```bash
hyodo dashboard --open
# → http://127.0.0.1:8768
```

Loopback only; 15s poll of `/api/evidence`; no composite invention.
**Measure again now** is token-protected.

## Install

Python 3.10+. `pip install -U hyodo` or `pipx install hyodo`.
See [Quick Start](./QUICK_START.md).

## Commands

| Command | Purpose |
| --- | --- |
| `hyodo safe` | Safety findings (early warning) |
| `hyodo init` | Write `.hyodo/gates.toml` (BYOG) |
| `hyodo check` | Absorbed gates or checkout preset |
| `hyodo event …` | Agent event validate / record |
| `hyodo policy check` | Agent policy ALLOW / DENY |
| `hyodo schema check` | Deterministic local JSON Schema validation |
| `hyodo mcp stdio` | Optional local MCP CLI adapter |
| `hyodo score …` | Optional review signal |
| `hyodo dashboard` | Local evidence panel |

**safe:** `0` findings · `1` high+`--strict` · `2` bad path.
**check:** `0` all executed PASS · `1` FAIL · `2` none/malformed.
**event/policy:** `0` ok/ALLOW · `1` invalid/DENY · `2` unobserved.
**schema check:** `0` valid · `1` validation error · `2` unobserved input.

## Scope

| Surface | Status |
| --- | --- |
| `hyodo/` package and CLI | Public release surface |
| `tests/` and CI workflows | Release verification |

Model-agnostic ≠ language-agnostic. Export PDF audit packs and full
runtime interceptors are roadmap items — not claimed shipped.

## For contributors

```bash
git clone https://github.com/lofibrainwav/HyoDo.git && cd HyoDo
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]" && ./.venv/bin/hyodo check
```

## Documentation

- [Quick Start](./QUICK_START.md) · [Philosophy](./PHILOSOPHY.md)
- [Security surface](./docs/SECURITY_SURFACE.md)
- [FDE spine examples](./examples/fde-evidence-spine/)
- [Changelog](./CHANGELOG.md) · [Roadmap](./ROADMAP.md)

## License

HyoDo is available under the [MIT License](./LICENSE).
