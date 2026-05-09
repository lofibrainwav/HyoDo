# HyoDo v3.1.0 Release Checklist

This checklist blocks the final public release until the package, CLI, and workflow path are verified.

## Current release candidate

- Target version: `3.1.0`
- Candidate commit: `8688a4bc0a95b3375937ec706face9edda2914a1`
- Release issue: <https://github.com/lofibrainwav/HyoDo/issues/1>

## Pre-release gates

### Documentation

- [x] `README.md` identifies HyoDo as a public OSS Claude Code workflow kit
- [x] `CHANGELOG.md` includes v3.1.0 notes
- [x] `QUICK_START_SIMPLE.md` uses HYOGOOK V5
- [x] `CONTRIBUTING.md` uses HYOGOOK V5
- [x] `SECURITY.md` supports v3.1.x and avoids invalid security contact info

### Runtime and package safety

- [x] `hyodo safe` tuple-shape runtime bug fixed
- [x] HYOGOOK V5 scoring APIs exported from `hyodo.__all__`
- [x] scoring inputs are clamped for numeric safety
- [x] CLI supports repository mode and standalone package mode
- [x] `hyodo check` no longer assumes `packages/afo-core` always exists

### CI and smoke validation

- [x] `.github/workflows/ci.yml` fixed for checkout behavior
- [x] `.github/workflows/smoke.yml` added
- [x] smoke workflow validates shell syntax, package build, wheel install, CLI help, and package import
- [ ] GitHub Actions run is visible for the release candidate
- [ ] smoke workflow is green
- [ ] CI workflow is green

## Required manual release steps

Do not perform these until the smoke workflow is visibly green.

1. Confirm GitHub Actions are enabled:
   - `Settings → Actions → General`
   - Allow all actions and reusable workflows
   - Approve any pending first workflow run

2. Run the smoke workflow manually if needed:
   - `Actions → HyoDo Smoke Test → Run workflow`

3. After green smoke and CI, create tag:

   ```bash
   git tag -a v3.1.0 8688a4bc0a95b3375937ec706face9edda2914a1 -m "HyoDo v3.1.0"
   git push origin v3.1.0
   ```

4. Create GitHub Release `v3.1.0` with notes from `CHANGELOG.md`.

5. Verify package build locally or in CI:

   ```bash
   python -m pip install --upgrade pip build twine
   python -m build
   python -m twine check dist/*
   pip install dist/*.whl
   hyodo --help
   hyodo safe
   python -c "import hyodo; print(hyodo.__version__)"
   ```

6. Publish to PyPI only after the package check passes.

7. Add PyPI badges to `README.md` only after PyPI confirms the package is live.

## Release decision

Current state: **release candidate, not final release**.

Reason: workflow files are present, but the release candidate still needs a visible green GitHub Actions run before final tag/release.
