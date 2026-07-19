# CLAUDE.md

Guidance for AI coding agents working in this repository.

## Project Overview

HyoDo is a model-agnostic quality-gate kit for AI-assisted development. Primary
surface is the public `hyodo` CLI and CI gates.

**Version**: see `VERSION`
**Python**: 3.10+  
**Public language**: English only

## Commands

### Main commands

- `hyodo start` / `/start` - onboarding
- `hyodo check` / `/check` - quality gates
- `hyodo score` / `/score` - review signal (not auto-approval)
- `hyodo safe` / `/safe` - safety early-warning scan
- `hyodo trinity` / `/trinity` - structured review checklist
- `/cost "task"` - cost routing signal

### Development commands

```bash
pip install -e ".[dev]"
ruff check hyodo/ --fix && ruff format hyodo/
pytest tests -q
pyright hyodo
hyodo check
hyodo safe
```

## Architecture

### Public package

The public product is `hyodo/` (Python package + CLI) with root `pyproject.toml`.

### Optional HYOGOOK V5 review signal

| Pillar | Weight | Focus |
|--------|--------|-------|
| Benevolence | 25% | Developer experience |
| Truth | 22% | Technical accuracy |
| Goodness | 18% | Security and stability |
| Loyalty | 15% | Project/context alignment |
| Beauty | 15% | Clarity and UX |
| Eternity | geometric mean | Long-term harmony |

Scores are decision support only. They do not authorize merge/deploy.

### Directory structure

```text
HyoDo/
├── hyodo/               # Public Python package (CLI + scoring)
├── tests/               # Public package tests
├── docs/                # Proof maps and audits
├── scripts/             # Release + verification tooling
└── .github/workflows/   # CI + smoke
```

## Security notes

- Do not commit secrets.
- `hyodo safe` is early warning only.
- See `docs/SECURITY_SURFACE.md` and `docs/EXTERNAL_CLAIM_AUDIT.md`.
