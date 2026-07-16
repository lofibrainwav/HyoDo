# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Primary product framing no longer leads with "cost-aware savings".
- Badge/copy use **tiered routing (intent only)** and state no public savings benchmark.
- `docs/SECURITY_SURFACE.md` records next afo_core Dependabot patch priorities.
- Regenerated `afo_core` poetry.lock with security floors (litellm, nltk, transformers, ...).
- `afo_core/requirements.txt` is now a Poetry export; removed duplicate `requirements-lock.txt`.
- Dropped `crewai` and `moviepy` optional deps that blocked secure dependency solves.
- afo_core Python range tightened to `>=3.10,<3.14` for litellm compatibility.
- Removed `chromadb` / `llama-index-vector-stores-chroma` from afo_core (Qdrant SSOT;
  eliminates residual critical Dependabot surface with no safe patched release).
- P1 high-volume security floors: aiohttp 3.14.1, starlette 1.3.1, fastapi 0.139+,
  Mako/PyJWT/banks/langsmith/lxml/mcp/orjson/protobuf/soupsieve.
- Stop committing pinned afo_core requirements export to avoid Dependabot double-count
  (poetry.lock is the only SSOT).
- P2 medium floors: idna/requests/pytest/dotenv/pygments/pydantic-settings/torch 2.10.
- Removed optional `mem0ai` from afo_core agents extras (not required; soft-fail paths).

### Added

- Model-agnostic provider proof map (`docs/PROVIDER_PROOF.md`).
- Security surface boundary doc (`docs/SECURITY_SURFACE.md`).
- External claim audit with measured evidence (`docs/EXTERNAL_CLAIM_AUDIT.md`).
- Real early-warning safety scanner (`hyodo/safety.py`) used by `hyodo safe`.
- Unit tests for safety helpers (`tests/test_safety.py`).
- Dependabot config for public surface and grouped `afo_core` updates.

### Changed

- Public product language is **English-only**. Locale trees (`i18n/ko|zh|ja`) removed.
- Public docs and CLI lead with model-agnostic CLI/CI; Claude Code is optional.
- Removed public auto-approval language from CLI score/check outputs.
- `commands/check.md` documents `hyodo check` and CI commands (no Makefile check).
- `SECURITY_PATCHES.md` marked historical; Dependabot is live inventory for extended tree.
- Install scripts rewritten in English; minimal install does not require Docker/Redis/Postgres.
- Cost routing docs use FREE / STANDARD / PREMIUM tiers without vendor exclusivity.
- CI regression guard bans auto-approve phrasing on public surfaces.

### Removed

- Japanese, Chinese, and Korean localization trees under `i18n/`.
- Language switcher links from root docs.

## [3.1.0] - 2026-05-08

### Added

- Interactive installer and simple quick start path.
- Minimal Docker compose profile for optional extended services.
- HYOGOOK V5 public documentation for optional scoring.

### Changed

- Version alignment to `3.1.0` across package metadata and badges.
