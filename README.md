# HyoDo

**Honest quality gates for AI-assisted Python work.**

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://img.shields.io/github/license/lofibrainwav/HyoDo)](./LICENSE)

Scan AI-assisted changes for secrets, dangerous commands, and production
risks. Then absorb *your* project's own tests and linters as quality gates.
Scores are **review signals only** — never automatic approval.

## Start here (any repository)

```bash
pipx install hyodo
cd your-project
hyodo safe                 # early-warning scan, no setup
hyodo safe --strict        # exit 1 on high-severity findings
hyodo safe --json          # machine-readable findings for CI
```

### CI snippet (GitHub Actions)

```yaml
- run: pipx install hyodo
- run: hyodo safe --strict --json
```

`hyodo safe` is an early-warning scanner, not a full security audit.

### Bring your own gates (optional)

```bash
hyodo init                 # detect tools → write .hyodo/gates.toml
hyodo check                # run absorbed gates
hyodo dashboard --open     # local evidence panel
```

`hyodo init` reads existing tooling (`pyproject.toml` pytest/ruff/mypy/
pyright, npm test/lint, `tsconfig.json`, `go.mod`, `Cargo.toml`, Makefile
`test:`/`lint:`) and writes `.hyodo/gates.toml`. It does not reinvent those
tools.

Measured CLI contracts (v4.2.0):

- Existing `.hyodo/gates.toml` → `hyodo init` exits **1** unless `--force`.
- Empty detection → starter template with commented examples (no guessing).
- Starter with no gates defined → `hyodo check` exits **2**
  (`This is not a validation pass`).
- When present, `.hyodo/gates.toml` beats the HyoDo checkout preset.

## Six pillars — branding kept, engineering mapped

| Pillar | Technical meaning | Measured by |
| --- | --- | --- |
| Truth (眞 / 진) | Type / static correctness | Command gate (typechecker) |
| Goodness (善 / 선) | Tests + safety stability | Command gate (tests) + `safe` |
| Beauty (美 / 미) | Lint / format | Command gate (linter) |
| Benevolence (仁 / 인) | Public-surface integrity | Native AST scan |
| Hyo (孝 / 효) | Consent + data protection | Native AST scan |
| Yeong (永 / 영) | Continuity of measurement | `.hyodo/history.jsonl` |

Truth / Goodness / Beauty come from commands you absorb (or HyoDo's preset).
Benevolence / Hyo / Yeong are **never** command gates — they cannot be gamed
by a fake-green shell script. Missing sources show `Not measured`.

Detail and fail-closed score math: [PHILOSOPHY.md](./PHILOSOPHY.md).

## Local instrument panel

```bash
hyodo dashboard --open
# → http://127.0.0.1:8768
```

```text
Truth / Goodness / Beauty   PASS | FAIL | Not measured
In / Hyo / Yeong            native collectors
[Measure again now]         raw JSON → /api/evidence
```

(Replace with a real screenshot under `docs/` when available.)

The panel never invents a composite score. With `.hyodo/gates.toml`, gate
rows use your absorbed names; otherwise the checkout preset applies.

### How it works / security

- Loopback only (`127.0.0.1`) — analysis stays off the LAN.
- 15s poll of `/api/evidence` (no websocket dependency).
- `--interval N` re-measures in the background.
- **Measure again now** is token-protected; no path injection.
- Change-safety card uses the current Git diff only; no diff →
  `Not measured`.

## Install

Python 3.10 or newer.

```bash
pip install -U hyodo
# or: pipx install hyodo
hyodo --version
```

See [Quick Start](./QUICK_START.md).

## Commands

| Command | Purpose |
| --- | --- |
| `hyodo safe [PATH]` | Safety findings (non-blocking) |
| `hyodo safe --strict` | Exit 1 on high-severity findings |
| `hyodo safe --json` | JSON findings for CI |
| `hyodo init [PATH]` | Write `.hyodo/gates.toml` (BYOG) |
| `hyodo check [PATH]` | Absorbed gates, else checkout preset |
| `hyodo check --general` | Bounded multi-language syntax sample |
| `hyodo score ...` | Optional review signal |
| `hyodo dashboard` | Local evidence panel |
| `hyodo start` | Onboarding guidance |
| `hyodo trinity "…"` | Structured review checklist |

### Exit contracts

**safe:** `0` print findings · `1` high + `--strict` · `2` bad path.

**check:** `0` ≥1 executed gate and all executed passed · `1` executed
failed · `2` missing path, malformed `gates.toml`, or zero executed gates.

Resolution: `--general` → `.hyodo/gates.toml` → HyoDo checkout preset →
guidance toward `hyodo init`.

## Optional review score

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --hyo 0.9
```

Optional **HYOGOOK V5** F-score (philosophy V6 labels) uses a geometric mean:
any pillar at 0 collapses the whole signal (fail-closed). Scores never replace
tests, `safe`, or human approval. See [PHILOSOPHY.md](./PHILOSOPHY.md).

## Scope

| Surface | Status |
| --- | --- |
| `hyodo/` package and CLI | Public release surface |
| `tests/` and CI workflows | Release verification |

Model-agnostic ≠ language-agnostic. `--general` is a bounded sample, not
universal multi-stack coverage.

## For contributors (dogfood)

```bash
git clone https://github.com/lofibrainwav/HyoDo.git && cd HyoDo
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]" && ./.venv/bin/hyodo check
```

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Documentation

- [Quick Start](./QUICK_START.md) · [Philosophy](./PHILOSOPHY.md)
- [Docs index](./docs/README.md) · [Provider proof](./docs/PROVIDER_PROOF.md)
- [Security surface](./docs/SECURITY_SURFACE.md)
- [Changelog](./CHANGELOG.md) · [Roadmap](./ROADMAP.md)

## License

HyoDo is available under the [MIT License](./LICENSE).
