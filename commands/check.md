---
description: "Run HyoDo 4-Gate CI protocol (Truth/Beauty/Goodness/Eternity)"
allowed-tools: Bash(hyodo:*), Bash(ruff:*), Bash(pyright:*), Bash(pytest:*), Read
impact: CRITICAL
tags: [ci, quality, testing, lint]
---

# 4-Gate CI Lock Protocol

Run the CI lock protocol to verify code quality.

## Gate order

1. **Truth - Pyright**: type check
2. **Beauty - Ruff**: lint + format
3. **Goodness - pytest**: unit tests
4. **Eternity - SBOM**: security seal (only when repo checkout + script exist)

## Recommended run

Vendor-neutral CLI:

```bash
pip install -e ".[dev]"
hyodo check
```

Run public package gates the same way CI does:

```bash
ruff check hyodo/ --output-format=concise
ruff format --check hyodo/
pyright hyodo
pytest -q --tb=short
```

> Makefile-based check targets are not provided in this repository. CI SSOT is
> `.github/workflows/ci.yml` and `hyodo check`.

## Individual gates

- `pyright hyodo` — type check (public package)
- `ruff check hyodo/` — lint
- `ruff format --check hyodo/` — format
- `pytest -q` — tests

## How to read results

- **PASS**: all gates green -> commit/PR candidate (human review still separate)
- **FAIL**: fix the failing gate and re-run

Passing gates is not automatic merge/deploy approval.

## Evidence template

```text
Gate: [Pyright|Ruff|pytest|SBOM]
Status: [PASS|FAIL]
Details: [error summary or OK]
```
