# HyoDo Release readiness checklist

This checklist blocks a public release until the package, CLI, and workflow path are verified.

## Current target

- Target version: see `VERSION` (SSOT; do not hardcode)
- Public package path only — the sdist ships only the `hyodo` package
- Truth contracts (v3.1.7+): `check` zero-gates → exit 2; `safe --strict` high → exit 1
- Supply-chain (v3.1.8+): PyPI via Trusted Publishing only — see `docs/PYPI_TRUSTED_PUBLISHING.md`
- Release-tag trust: new public releases require an annotated tag that GitHub reports as verified

## Pre-release gates (local)

```bash
bash scripts/verify-public.sh
python scripts/release/check_version_sync.py
```

Expected: exit 0, version synchronized, sdist limited to the public package, CLI smoke green
(including empty-tree `check` exit 2 and `safe --strict` high-fixture exit 1).

### Documentation

- [ ] `README.md` leads with model-agnostic quality gate (CLI + CI) and honest check scope
- [ ] `CHANGELOG.md` has a section for the target version
- [ ] `QUICK_START.md` / `CONTRIBUTING.md` use HYOGOOK V5 + review-signal language
- [ ] `SECURITY.md` + `docs/SECURITY_SURFACE.md` document the public package security surface
- [ ] No public claim language that implies automatic merge/write authority
- [ ] Exit-code contracts for `check` / `safe` documented in README or quick start
- [ ] PyPI badge only if live index matches the release claim

### Runtime and package

- [ ] Wheel installs and imports `hyodo`
- [ ] `hyodo --version` matches `VERSION`
- [ ] `hyodo score` emits REVIEW_SIGNAL (not approval)
- [ ] `hyodo safe` flags secret fixtures; `--strict` exits 1 on high findings
- [ ] Empty/non-HyoDo `hyodo check` exits 2 (not false green)
- [ ] Sdist ships only the public `hyodo` package

### CI and smoke (GitHub Actions)

- [ ] `.github/workflows/ci.yml` public gates (Truth / Goodness / Beauty)
- [ ] Public `tests/` pytest is a **release blocker** (not `continue-on-error`)
- [ ] `.github/workflows/smoke.yml` build + twine + wheel + CLI + empty-check exit 2
- [ ] Latest `main` CI run is green (measure before tag)
- [ ] Latest `main` smoke run is green (measure before tag)

## Release steps (after green CI + smoke on main)

1. Confirm Actions are enabled and latest main runs are green.

2. Create and locally verify the synchronized release tag. New release tags are
   immutable, annotated, and signed; do not retag an existing version:

   ```bash
   VERSION="$(tr -d '[:space:]' < VERSION)"
   git tag -s "v$VERSION" -m "HyoDo v$VERSION"
   git tag -v "v$VERSION"
   git push origin "v$VERSION"
   ```

   The signing identity must be associated with the GitHub account so GitHub
   displays the annotated tag as **Verified**. The publish workflow independently
   checks the GitHub tag object and refuses lightweight, unsigned, invalid, nested,
   or unexpectedly-targeted tags. Tag push alone does not publish to PyPI.

3. Create GitHub Release `v$VERSION` as a **draft** and add reviewed notes from
   the matching `CHANGELOG.md` section. Do not publish the draft yet.

4. Run **HyoDo Release Evidence** for `v$VERSION`.

   - The workflow re-verifies the exact signed tag before generating evidence.
   - It generates the CycloneDX SBOM plus portable SHA-256 receipt from that tag.
   - It attaches assets only while the release is still a draft; existing complete
     assets are verified without replacement, and partial evidence fails closed.
   - It downloads the durable assets and verifies byte equality plus the checksum.
   - A successful run intentionally leaves the release in draft state.

   This draft-first sequence remains compatible with GitHub immutable releases,
   which do not allow assets to be added or replaced after publication.

5. **Publish the draft GitHub Release manually** after the evidence run is green.
   The human publication event is intentional: Actions performed with the repository
   `GITHUB_TOKEN` do not recursively trigger ordinary downstream workflows.

6. The `release: published` event starts **PyPI Trusted Publishing** automatically.

   - The build job re-verifies the signed tag and main ancestry.
   - It requires the published GitHub Release to contain both durable SBOM assets.
   - It downloads the assets and checks the SHA-256 receipt before building.
   - PyPI publication uses OIDC only; no long-lived token is stored.
   - The post-publish job verifies provenance and an install smoke test.
   - Manual `workflow_dispatch` is recovery-only and enforces the same Release gate.

7. Demo recording uses `docs/DEMO_READY_CHECKLIST.md` **after** this checklist is green.

## Decision log

| Date | Version | Decision |
|------|---------|----------|
| 2026-05 | 3.1.0 | Tag/Release existed; later main advanced past that snapshot |
| 2026-07-16 | 3.1.4 | GitHub release published; PyPI intentionally separate at the time |
| 2026-07-16 | 3.1.5 | Pre-demo surface polish; later PyPI 3.1.5 published |
| 2026-07-16 | 3.1.6 | Truth Patch on GitHub + tag `v3.1.6` + PyPI 3.1.6 (false-green gates removed) |
| 2026-07-16 | 3.1.7 | format gate + safe scan exit 2 + path-stable tests; tag/PyPI 3.1.7 |
| 2026-07-16 | 3.1.8 | Supply-chain seal: Trusted Publishing workflow + provenance verify path |
| 2026-07-19 | 3.2.0 | safe --json + check honesty hardening; SBOM exception split |
| 2026-07-20 | 3.2.1 | Pyright interpreter pin for venv import stability |
| 2026-07-20 | 3.3.0 | Philosophy V6: `hyo` restored; `loyalty` deprecated until 4.0.0 |
| 2026-07-20 | 4.0.0 | Philosophy V6 complete: legacy approval surfaces removed |
| 2026-07-20 | 4.0.1 | Score honesty: required pillars, flag conflicts, safe path/line |
| 2026-09-03 | 4.11.0 | MCP access ledger + agent-rules opt-in (M4 complete, Issue #95) |
| 2026-09-03 | 4.10.0 | `hyodo mcp doctor` diagnostic command (M4 slice 1) |
| 2026-09-03 | 4.9.0 | MCP v1/v2 dual-major compatibility + v1 CI gate; twine>=7 fix |

Release readiness is **measured green when**: local verification passes, main CI and smoke are green,
the verified tag has durable release SBOM evidence, the GitHub Release is published, and any PyPI
claim has Trusted Publishing success with non-null provenance.
