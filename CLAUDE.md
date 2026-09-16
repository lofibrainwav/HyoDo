# CLAUDE.md

Guidance for AI coding agents working in this repository.

## Project Overview

HyoDo is a model-agnostic quality-gate kit for AI-assisted development. Primary
surface is the public `hyodo` CLI and CI gates.

**Version**: see `VERSION`
**Python**: 3.10+  
**Public language**: English only

### What "English only" covers

This repository is public. Everything a reader outside the project can see is
English — not just CLI output:

- code comments and docstrings
- commit messages and PR titles/bodies
- CHANGELOG, docs, issue text
- identifiers, log lines, error messages

The one deliberate exception is the six virtue labels, which ship as
hanja/Hangul/English together (`("jin", "眞", "진", "Truth", ...)`) because the
trilingual form *is* the label. Do not extend that exception to prose.

Agents arriving from the Kingdom repos carry a Korean-first convention. It does
not apply here, and this line is the SSOT — if another doc in this repo says
otherwise, that doc is wrong and should be corrected.

**Attribution**: state the model in `Co-Authored-By`. That is truthful and it is
English. Do not add a Korean authorship line — the Kingdom seat name is internal
and carries no meaning for a reader of this repository.

Both halves are enforced: `tests/test_public_language.py` covers tracked files,
and the `public-language` CI job covers commit messages and PR title/body.

## Commands

### Main commands

- `hyodo start` - onboarding
- `hyodo check` - quality gates
- `hyodo score` - review signal (not auto-approval)
- `hyodo safe` - safety early-warning scan
- `hyodo trinity` - structured review checklist
- `hyodo event` / `hyodo policy` - agent evidence and policy decisions (`event validate` exits 0 valid / 1 invalid / 2 unreadable; policy results exit 0 ALLOW / 1 DENY / 2 UNOBSERVED / 3 ASK — see QUICK_START.md; `UNOBSERVED` means there is not enough evidence to say whether a check passed or failed)
- `hyodo mcp` - optional MCP adapter (no slash commands ship in this repo)

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

### Optional HyoDo Integrity Score

This table is an internal PR-review emphasis checklist for this repository. It is not a personal virtue-weighted aggregate: the percentages are illustrative review weights, they are not meant to sum to 100, and they do not define anyone's EROS-style profile. A host that builds a weighted lens on top of the six virtues owns and configures that lens itself.

| Virtue | Review emphasis | Focus |
|--------|--------|-------|
| Benevolence | 25% | Developer experience |
| Truth | 22% | Technical accuracy |
| Goodness | 18% | Security and stability |
| Hyo | 15% | Project/context alignment |
| Beauty | 15% | Clarity and UX |
| Eternity | narrative, not a percentage | Longitudinal continuity evidence; any harmony aggregate is a separate derived value |

The score uses the Six-Virtue Model and Trinity Gates subset; HYOGOOK V5 is the
formula lineage (internal lineage names recorded in CHANGELOG.md; there is no separate public spec). Scores are decision support only and do not authorize
merge/deploy.

HyoDo is public, host-neutral, and model-agnostic. It observes, validates,
records, attests, and measures. The integrating host or harness owns
orchestration, memory, retrieval, runtime, execution, and final authority.
The host also owns and configures any virtue-weighted lens or profile it builds
on top of HyoDo's six-virtue philosophy, and it decides action authorization
separately from any lens result; HyoDo does not own or configure that lens.
HyoDo is not KINGDOM; a HyoDo receipt or score is evidence, never authority.
The canonical boundary contract is `docs/PRODUCT_BOUNDARY.md`.

The canonical invariants are: Map is not Territory, Evidence is not a
Decision, Capability is not Authority, Receipt is not Authority, Merged is not
Served, and UNOBSERVED is not GREEN.

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
