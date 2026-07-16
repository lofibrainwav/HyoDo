# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
