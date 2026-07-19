# HyoDo

**Honest quality gates for AI-assisted Python work.**

[![CI](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml/badge.svg)](https://github.com/lofibrainwav/HyoDo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyodo)](https://pypi.org/project/hyodo/)
[![Python](https://img.shields.io/pypi/pyversions/hyodo)](https://pypi.org/project/hyodo/)
[![License](https://img.shields.io/github/license/lofibrainwav/HyoDo)](./LICENSE)

HyoDo provides a small CLI and CI workflow for reviewing AI-assisted changes.
It combines type checking, linting, tests, safety warnings, and an optional
review score without granting automatic approval.

## Two tracks

HyoDo has two surfaces with deliberately different scopes:

- **`safe` — outward, any repository.** A dependency-light safety
  early-warning scanner (secrets, dangerous commands, production
  impact). Run `hyodo safe` or `hyodo safe --json` on your diff.
- **`check` — reference, a HyoDo checkout only.** HyoDo's own
  release gates (Pyright/Ruff/pytest/SBOM). It proves HyoDo's
  honesty contract; it does not gate arbitrary projects.

If you want a gate for *your* repo today, use `safe`. `check` is intentionally
scoped to HyoDo itself.

## Install

Python 3.10 or newer is required.

```bash
pip install -U hyodo
hyodo --version
```

The installed package exposes `score`, `safe`, and onboarding commands from any
directory:

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 \
  --benevolence 0.9 --loyalty 0.9
hyodo safe path/to/file_or_diff_context
hyodo safe --strict path/to/file_or_diff_context
```

`hyodo check` currently validates a **HyoDo repository checkout**, not an
arbitrary project. Clone the repository to run its full release gates:

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m pip install -e ".[dev]"
hyodo check
```

See [Quick Start](./QUICK_START.md) for the complete first-run path.

## Commands

| Command | Purpose |
| --- | --- |
| `hyodo start` | Show onboarding guidance |
| `hyodo check [PATH]` | Run HyoDo checkout gates |
| `hyodo score ...` | Produce a review signal |
| `hyodo safe [PATH]` | Print safety findings without blocking |
| `hyodo safe --strict [PATH]` | Exit 1 when high-severity findings exist |
| `hyodo safe --json [PATH]` | Emit machine-readable JSON findings for CI |
| `hyodo trinity "CHANGE"` | Produce a structured review checklist |

### `hyodo check` exit contract

| Exit | Meaning |
| ---: | --- |
| `0` | At least one gate ran and every executed gate passed |
| `1` | An executed gate failed |
| `2` | The path is missing or no applicable gate ran |

The checkout gates run Pyright, Ruff, pytest, and an optional SBOM check. A
zero-gate run is never reported as success.

### `hyodo safe` exit contract

- Default mode prints findings and exits `0`.
- `--strict` exits `1` when a high-severity finding is present.
- Missing or unreadable paths exit `2`.

`hyodo safe` is an early-warning scanner, not a security audit.

## Scope

The supported release surface is intentionally narrow:

| Surface | Status |
| --- | --- |
| `hyodo/` Python package and CLI | Public release surface |
| `tests/` and `.github/workflows/` | Release verification |

Model-agnostic means the core CLI does not require a specific AI provider or
agent UI. It does not mean language-agnostic or universal repository support.

## Optional review score

HYOGOOK V5 evaluates Truth, Goodness, Beauty, Benevolence, and Loyalty, with a
geometric-mean harmony signal. Scores support review; they never replace tests,
security checks, or human approval.

The practical CLI works without this optional philosophy layer. See
[HyoDo philosophy](./PHILOSOPHY.md) for the short model description.

## Documentation

- [Quick Start](./QUICK_START.md)
- [Documentation index](./docs/README.md)
- [Provider support evidence](./docs/PROVIDER_PROOF.md)
- [Security boundaries](./docs/SECURITY_SURFACE.md)
- [External claim audit](./docs/EXTERNAL_CLAIM_AUDIT.md)
- [Changelog](./CHANGELOG.md)
- [Roadmap](./ROADMAP.md)

## Contributing and security

See [CONTRIBUTING.md](./CONTRIBUTING.md) before opening a pull request. Report
security issues through the process in [SECURITY.md](./SECURITY.md).

## License

HyoDo is available under the [MIT License](./LICENSE).
