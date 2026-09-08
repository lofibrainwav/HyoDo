# HyoDo Security Surface

This document defines the security boundaries of the public `hyodo` package,
CLI, and CI/release pipeline. It reflects only what is present in this
repository today.

## What ships

- Public package: `hyodo/`, root `pyproject.toml` — release gate: Yes
- Public tests: `tests/` — release gate: Yes (`pytest`)
- Release/verify scripts: `scripts/` — release gate: Yes

## Thin runtime dependency surface

`pyproject.toml` declares three runtime dependencies for the `hyodo` package
on Python 3.11+, plus the `tomli` backport on Python 3.10:

```text
jsonschema>=4.18,<5
typer>=0.9.0
rich>=13.0.0
tomli>=1.2.0; python_version < "3.11"
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
  *that* environment — so the SBOM contains `jsonschema`, `typer`, `rich`,
  their transitive closure, and Python 3.10's conditional `tomli`; it never
  contains the generator (`cyclonedx-bom`) or dev/test/lint tooling. This
  scope is enforced in-process (`assert_public_scope`, which fails the run)
  and by tests. Inventorying the dev environment directly would be wrong —
  it would pull the whole dev toolchain in.
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
  venv (installing the wheel and its runtime dependencies) may use the
  network; when that is not possible, the gate SKIPs.
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

Inside a git repository `hyodo safe` with no path scans the working diff
only; `hyodo safe . --max-files 0` scans the tree.

### Scan scope and coverage are named, not inferred

Both text and `--json` output carry two fields that state exactly what was
scanned, so a reader never has to parse the free-text `source` string to
find out:

- `scope` — which corpus was scanned:
  - `diff` — the `git diff HEAD` corpus (the default inside a git repo with
    pending changes)
  - `status` — the `git status --porcelain` fallback (used when the diff is
    empty, e.g. only untracked files)
  - `file` — a single file was named on the command line
  - `directory` — a directory was named on the command line
  - `external` — an external scanner (`--scan gitleaks` / `trufflehog` /
    `all`) ran instead of the built-in pattern scan
  - `none` — no corpus was available at all (missing path, unreadable
    target, or a git repo with nothing to diff or list)
- `coverage` — how much of that scope was actually read:
  - `FULL` — every scannable file in the corpus was read (`scanned_files ==
    total_scannable`, both known, and greater than zero)
  - `PARTIAL` — some but not all of the corpus was read (for example a
    `--max-files` cap was hit, or a diff contained sections without hunks)
  - `UNOBSERVED` — the corpus was missing, unreadable, or errored, or the
    counts are unknown; for `external`, this also covers a scanner that
    failed to run. Unobserved is never reported as a clean pass.

The text output prints this as a line right after `source:` —
`Scope: <scope> · Coverage: <coverage> (<scanned>/<total> files)` — and,
when `scope` is `diff` or `status`, a follow-up hint suggesting a directory
scan. `--quiet` suppresses both lines; `--audience` lenses never change the
underlying `scope` or `coverage` values.

### `--scan gitleaks` / `--scan trufflehog` / `--scan all`

`hyodo safe --scan gitleaks` shells out to a locally installed `gitleaks`
binary instead of the built-in regex patterns. gitleaks 8.x removed the
older `--format json` flag; HyoDo invokes it as `detect --report-format
json --report-path -` (report streamed to stdout) so it stays compatible
with 8.x releases. Before scanning, HyoDo runs `gitleaks version` as a
positive control (10s timeout): if the binary does not answer with a
version string, the scan is reported as a high-severity `gitleaks_failed`
finding rather than being treated as clean, and the actual scan is not
attempted. On success the reported `source` includes the detected version,
for example `gitleaks:scan (8.30.1)`. `--scan trufflehog` runs the same
positive control before invoking `trufflehog git file://<path> --json`:
HyoDo runs `trufflehog --version` first (accepting the version string on
either stdout or stderr, since this differs across trufflehog releases). A
binary that does not answer with a version-looking string (digits and dots)
is reported as a high-severity `trufflehog_failed` finding and the scan is
not attempted, mirroring the `gitleaks_failed` control above. On success the
reported `source` includes the detected version, for example
`trufflehog:scan (3.63.2)`. `--scan all` (both tools merged) behaves as
documented in `hyodo safe --help`.

## Agent event ledger is opt-in evidence, not a runtime interceptor

`hyodo event` / `hyodo policy` implement an **opt-in FDE evidence spine**:

- Events are caller-supplied JSON (`hyodo.agent-event/v1`); HyoDo does not
  monkey-patch model SDKs or automatically intercept tool calls.
- Default ledger storage is **digest-only** (`.hyodo/agent-events.jsonl`).
  Full prompt/tool bodies are written only with `--full-body`. See
  [`docs/FULL_BODY.md`](FULL_BODY.md) for who may enable it, that the
  ledger is not rotated or redacted, and that a client cannot
  self-upgrade. `hyodo mcp serve` has no `--allow-full-body`.
- Policy DENY is recorded for audit; **the agent runtime must enforce stop**.
- Missing or invalid policy is **unobserved** (exit 2), never silent ALLOW.
- No network export, encryption, or cloud telemetry in this surface.

Do not claim "all agent tool calls are intercepted" or "encrypted audit
trail" unless those layers are implemented and tested separately.

## Optional MCP adapter

The optional `hyodo[mcp]` extra provides local stdio and explicit HTTP MCP
transports that delegate to the existing HyoDo CLI. The core `pip install
hyodo` dependency set does not include the MCP SDK.

- `hyodo mcp stdio --root PATH` creates no network listener.
- `hyodo mcp serve --bind loopback` listens only on `127.0.0.1`.
- `hyodo mcp serve --bind tailscale --bind-ip 100.x.x.x --token TOKEN` accepts
  only a supplied address in `100.64.0.0/10`. A missing or blank token refuses
  before the server starts; authenticated requests require exact bearer
  matching.
- Tools are locked to the configured host workspace; relative policy paths
  cannot escape it.
- `safe`, `check`, `event record`, and `policy check` retain their CLI exit
  contracts; a policy that cannot be observed remains exit `2`.
- No public `0.0.0.0` listener is supported. A Vercel gate executor remains
  out of scope. Second-device tailnet operation is an operator dogfood step,
  not a package claim until observed.
- `https://mcp.hyodo.app/mcp` and ChatGPT are contract-only,
  `UNOBSERVED`, and not equivalent to `hyodo mcp stdio`. See
  [`docs/M5_REMOTE_CONNECTOR_CONTRACT.md`](M5_REMOTE_CONNECTOR_CONTRACT.md).

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
the runtime dependency list is intentionally short, the expected steady-state
alert volume is low; any alert against the public surface is expected to be
triaged and patched promptly, not deferred.

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
- [`docs/CLAIMS.md`](CLAIMS.md) — what public pages do not claim
- [`docs/FULL_BODY.md`](FULL_BODY.md) — full-body ledger consent and retention
- [`docs/M5_REMOTE_CONNECTOR_CONTRACT.md`](M5_REMOTE_CONNECTOR_CONTRACT.md)
  — remote MCP is contract-only, not a shipped path next to stdio
- [`.github/dependabot.yml`](../.github/dependabot.yml) — update scope
