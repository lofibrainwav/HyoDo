# HyoDo Release readiness checklist

This checklist blocks a public release until the package, CLI, and workflow path are verified.

## Current target

- Target version: see `VERSION` (currently `3.1.1`)
- Release issue: <https://github.com/lofibrainwav/HyoDo/issues/1>
- Public package path only — `afo_core/` is advisory, not a release blocker

## Pre-release gates (local)

```bash
bash scripts/verify-public.sh
python scripts/release/check_version_sync.py
```

Expected: exit 0, version synchronized, sdist without `afo_core`, CLI smoke green.

### Documentation

- [x] `README.md` leads with model-agnostic quality gate (CLI + CI)
- [x] `CHANGELOG.md` has a section for the target version
- [x] `QUICK_START_SIMPLE.md` / `CONTRIBUTING.md` use HYOGOOK V5
- [x] `SECURITY.md` + `docs/SECURITY_SURFACE.md` document public vs advisory tree
- [x] No public claim language that implies automatic merge/write authority
- [x] No PyPI badge until PyPI publish is confirmed live

### Runtime and package

- [x] Wheel installs and imports `hyodo`
- [x] `hyodo --version` matches `VERSION`
- [x] `hyodo score` emits REVIEW_SIGNAL (not approval)
- [x] `hyodo safe` flags secret fixtures
- [x] Sdist does not ship `afo_core`

### CI and smoke (GitHub Actions)

- [x] `.github/workflows/ci.yml` public gates (Truth / Goodness / Beauty)
- [x] `.github/workflows/smoke.yml` build + twine + wheel + CLI + API
- [ ] Latest `main` CI run is green (measure before tag)
- [ ] Latest `main` smoke run is green (measure before tag)

## Release steps (after green CI + smoke on main)

1. Confirm Actions are enabled and latest main runs are green.

2. Tag and push (example for 3.1.1):

   ```bash
   git tag -a v3.1.1 -m "HyoDo v3.1.1"
   git push origin v3.1.1
   ```

3. Create GitHub Release `v3.1.1` with notes from `CHANGELOG.md` `[3.1.1]`.

4. **PyPI publish is separate and optional.** Measure first:

   ```bash
   # Live status (do not assume)
   curl -s https://pypi.org/pypi/hyodo/json | python -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"
   ```

   Current measured status (2026-07-16): PyPI `hyodo` is **3.0.1** only.
   Do **not** add PyPI badges until a newer version is confirmed live.

5. Demo recording uses `docs/DEMO_READY_CHECKLIST.md` **after** this checklist is green.

## Decision log

| Date | Version | Decision |
|------|---------|----------|
| 2026-05 | 3.1.0 | Tag/Release existed; later main advanced past that snapshot |
| 2026-07-16 | 3.1.1 | Public readiness: security track closed, packaging hygiene, clutter removed |

Release readiness is **measured green when**: local `verify-public` PASS + GitHub CI green + GitHub smoke green + tag/notes published. PyPI is not required for GitHub release readiness.
