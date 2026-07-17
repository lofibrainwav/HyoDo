# HyoDo repository guidance

Instructions for coding agents working in this repository.

## Product boundary

- `hyodo/` is the public Python package and primary release surface.
- `tests/` contains the public package tests.
- `commands/` contains optional agent UI adapters.
- `afo_core/` is an extended legacy tree and is not included in the public
  package. Treat its checks as advisory unless a task explicitly targets it.

Do not describe HyoDo as a universal project scanner. Full `hyodo check` gates
currently require a HyoDo checkout containing `pyproject.toml` and `hyodo/`.

## Working rules

- Inspect the current implementation and tests before editing.
- Keep changes focused; preserve unrelated user work.
- Never commit credentials or populated `.env` files.
- Keep public documentation in English.
- Treat scores as review signals, never as merge or deployment authority.
- Do not report a skipped or zero-gate run as success.

## Verification

Use Python 3.10 or newer. The preferred full check is:

```bash
bash scripts/verify-public.sh
```

For focused work, run the relevant subset:

```bash
python -m ruff check hyodo tests
python -m ruff format --check hyodo tests
python -m pyright hyodo
python -m pytest tests -q --tb=short
```

Before finishing, inspect `git diff`, verify local documentation links, and
report tests that were actually run.

## Documentation

- [README.md](./README.md): public product overview
- [QUICK_START.md](./QUICK_START.md): first-run instructions
- [CONTRIBUTING.md](./CONTRIBUTING.md): contribution workflow
- [SECURITY.md](./SECURITY.md): security policy
- [docs/README.md](./docs/README.md): documentation index
