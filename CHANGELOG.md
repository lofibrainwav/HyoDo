# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.7] - 2026-07-16

### Fixed

- **Ruff gate runs format**: `hyodo check` Gate 2 now executes both `ruff check`
  and `ruff format --check` (with `--fix`, format write). Format-only failures
  no longer false-green.
- **`hyodo safe` scan read failure**: unreadable paths report `error:read:` and
  exit **2** (same class as missing path). OSError is no longer swallowed into
  empty corpus + exit 0.
- **Path-length-stable CLI test**: checkout path assertion tolerates Rich
  line-wrapping of long absolute paths.

### Changed

- Public regression tests cover format-fail gate and scan-error exit 2.
- Coverage floor raised from `fail_under = 0` to `fail_under = 50` for the public
  `hyodo` package.
- Version SSOT and install pins aligned to **3.1.7**.

### Notes

- Follow-up Truth Patch after 3.1.6 cross-audit (P1 only). No language-agnostic
  expansion, Trusted Publishing, or `afo_core` split in this release.

## [3.1.6] - 2026-07-16

### Fixed

- **Truth contract for `hyodo check`**: no longer reports `All gates passed` when
  zero gates ran. Unsupported trees exit 2 with `No project gates were executed`
  / `This is not a validation pass`. PASS / FAIL / SKIP / UNSUPPORTED are
  separated (SKIP is not painted as PASS).
- **`hyodo check PATH`**: gates resolve and run against the given path's HyoDo
  checkout root instead of re-probing only `Path.cwd()`.
- **`hyodo safe --strict`**: exits 1 when any high-severity finding is present
  (CI-usable). Default mode remains early-warning exit 0. Missing path exits 2.
- **Legacy `calculate_trinity_score`**: weight sum is normalized so all-ones
  inputs yield 100 (was 95 because weights summed to 0.95).
- **CI false-green**: public `tests/` pytest is a release blocker
  (`continue-on-error` removed). Markdown lint is explicitly advisory.
  Smoke expects empty-directory `hyodo check` exit 2 and `safe --strict`
  high-risk fixture exit 1.

### Changed

- Score CLI/README: review-emphasis percentages are labeled as not used in the
  F formula (`F = sum(1–10 pillars) + geometric mean`).
- `should_auto_approve()` is a deprecation warning wrapper around
  `is_strong_review_signal()` (removal planned for 4.0.0).
- Documented scan limits: directory cap 40 files; default corpus is git
  diff/status when no path is given.

### Notes

- Shipped as **3.1.6** because PyPI already had **3.1.5** when this patch landed.
- GitHub tag `v3.1.6` + PyPI `hyodo==3.1.6` published after merge (measure live if citing).
- No language-agnostic expansion, SARIF, or TruffleHog in this release.

## [3.1.5] - 2026-07-16

### Changed

- Refreshed the demo receipt with explicit pre-commit provenance and current
  public CLI output.
- Made installer headers read `VERSION` when available instead of carrying a
  stale patch number.
- Reconciled release/demo documentation with the live zero-open Dependabot
  alert readback while retaining the historical cleanup context.

## [3.1.4] - 2026-07-16

### Added

- `[tool.pyright] pythonVersion = "3.10"` in `pyproject.toml` so Pyright matches
  `requires-python >=3.10` (avoids PEP 604 false-red when tools default to 3.9).

### Changed

- Score / docs wording: "strong review signal" only — never "proceed immediately"
  or bare "candidate for approval" without human-gate language.
- `QUICK_START.md` rewritten as CLI-first pointer to `QUICK_START_SIMPLE.md`.
- `hyodo safe` action strings: low/caution use human-gate language only.
- `LICENSE.md` points at canonical `LICENSE` (same MIT).
- `PHILOSOPHY.md` rewritten as short HYOGOOK V5 public note.
- Version SSOT and public badges/demo receipts aligned to `3.1.4`.

### Removed

- Empty English-SSOT stub docs (`docs/ARCHITECTURE.md`, JS/TS stub, security-scanning stub).
- Stale tracked `artifacts/sbom` and `memory/` placeholder notes.

## [3.1.3] - 2026-07-16

### Fixed

- `hyodo check` package mode (wheel-only / empty cwd): skip type/lint when no repo checkout,
  so smoke `hyodo check` after `pip install dist/*.whl` exits 0 without dev extras.
- Missing pyright/ruff/pytest soft-skip in package mode; still hard-fail inside a repo.

## [3.1.2] - 2026-07-16

### Fixed

- `hyodo check` runs pyright/ruff/pytest via `sys.executable -m ...` so PATH
  homebrew tools cannot break the Goodness gate with a foreign interpreter.
- `hyodo check` now exits non-zero when any gate fails (demo-safe, CI-safe).

### Added

- `scripts/demo-dry-run.sh` and refreshed demo docs for the v3.1.x public path.
- Unit coverage for CLI tool invocation helpers.

## [3.1.1] - 2026-07-16

### Added

- `scripts/verify-public.sh` — local public package gate (lint, typecheck, tests, build, sdist guard, CLI).
- `scripts/release/check_version_sync.py` and `set_version.py` — VERSION / pyproject / `__init__` SSOT.
- `docs/DEMO_READY_CHECKLIST.md` for post-release demo preflight.
- Model-agnostic provider proof map (`docs/PROVIDER_PROOF.md`).
- Security surface boundary doc (`docs/SECURITY_SURFACE.md`).
- External claim audit with measured evidence (`docs/EXTERNAL_CLAIM_AUDIT.md`).
- Real early-warning safety scanner (`hyodo/safety.py`) used by `hyodo safe`.
- Unit tests for safety helpers (`tests/test_safety.py`).
- Dependabot config for public surface and grouped `afo_core` updates.
- Public API `is_strong_review_signal` (review signal only; not auto-approval).

### Changed

- Public product language is **English-only**. Locale trees (`i18n/ko|zh|ja`) removed.
- Public docs and CLI lead with model-agnostic CLI/CI; Claude Code is optional.
- Primary product framing no longer leads with "cost-aware savings".
- Badge/copy use **tiered routing (intent only)** and state no public savings benchmark.
- Removed public auto-approval language from CLI score/check outputs.
- Hatch **sdist** limited to public package surface (does not ship `afo_core`).
- Pytest/coverage default to public `hyodo` package only.
- afo_core security floors and lock SSOT (poetry.lock only; no requirements double-count).
- afo_core Python range tightened to `>=3.10,<3.14` for litellm compatibility.
- Install scripts rewritten in English; minimal install does not require Docker/Redis/Postgres.
- CI regression guard bans auto-approve phrasing on public surfaces.
- Smoke workflow: dynamic VERSION sync, sdist afo_core guard.
- Documented no-patch Dependabot dismiss policy for diskcache/torch residual.

### Removed

- Japanese, Chinese, and Korean localization trees under `i18n/`.
- Language switcher links from root docs.
- Optional `chromadb` / chroma vector store from afo_core (Qdrant SSOT).
- Optional `mem0ai`, `crewai`, `moviepy` from afo_core dependency solves.
- Repo clutter: stub improvement/migration notes, transplant verifier, kingdom-only
  memory hooks, broken ticket045/validator scripts that pointed at missing `packages/afo-core`.

## [3.1.0] - 2026-05-08

### Added

- Interactive installer and simple quick start path.
- Minimal Docker compose profile for optional extended services.
- HYOGOOK V5 public documentation for optional scoring.

### Changed

- Version alignment to `3.1.0` across package metadata and badges.
