# HyoDo repository guidance

Instructions for coding agents working in this repository.

## Product boundary

HyoDo is a public, host-neutral, model-agnostic trust, evidence, policy, and
attestation layer. The integrating host or harness owns orchestration, memory,
retrieval, runtime, execution, and final authority. HyoDo is not KINGDOM.

The canonical virtue set is exactly six: Truth / 眞, Goodness / 善, Beauty / 美,
Benevolence / 仁, Hyo / 孝, and Eternity / 永. A virtue is not evidence;
evidence is not a decision; a score or receipt is not authority. Merged is not
served, and UNOBSERVED is not GREEN. KINGDOM-specific behavior is upstreamed
only when it generalizes into a reusable public primitive.

- `hyodo/` is the public Python package and primary release surface.
- `tests/` contains the public package tests.

Do not describe HyoDo as a universal project scanner. The public `hyodo check`
path supports BYOG project checks, while HyoDo's own full verification requires
a checkout containing `pyproject.toml` and `hyodo/`; these are separate scopes.

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
