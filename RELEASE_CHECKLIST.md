# HyoDo Release readiness checklist

This checklist blocks a public release until the package, CLI, and workflow path are verified.

## Current target

- Target version: see `VERSION` (SSOT; do not hardcode)
- Public package path only — `afo_core/` is advisory, not a release blocker
- Truth contracts (v3.1.7+): `check` zero-gates → exit 2; `safe --strict` high → exit 1
- Supply-chain (v3.1.8+): PyPI via Trusted Publishing only — see `docs/PYPI_TRUSTED_PUBLISHING.md`

## Pre-release gates (local)

```bash
bash scripts/verify-public.sh
python scripts/release/check_version_sync.py
```

Expected: exit 0, version synchronized, sdist without `afo_core`, CLI smoke green
(including empty-tree `check` exit 2 and `safe --strict` high-fixture exit 1).

### Documentation

- [ ] `README.md` leads with model-agnostic quality gate (CLI + CI) and honest check scope
- [ ] `CHANGELOG.md` has a section for the target version
- [ ] `QUICK_START_SIMPLE.md` / `CONTRIBUTING.md` use HYOGOOK V5 + review-signal language
- [ ] `SECURITY.md` + `docs/SECURITY_SURFACE.md` document public vs advisory tree
- [ ] No public claim language that implies automatic merge/write authority
- [ ] Exit-code contracts for `check` / `safe` documented in README or quick start
- [ ] PyPI badge only if live index matches the release claim

### Runtime and package

- [ ] Wheel installs and imports `hyodo`
- [ ] `hyodo --version` matches `VERSION`
- [ ] `hyodo score` emits REVIEW_SIGNAL (not approval)
- [ ] `hyodo safe` flags secret fixtures; `--strict` exits 1 on high findings
- [ ] Empty/non-HyoDo `hyodo check` exits 2 (not false green)
- [ ] Sdist does not ship `afo_core`

### CI and smoke (GitHub Actions)

- [ ] `.github/workflows/ci.yml` public gates (Truth / Goodness / Beauty)
- [ ] Public `tests/` pytest is a **release blocker** (not `continue-on-error`)
- [ ] `.github/workflows/smoke.yml` build + twine + wheel + CLI + empty-check exit 2
- [ ] Latest `main` CI run is green (measure before tag)
- [ ] Latest `main` smoke run is green (measure before tag)

## Release steps (after green CI + smoke on main)

1. Confirm Actions are enabled and latest main runs are green.

2. Tag and push the synchronized version (immutable annotated tag; do not retag):

   ```bash
   VERSION="$(tr -d '[:space:]' < VERSION)"
   git tag -a "v$VERSION" -m "HyoDo v$VERSION"
   git push origin "v$VERSION"
   ```

3. Create GitHub Release `v$VERSION` with notes from its `CHANGELOG.md` section.

4. **PyPI publish = Trusted Publishing only** (OIDC; no long-lived API token):

   - One-time setup: `docs/PYPI_TRUSTED_PUBLISHING.md`
     (PyPI publisher: `lofibrainwav` / `HyoDo` / `publish.yml` / env `pypi`)
   - Tag push triggers `.github/workflows/publish.yml`
   - Approve GitHub Environment **`pypi`** deployment if required
   - Job verifies provenance + install smoke automatically
   - Manual measure (optional):

   ```bash
   python scripts/release/verify-pypi-release.py \
     --version "$(tr -d '[:space:]' < VERSION)" \
     --require-provenance \
     --install-smoke
   ```

5. Demo recording uses `docs/DEMO_READY_CHECKLIST.md` **after** this checklist is green.

## Decision log

| Date | Version | Decision |
|------|---------|----------|
| 2026-05 | 3.1.0 | Tag/Release existed; later main advanced past that snapshot |
| 2026-07-16 | 3.1.4 | GitHub release published; PyPI intentionally separate at the time |
| 2026-07-16 | 3.1.5 | Pre-demo surface polish; later PyPI 3.1.5 published |
| 2026-07-16 | 3.1.6 | Truth Patch on GitHub + tag `v3.1.6` + PyPI 3.1.6 (false-green gates removed) |
| 2026-07-16 | 3.1.7 | format gate + safe scan exit 2 + path-stable tests; tag/PyPI 3.1.7 |
| 2026-07-16 | 3.1.8 | Supply-chain seal: Trusted Publishing workflow + provenance verify path |

Release readiness is **measured green when**: local `verify-public` PASS + GitHub CI green + GitHub smoke green + tag/notes published + (if claiming pip) Trusted Publishing success with non-null provenance.
