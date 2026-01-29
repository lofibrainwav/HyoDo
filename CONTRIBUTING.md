# Contributing to HyoDo (孝道)

> "The Spirit of King Sejong: Practical innovation for the people"

<p align="center">
  <a href="./i18n/ko/CONTRIBUTING.md">한국어</a> •
  <a href="./i18n/zh/CONTRIBUTING.md">中文</a> •
  <a href="./i18n/ja/CONTRIBUTING.md">日本語</a>
</p>

Thank you for your interest in contributing to HyoDo!

## 眞善美孝永 Contribution Principles

All contributions are evaluated according to the Five Pillars:

| Pillar | Weight | Contribution Criteria |
|--------|--------|----------------------|
| **眞 (Truth)** | 35% | Is it technically accurate? Does it have tests? |
| **善 (Goodness)** | 35% | Is it safe and stable? No security issues? |
| **美 (Beauty)** | 20% | Is the code readable and well-documented? |
| **孝 (Serenity)** | 8% | Does it improve user experience? |
| **永 (Eternity)** | 2% | Is it maintainable long-term? |

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
/trinity        # Trinity Score analysis
```

### 5. Pull Request

- Write a clear PR title describing the change
- Fill out the PR template
- Link related Issues
- **Trinity Score >= 70 required** for merge

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

## Getting Help

- Open an Issue for questions
- Check existing Issues and PRs
- Read the [Documentation](./docs/)

## Code of Conduct

Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) before contributing.

---

*"Strategists command, warriors execute"* - AFO Kingdom Philosophy
