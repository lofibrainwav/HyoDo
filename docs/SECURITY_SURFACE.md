# HyoDo Security Surface

This document defines the security boundaries of the public `hyodo` package,
CLI, and CI/release pipeline. It reflects only what is present in this
repository today.

## What ships

- Public package: `hyodo/`, root `pyproject.toml` — release gate: Yes
- Public tests: `tests/` — release gate: Yes (`pytest`)
- Release/verify scripts: `scripts/` — release gate: Yes

## Thin runtime dependency surface

`pyproject.toml` declares exactly two runtime dependencies for the `hyodo`
package:

```text
typer>=0.9.0
rich>=13.0.0
```

Everything else (`pytest`, `ruff`, `pyright`, `build`, `twine`, `PyYAML`, ...)
is in the `dev` optional-dependency group and is never installed for an end
user running `pip install hyodo`. Keeping this list short and reviewed is the
primary control against a large third-party attack surface: fewer transitive
packages means fewer places a supply-chain issue can enter.

Verify locally:

```bash
pip install -e ".[dev]"
hyodo check
hyodo safe
python -m pytest tests -q
```

## Package contents are scoped to the public surface

`pyproject.toml` uses hatchling's `only-include` to restrict what actually
lands in the sdist and wheel:

```bash
python -c "
import tomllib
print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['hatch']['build'])
"
```

This means the distributed artifact contains the `hyodo` package (plus
declared metadata files such as `README.md` and `LICENSE`) and nothing else
from the repository. Reviewers can confirm this directly by building and
inspecting the artifact:

```bash
python -m build
python -m tarfile -l dist/hyodo-*.tar.gz
unzip -l dist/hyodo-*.whl
```

## Public SBOM (Eternity gate)

The 4th `hyodo check` gate ("Eternity") emits a CycloneDX SBOM of the public
surface via `scripts/generate_sbom.py`.

- **Scope.** The generator builds the public wheel and installs it into a
  clean throwaway virtualenv created **without pip** (so the venv bootstrap
  seeds `pip`/`setuptools`/`wheel` are never inventoried), then inventories
  *that* environment — so the SBOM contains `typer`, `rich`, and their
  transitive closure, and never the generator (`cyclonedx-bom`) or dev/test/
  lint tooling. This scope is enforced in-process (`assert_public_scope`,
  which fails the run) and by tests. Inventorying the dev environment
  directly would be wrong — it would pull the whole dev toolchain in.
- **Gate behavior.** The Eternity gate is offline-safe and does not regress
  `hyodo check`: a **scope violation** (SBOM produced but mis-scoped) is a
  real defect and **FAILs** (exit 2); only the generator's *defined*
  **environment failure** (offline, build/venv cannot be provisioned)
  **SKIPs** (exit 3) — the same honest "not executed" posture as when the
  script is absent. Any other, **unexpected** generator failure (a bug,
  corrupt output, an unhandled exception → exit 1) **FAILs** rather than
  being masked as a SKIP, so the gate can never silently pretend it ran.
- **Offline.** "Offline" means the *generation* step (rendering the SBOM
  from installed metadata) makes no network calls. Provisioning the clean
  venv (installing the wheel + `typer`/`rich`) may use the network; when
  that is not possible, the gate SKIPs.
- **Reproducibility.** Output is generated with `--output-reproducible`, so
  volatile fields (`serialNumber`, `metadata.timestamp`) are stripped; the
  stable contract is the component (name, version) set. CI runs the real
  pipeline twice and asserts this set is identical.
- **CI.** A dedicated advisory job (`Eternity - Public SBOM`) generates and
  uploads `dist/sbom.cyclonedx.json` as an artifact and runs the real
  scope+reproducibility check. It is `continue-on-error` (observe first) and
  is not in the release-gate `needs`; it does not yet block the release.

Reproduce locally:

```bash
pip install -e ".[dev]"          # provides cyclonedx-bom
python scripts/generate_sbom.py  # writes dist/sbom.cyclonedx.json
```

## `hyodo safe` is early warning, not full SAST

`hyodo safe` is a fast, offline, pattern-based scanner. It flags obvious
risk signals (for example hardcoded-secret-shaped strings or dangerous
call patterns) in the current working tree. It is **not**:

- a full static-analysis (SAST) engine,
- a comprehensive secret-scanning service,
- a substitute for `hyodo check`, dependency scanning, or human review.

