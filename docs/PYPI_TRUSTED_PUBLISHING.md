# PyPI Trusted Publishing (HyoDo)

SSOT for the supply-chain seal: **OIDC only**, no long-lived PyPI API token in GitHub secrets.

## Components

| Layer | Name / value |
|---|---|
| GitHub workflow | `.github/workflows/publish.yml` |
| GitHub Environment | `pypi` (required reviewers recommended) |
| PyPI project | `hyodo` |
| Trigger | annotated tag `vX.Y.Z` matching `VERSION` |
| Publish action | `pypa/gh-action-pypi-publish` (OIDC + attestations) |
| Post-publish | `scripts/release/verify-pypi-release.py --require-provenance --install-smoke` |

## One-time PyPI setup (package owner account)

Owner of `hyodo` on PyPI (historically `afo`) must add a Trusted Publisher:

1. Open [hyodo Managing → Publishing](https://pypi.org/manage/project/hyodo/settings/publishing/)
2. Under **GitHub**, add:

| Field | Value |
|---|---|
| Owner | `lofibrainwav` |
| Repository name | `HyoDo` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

3. Save. The publisher must match the workflow file name and environment **exactly**.

## One-time GitHub Environment

Environment name: **`pypi`**

Recommended protection:

- Required reviewers: repository owner/maintainers
- No branch restriction that blocks tags (tag pushes must be allowed to use the environment)
- Do **not** store `TWINE_PASSWORD` / `PYPI_API_TOKEN` in the environment

Create or update via UI: Settings → Environments → `pypi`.

## Release flow (after main is green)

```bash
# 1) VERSION SSOT already bumped on main; CI green
VERSION="$(tr -d '[:space:]' < VERSION)"

# 2) Annotated tag only (immutable preferred; no retag)
git tag -a "v$VERSION" -m "HyoDo v$VERSION"
git push origin "v$VERSION"

# 3) Approve the GitHub Environment deployment if required

# 4) Workflow builds → OIDC publish → provenance verify → install smoke
```

Manual recovery (existing tag only):

```text
Actions → Publish to PyPI → Run workflow → tag = vX.Y.Z
```

## Success criteria (measure, do not assume)

```bash
python scripts/release/verify-pypi-release.py \
  --version "$(tr -d '[:space:]' < VERSION)" \
  --require-provenance \
  --install-smoke
```

Expected:

1. PyPI version exists, non-yanked, wheel + sdist present
2. Provenance non-null for **both** artifacts (integrity / attestation API)
3. `pip install --no-cache-dir hyodo==$VERSION` → `hyodo --version` matches

## Explicitly removed

- Manual `twine upload` with long-lived API token as the **supported** path
- Documenting `/tmp/hyodo-twine.env` as the release procedure

Emergency break-glass (token upload) is outside this SSOT and requires Commander approval + post-incident rotation.
