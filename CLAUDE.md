# CLAUDE.md

Guidance for AI coding agents working in this repository.

## Project Overview

HyoDo is a model-agnostic quality-gate kit for AI-assisted development. Primary
surface is the public `hyodo` CLI and CI gates. Optional agent adapters live in
`commands/`. Extended backend modules live in `afo_core/` and are advisory for
public release.

**Version**: 3.1.3  
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

### Public package vs extended tree

| Surface | Path | Release gate |
|---------|------|--------------|
| Public product | `hyodo/`, root `pyproject.toml` | Yes |
| Agent adapters | `commands/`, `agents/` | Docs only |
| Extended / legacy | `afo_core/` | Advisory |

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
├── commands/            # Optional agent slash-command docs
├── agents/              # Optional agent helpers
├── docs/                # Proof maps, security surface, audits
├── .github/workflows/   # CI + smoke
└── afo_core/            # Extended/legacy backend (advisory)
```

### afo_core backend

For backend-specific work in `afo_core/`, see `afo_core/CLAUDE.md` when present.
Extended services may involve Redis/Postgres/Docker; they are **not** required
for the public CLI path.

## Security notes

- Do not commit secrets.
- `hyodo safe` is early warning only.
- Dependabot volume on `afo_core` lockfiles is not the public package surface.
- See `docs/SECURITY_SURFACE.md` and `docs/EXTERNAL_CLAIM_AUDIT.md`.