Treat a clean `hyodo safe` run as "no obvious red flags found," not as
"verified secure." Run it with:

```bash
hyodo safe
```

## Agent event ledger is opt-in evidence, not a runtime interceptor

`hyodo event` / `hyodo policy` implement an **opt-in FDE evidence spine**:

- Events are caller-supplied JSON (`hyodo.agent-event/v1`); HyoDo does not
  monkey-patch model SDKs or automatically intercept tool calls.
- Default ledger storage is **digest-only** (`.hyodo/agent-events.jsonl`).
  Full prompt/tool bodies are written only with `--full-body`.
- Policy DENY is recorded for audit; **the agent runtime must enforce stop**.
- Missing or invalid policy is **unobserved** (exit 2), never silent ALLOW.
- No network export, encryption, or cloud telemetry in this surface.

Do not claim "all agent tool calls are intercepted" or "encrypted audit
trail" unless those layers are implemented and tested separately.

## MCP connector (design only until implemented)

Optional MCP adapter and remote connector URLs are specified in
[`HYODO_MCP_CONNECTOR_DESIGN.md`](HYODO_MCP_CONNECTOR_DESIGN.md). Until that
code ships:

- The public package does **not** open network MCP listeners.
- Multi-machine access is **not** claimed.
- When shipped: default remains stdio/local; private-net bind requires an
  explicit token; public `0.0.0.0` is out of v1 scope; Vercel is not a gate
  executor.

## Release pipeline: Trusted Publishing + provenance

Releases to PyPI are handled by `.github/workflows/publish.yml` using PyPI
**Trusted Publishing** (OIDC) — there is no long-lived PyPI API token stored
as a repository secret. The workflow:

1. Builds the sdist/wheel from the tagged commit.
2. Publishes via the OIDC-based trusted-publisher flow
   (`pypa/gh-action-pypi-publish`).
3. Generates build provenance/attestation for the published artifacts.

This means a PyPI release is cryptographically traceable back to the exact
GitHub Actions run and workflow file that produced it, and does not depend
on a credential that could leak or be reused outside CI. See
[`docs/PYPI_TRUSTED_PUBLISHING.md`](PYPI_TRUSTED_PUBLISHING.md) for the
mechanics, and verify a specific release with:

```bash
python scripts/release/verify-pypi-release.py
```

`scripts/release/check_version_sync.py` additionally checks that `VERSION`,
`pyproject.toml`, and any other declared version sources agree before a tag
is cut, so a release can't ship with mismatched version metadata.

## CI checks (`.github/workflows/ci.yml`, `smoke.yml`)

- `ci.yml` installs the package with `pip install -e ".[dev]"`, then runs
  `ruff check`, `pyright`, and `pytest tests -q` against the public surface
  only.
- `smoke.yml` installs the built package and exercises the `hyodo` CLI
  entry points end-to-end, catching packaging/entry-point regressions that
  unit tests alone would miss.
- `scripts/verify-public.sh` and `scripts/demo-dry-run.sh` provide local
  equivalents of the CI checks a contributor can run before pushing.

## Dependabot scope

`.github/dependabot.yml` tracks the root `pyproject.toml` (the public
package's dependency graph) and the GitHub Actions workflow files. Because
the runtime dependency list is intentionally short (`typer`, `rich`), the
expected steady-state alert volume is low; any alert against the public
surface is expected to be triaged and patched promptly, not deferred.

## Secrets

- Do not commit secrets, tokens, or credentials to this repository.
- The PyPI release path uses OIDC Trusted Publishing specifically to avoid
  needing a long-lived publish token as a stored secret (see above).
- Report suspected credential leaks per [`SECURITY.md`](../SECURITY.md).

## Verification commands

```bash
pip install -e ".[dev]"
hyodo check
hyodo safe
python -m pytest tests -q
ruff check hyodo/
pyright hyodo
python scripts/generate_sbom.py
python scripts/release/check_version_sync.py
```

## Related docs

- [`SECURITY.md`](../SECURITY.md) — reporting and keyword safety gates
- [`docs/PYPI_TRUSTED_PUBLISHING.md`](PYPI_TRUSTED_PUBLISHING.md) — OIDC
  publish flow details
- [`docs/EXTERNAL_CLAIM_AUDIT.md`](EXTERNAL_CLAIM_AUDIT.md) — audit of
  externally-facing claims
- [`.github/dependabot.yml`](../.github/dependabot.yml) — update scope
