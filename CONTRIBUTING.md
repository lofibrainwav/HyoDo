# Contributing to HyoDo

Thank you for helping improve HyoDo. Contributions should keep the public CLI
small, inspectable, and honest about what was actually verified.

## Before you start

- Search existing [issues](https://github.com/lofibrainwav/HyoDo/issues) and
  [pull requests](https://github.com/lofibrainwav/HyoDo/pulls).
- Open an issue before large features or public API changes.
- Use Python 3.10 or newer.

## Development setup

```bash
git clone https://github.com/lofibrainwav/HyoDo.git
cd HyoDo
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Make a focused change

- Add or update tests for behavior changes.
- Keep public functions typed and documented.
- Update user-facing documentation when commands or exit codes change.
- Do not commit secrets, populated `.env` files, or generated build artifacts.
- Do not present a score as automatic approval.

Use conventional commit subjects where practical:

```text
feat: add a new check
fix: report unreadable paths
docs: simplify the quick start
test: cover strict safety mode
```

## Verify

Run the full public verification before opening a pull request:

```bash
bash scripts/verify-public.sh
```

The script checks version synchronization, Ruff, formatting, Pyright, pytest,
shell syntax, package build metadata, wheel installation, and CLI behavior.

For a focused test loop:

```bash
python -m ruff check hyodo tests
python -m ruff format --check hyodo tests
python -m pyright hyodo
python -m pytest tests -q --tb=short
```

## Pull request checklist

- Explain the problem and the smallest useful solution.
- Link related issues when applicable.
- List the exact verification commands and results.
- Keep unrelated formatting or dependency updates out of the pull request.
- Confirm documentation matches implemented behavior.
- Wait for all required CI checks to pass before merge. CI is the enforced gate.

## How review actually works here

Stating this plainly because a security tool should not overstate its own process.

HyoDo is maintained by a single person. Branch protection requires passing CI and an
up-to-date branch; it does **not** require an approving review, and maintainer pull
requests are normally self-merged once CI is green. "Human review" here means the
maintainer reads the diff — not that a second person signed off.

For outside contributions the maintainer reviews before merge, which *is* a second pair
of eyes. Automated reviewers, when configured, are advisory only; if one is paused or
unavailable, that is a gap in coverage rather than a silent pass, and it should be noted
on the pull request.

## Review principles

HyoDo's optional HYOGOOK V5 score can help structure a review, but tests,
security checks, maintainability, and human judgment remain authoritative. See
[PHILOSOPHY.md](./PHILOSOPHY.md) for the short description.

## Security and conduct

Do not disclose vulnerabilities in public issues. Follow
[SECURITY.md](./SECURITY.md) for private reporting and read
[CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) before participating.
