# Contributing to HyoDo

> "The Spirit of King Sejong: Practical innovation for the people"

Thank you for your interest in contributing to HyoDo!

## HYOGOOK V5 Contribution Principles

All contributions are evaluated according to the six pillars used in the public HyoDo v3.1.x documentation.

| Pillar | Meaning | Focus |
|--------|---------|-------|
| Benevolence | Developer experience | User serenity and clear DX |
| Truth | Technical accuracy | Architecture and evidence |
| Goodness | Security and stability | Safe defaults, no secrets |
| Loyalty | Continuity | SSOT and project integrity |
| Beauty | Clarity | Readability, UX, docs |
| Eternity | Harmony | Long-term maintainability |

### Score Expectations

HyoDo currently uses the HYOGOOK V5 evaluation model documented in `README.md`.
Scores are **review signals only** — they never replace human review or merge authority.

| Result | Meaning | Action |
|--------|---------|--------|
| F ≥ 54 and S ≥ 8 | Excellent | Strong review signal |
| F ≥ 45 and S ≥ 7 | Good | Review recommended |
| F < 45 | Needs work | Changes required |

> Legacy WEIGHTED_V1 contribution weights are preserved only for historical reference.

## Contribution Process

### 1. Create an Issue

Before working on new features or bug fixes, please create an Issue to discuss your proposal.

### 2. Fork & Branch

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
git checkout -b feature/your-feature-name
```

### 3. Development Guidelines

- Follow the existing code style (Ruff for Python)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic
- Avoid changing philosophy or scoring logic without documentation updates

### 4. Testing

Run the quality gates before submitting:

```bash
# Type checking
pyright

# Linting
ruff check .

# Tests
pytest
```

If using Claude Code:

```bash
/check          # Full 4-gate CI check
/trinity        # HYOGOOK V5 analysis
```

### 5. Pull Request

- Write a clear PR title describing the change
- Fill out the PR template
- Link related Issues
- Ensure documentation matches implementation
- Ensure HYOGOOK V5 scoring references stay consistent

## Code Style

### Python

- Use type hints for all public functions
- Follow PEP 8 (enforced by Ruff)
- Line length: 100 characters
- Docstrings for public functions

### Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
refactor: code improvement
```

## Testing Structure

The public `hyodo` package and the extended `afo_core` modules currently share validation infrastructure.

```text
hyodo/            -> public package and CLI
afo_core/tests/   -> extended evaluation and integration tests
```

## Getting Help

- Open an Issue for questions
- Check existing Issues and PRs
- Read the [Documentation](./docs/)

## Code of Conduct

Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) before contributing.

---

*"Strategists command, warriors execute"* - HyoDo OSS Philosophy
