# CLAUDE.md

@AGENTS.md

## Claude Code-specific guidance

Follow the repository constitution above. Claude-specific behavior must remain
additive and must not redefine HyoDo's product boundary, six independent
virtues, evidence states, or authority rules.

## Project Overview

HyoDo is a public, host-neutral, model-agnostic trust, evidence, policy, and
attestation layer. The primary release surface is the public `hyodo` package
and CLI; the integrating host owns orchestration, memory, retrieval, runtime,
execution, and final authority.

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
not apply here. Contradictions with this policy should be reported as drift;
agents should edit the conflicting document only when the task scope permits.

**Attribution**: state the model in `Co-Authored-By`. That is truthful and it
is English. Do not add a Korean authorship line — the Kingdom seat name is
internal and carries no meaning for a reader of this repository.

Both halves are enforced: `tests/test_public_language.py` covers tracked files,
and the `public-language` CI job covers commit messages and PR title/body.

## Commands

### Main commands

- `hyodo start` - onboarding
- `hyodo check` - quality gates
- `hyodo score` - review signal (not auto-approval)
- `hyodo safe` - safety early-warning scan
- `hyodo trinity` - structured review checklist
- `hyodo event` / `hyodo policy` - agent evidence and policy decisions
  (`event validate` exits 0 valid / 1 invalid / 2 unreadable; policy results
  exit 0 ALLOW / 1 DENY / 2 UNOBSERVED / 3 ASK — see QUICK_START.md;
  `UNOBSERVED` means there is not enough evidence to say whether a check passed
  or failed)
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

### Legacy score compatibility

`hyodo score` and its Integrity Score display name are historical compatibility
surfaces. They use the older five-input calculation and must not be described as
the canonical six-virtue evaluator. The six virtues remain independent lenses;
HyoDo does not define one canonical virtue aggregate. Scores are review signals
only and never authorize merge or deployment. See `PHILOSOPHY.md` and
`docs/SCORE_DERIVATION.md` for the compatibility contract.

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
