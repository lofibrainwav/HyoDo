# Third-party security remediation plan

Status: **OPEN — remediation plan only**
Assessment date: **2026-09-13 PT**
Assessment style: **read-only, non-destructive, external-first review**

## Current product boundary

HyoDo's public product is the Python package, CLI, and MCP adapter. Docker and
the optional Compose service stack are not required for installation, CLI
gates, MCP use, or public release, and are retired from the live product
surface. The Docker references below are retained as historical remediation
evidence only; they are not current setup instructions or release gates.

This document records how HyoDo should address the findings from a third-party
view of the repository, the published Python package, and `https://hyodo.app`.
It is a remediation plan, not evidence that the fixes have already shipped.

## 1. Scope and decision rule

The review covered:

- the current HyoDo checkout and its tracked Git history;
- `docker-compose.minimal.yml`, `Dockerfile`, release workflows, and security
  documentation;
- the public GitHub repository, PyPI metadata, and `hyodo.app` HTTP surface;
- public static-site JavaScript and the local MCP/dashboard security boundary;
- read-only `gitleaks`, `bandit`, `npm audit`, and focused test observations.

The following are separate proof axes and must remain separate during repair:

1. source/configuration correctness;
2. test and static-analysis evidence;
3. built artifact and container evidence;
4. GitHub release/CI evidence;
5. PyPI publication and clean-install evidence;
6. live `hyodo.app` header and route evidence.

An item is **CLOSED** only when its stated acceptance criteria and its
corresponding proof receipt exist. A source change alone is **IMPLEMENTED**, not
**VERIFIED**.

## 2. Executive remediation order

| Priority | Finding | Required disposition |
| --- | --- | --- |
| P1 conditional | Optional Compose stack exposes unauthenticated Redis and a fixed PostgreSQL development password | Harden before recommending the stack for any non-isolated host |
| P1 investigation | Historical `gitleaks` matches include removed `afo_core` material | Preserve the redacted 2026-09-13 snapshot and current `.gitleaksignore` dispositions; keep C2/C3 as explicit historical residuals |
| P2 | Docker image installs floating dependencies | Pin or lock build inputs and publish a reproducible image procedure |
| P2 | Security and public-state documentation trails the live package | Establish one version/release-status source and update public pages |
| P2 | Local verification environment could not execute all focused tests | Re-run in a clean supported environment and attach the receipt |
| P2 | Public verifier used a brittle compressed sdist-size ceiling | Verify declared archive scope and unsafe paths instead of compressed size |
| P2 security UX | BYOG first-use trust previously executed an unreviewed command set | Require interactive approval or explicit automation pre-approval before any user gate runs |
| P3 hardening | Public CSP still allows `'unsafe-inline'` and broad HTTPS connections | Tighten after the current static site remains functionally equivalent |
| P2 governance | Remediation work is not yet represented on the public tracking surface | Publish this register through a reviewed PR or linked issue and keep dispositions linked to receipts |
| P3 release hardening | The latest GitHub Release is not immutable | Protect release/tag mutation or document an approved immutable release procedure |

The remote MCP result is not a vulnerability: `https://mcp.hyodo.app/mcp`
currently returns `404 DEPLOYMENT_NOT_FOUND`, which is consistent with the
repository's documented `CONTRACT ONLY / UNOBSERVED` boundary. The remediation
must preserve that honesty unless a real authenticated service is separately
deployed and tested.

## Current execution status

| Item | Status | Evidence boundary |
| --- | --- | --- |
| Compose default exposure | RETIRED | The Compose surface is no longer part of the live product; historical YAML/runtime evidence remains recorded below |
| Historical credential disposition | RECONCILED / HISTORICAL RESIDUAL | 13 narrow test/fixture/non-secret baselines are documented; C1 is revoked; C2/C3 are decommissioned external historical credentials with unavailable owners and no current validation control. None is treated as an active credential |
| Version/support-policy reconciliation | IMPLEMENTED LOCALLY / DEPLOYMENT-UNOBSERVED | Current-state, roadmap, security, capabilities, package metadata, and site source claims now name public release `4.20.0`; public deployment readback is separate |
| Docker image boundary | IMPLEMENTED LOCALLY / BUILD UNOBSERVED | Runtime-only install, non-editable package install, reduced build context, and lock-derived exact runtime requirements are encoded; image build, base-image digest, and reproducibility receipt remain unobserved |
| Clean security verification | VERIFIED IN ISOLATED ENVIRONMENT / HOST GLOBAL AUDIT UNOBSERVABLE | Isolated Python 3.12 environment: `1499 passed, 7 skipped`; `ruff`, `pyright`, `pip-audit --local`, package build, scope, wheel install smoke, CLI smoke, and claim regression passed. A later host-global `pip-audit` attempt could not start because that environment lacks `certifi`; it is not counted as a vulnerability result |
| CI secret/dependency scan | VERIFIED ON REMOTE MAIN / REQUIRED | SHA-pinned `security.yml` runs full-history gitleaks, verifies the lock-derived runtime export, audits that exact set with `pip-audit`, and reviews pull-request dependency changes; required contexts include the historical secret scan and runtime dependency audit |
| CI action/dependency maintenance | VERIFIED ON REMOTE MAIN | Site and security workflow actions are SHA-pinned; remote `main` contains the merged site hardening and security workflow |
| Public remediation tracking | IMPLEMENTED LOCALLY / NOT PUBLISHED | The register exists locally; the fresh remote readback found no open issue or PR dedicated to this remediation |
| GitHub release immutability | OBSERVED RESIDUAL | Public `v4.19.5` reports `immutable: false`; signed tag and artifact provenance are separate evidence and do not establish release-record immutability |
| Public sdist scope gate | IMPLEMENTED_AND_VERIFIED_LOCALLY | `verify-public.sh` now delegates archive-scope validation to `verify_sdist_scope.py`; a 512,954-byte sdist passed with 199 members and no `afo_core` |
| Site dependency/build verification | PRODUCTION HEADER VERIFIED / ARTIFACT READBACK SEPARATE | `npm ci` previously reported 0 vulnerabilities; local build/browser evidence remains separate, while a fresh 2026-09-14 production readback returned `200` with strict same-origin CSP on `/` and `/docs/quickstart/` |

### Remote governance readback

The current public `main` was read back at commit
`38830d7bf98a9ea476165b214c2f3412c4a8b119` on 2026-09-14 PT. The classic
branch-protection endpoint reports required status checks for the Python truth
gates, goodness/beauty gates, install smoke, integrity score, historical secret
scan, and runtime dependency audit; it also reports force-push and
branch-deletion denial. Required approving review count is currently `0`, and
required signed commits are disabled. The rulesets endpoint returned an empty
list. Security scan enforcement is observed on remote `main`; the historical
findings themselves remain an independent owner-disposition hold.

The public site hardening from [PR #296](https://github.com/lofibrainwav/HyoDo/pull/296)
is merged and the corresponding Vercel production deployment is `READY`. A
fresh 2026-09-14 production readback also returned the strict CSP headers for
the root and representative docs route. This is evidence for the public header
surface only; it does not close the historical secret or Docker proof holds.

The fresh production readback on 2026-09-14 PT returned `200` for both `/` and
`/docs/quickstart/`. HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options:
DENY`, Referrer Policy, Permissions Policy, exact-origin CORS, and strict
same-origin CSP were present. The production header readback is separate from
local artifact/browser evidence and does not close the historical secret or
Docker proof holds. The local
post-build artifact has removed these classes of inline content.

### Public tracking and release mutability

As of the 2026-09-13 PT readback, the public repository had no open issues or
open pull requests for this remediation. The local register therefore remains
an implementation artifact until it is published through a reviewed PR or an
explicitly linked security issue. The latest public GitHub Release, `v4.19.5`,
reported `immutable: false`; the signed tag, artifact hashes, and PyPI
provenance remain valuable independent evidence, but they do not prove that
the GitHub release record cannot be changed.

The closure condition is not merely “documented”: the public tracking item
must link the exact source SHA, owner disposition receipt, and final external
readback. Until then, this lane is `IMPLEMENTED LOCALLY / NOT PUBLISHED`.

## 3. P1 conditional — harden the optional Compose stack

### Observed condition before repair

The retired `docker-compose.minimal.yml` previously published:

- Redis on host port `6379`, without authentication;
- PostgreSQL on host port `15432`;
- PostgreSQL credentials `hyodo` / `hyodo_dev` in the Compose file.

The comments described the services as optional, but the pre-repair
configuration was still unsafe when copied to a laptop on an untrusted network,
a shared development host, or a cloud VM. A development-only password is not a
boundary. The current YAML repair is recorded in the status table above; actual
Compose runtime readback remains unobserved because Docker is unavailable on
this workstation.

### Repair

1. Bind development ports to loopback explicitly, for example
   `127.0.0.1:6379:6379` and `127.0.0.1:15432:5432`.
2. Make the PostgreSQL password an operator-supplied environment variable and
   fail clearly when it is missing. Do not provide a usable default password.
3. Configure Redis authentication when Redis is enabled, or remove its host
   port publication and document container-network-only access.
4. Remove `container_name` unless there is a demonstrated need. Fixed names
   create collisions between users and concurrent test stacks.
5. Add a dedicated `docker-compose.dev.yml` if the extended services are not
   part of the public product. Keep the minimal public CLI path free of these
   services.
6. Update `QUICK_START.md` and the Compose comments with a warning that the
   stack is local development infrastructure, not a production deployment.

### Acceptance criteria

- `docker compose config` contains no fixed secret value.
- A default start exposes neither Redis nor PostgreSQL beyond loopback.
- Redis rejects an unauthenticated command when authentication is enabled.
- PostgreSQL accepts only the operator-supplied password.
- A clean host scan of the documented local configuration shows no public
  listener on `6379` or `15432`.
- The public CLI verification still passes without starting Compose services.

### Proof to retain

```text
docker compose config
docker compose ps
docker compose port redis 6379
docker compose port postgres 5432
git diff -- docker-compose.minimal.yml QUICK_START.md
```

Do not report this finding closed from a YAML review alone; verify the resolved
ports from the actual Compose configuration.

## 3A. P2 security UX — require explicit BYOG first-use approval

### Observed condition

`.hyodo/gates.toml` can contain arbitrary executable commands. The previous
trust-on-first-use behavior automatically recorded the first command-set
fingerprint and executed it, which protected against later drift but did not
protect a user running HyoDo against a newly cloned, unreviewed checkout.

### Repair

The execution path now requires an explicit decision before a new fingerprint
can reach `subprocess.run`:

1. Interactive use prints the exact command set and records approval only after
   the operator answers yes.
2. Non-interactive use reports `SKIP` and executes nothing unless
   `HYODO_GATES_TRUST_ALL=1` is explicitly present.
3. Previously approved fingerprints remain executable; changed fingerprints
   require a new approval.
4. Tests use marker files and isolated approval setup so “reported PASS” cannot
   be confused with actual command execution.

### Acceptance criteria

- A fresh non-interactive checkout cannot execute its BYOG commands silently.
- Interactive approval records the exact command-set fingerprint.
- An approved fingerprint executes normally and a changed fingerprint is not
  silently promoted to PASS.
- Documentation states that approval is execution permission, not a safety or
  merge authority decision.

## 4. P1 investigation — historical secret matches

### Observed condition

`gitleaks` scanned 603 commits and reported 16 matches. The current checkout
does not contain the old `afo_core` tree, but Git history contains paths such as
`afo_core/data/api_wallet.json`. The current redacted disposition source
separates 13 narrow test/fixture/non-secret baselines from three genuine
historical credentials: C1 was revoked, while C2/C3 belong to decommissioned
external consumers whose owners and validation endpoints are unavailable.
Those C2/C3 values remain permanently exposed historical residuals, not active
credentials.

The current redacted finding index is maintained in
[`docs/security/GITLEAKS_DISPOSITION.md`](security/GITLEAKS_DISPOSITION.md).
It includes the present-code `hyodo/cli/main.py:350` identifier match in the
accepted narrow historical baseline; an unexplained current or active finding
would remain actionable and would not be hidden by that baseline.

This is deliberately classified as **historical residual**, not as an active
credential and not as a clean-history claim. A deleted file remains available
to anyone with the repository history.

### Repair and investigation sequence

1. Inventory each historical match by commit, path, rule, and value type while
   redacting the value itself.
2. Ask the credential owner whether each value was synthetic, encrypted test
   data, or ever usable against a service.
3. If there is any uncertainty, rotate or revoke the corresponding credential
   before attempting history cleanup.
4. Search all reachable refs, tags, pull requests, and release artifacts again.
5. Add safe fixture handling only after confirming the fixtures are synthetic;
   do not silence a real secret with an allowlist.
6. If history rewriting is required, obtain explicit repository-owner approval,
   coordinate the force-update, and preserve a documented before/after object
   map. History rewriting is a separate authority decision from remediation.

### Acceptance criteria

- Every `gitleaks` result has a disposition: `synthetic`, `rotated`, or
  `removed-and-verified`.
- No live credential remains valid solely because it appeared in Git history.
- A fresh scan of the intended refs has zero unexplained findings.
- Public releases and source distributions contain no credential material.
- The report records the scan scope and does not print secret values.

### Proof to retain

```text
gitleaks detect --source . --redact --report-format json --report-path <receipt>
git log --all -- <historical-path>
python -m build
tar/list and wheel/list inspection of the public artifacts
```

The `<receipt>` must be stored outside the repository if it contains sensitive
metadata. Do not commit populated `.env` files or raw scanner output.

## 5. P2 — make the Docker build reproducible

### Observed condition before repair

The retired `Dockerfile` installed tools such as `ruff`, `pyright`,
`pytest`, `pydantic`, `typer`, and `rich` without version pins, then installs
the package from a source tree whose runtime dependencies use ranges. The
image also mixes runtime packaging with development verification tooling.

This created time-dependent builds and made it difficult to prove which code
and dependency set a user actually ran. The retired Dockerfile used a
multi-stage build, consumes the repository-owned lock export in
`requirements.runtime.txt`, and copies only the built wheel into the final
image; the base image and actual build remain separate unobserved axes.

### Repair

1. Decide whether the Dockerfile is a developer image or a runtime image; do
   not present one image as both.
2. For a developer image, install from the repository's lock/constraint source
   and pin the verification toolchain.
3. For a runtime image, install the built wheel rather than `pip install -e .`.
4. Use a multi-stage build so build tooling does not remain in the runtime
   image.
5. Pin the base image by digest in the release build path, or document the
   accepted tag-update policy and record the resolved digest in the receipt.
6. Generate and retain an SBOM for the image, separately from the Python public
   wheel SBOM.
7. Keep `requirements.runtime.txt` generated from `uv.lock` and fail CI if
   the export is stale. The local security workflow now contains this exact
   check.

### Acceptance criteria

- Rebuilding the same source revision with the same lock/constraints produces
  the same package dependency set.
- The runtime image contains no unnecessary test/lint toolchain.
- The image runs as the non-root `hyodo` user.
- A vulnerability scan is run against the resolved image, with findings
  dispositioned rather than ignored.
- The image's source revision, base digest, and dependency manifest are
  recorded together.

## 6. P2 — repair version and security-document drift

### Observed condition

At the time of the initial audit, the public package reported `4.19.5` while
the audit checkout contained `4.19.4`. Public documentation also contained
older claims such as:

- [`SECURITY.md`](../SECURITY.md) listing supported versions through `3.2.x`;
- [`docs/CURRENT_STATE.md`](CURRENT_STATE.md) describing `4.19.3` as the latest
  public package;
- site documentation carrying the `4.19.3` baseline language.

This is a security communication defect: a user may follow an obsolete support
table when deciding whether to patch or report a vulnerability.

### Repair

1. Define the release metadata source of truth: `VERSION` for source, PyPI for
   published availability, and a generated release-status page for public
   communication.
2. Update `SECURITY.md` to describe the actually supported policy, not a
   historical table copied from an earlier release.
3. Mark historical baselines explicitly as historical.
4. Add CI checks that fail when public version claims contradict the intended
   release boundary.
5. Add a release checklist item requiring live GitHub, PyPI, and site readback.
6. Keep unreleased `main`, local worktrees, PyPI, and `hyodo.app` status in
   separate fields; never infer one from another.
7. Publish this register through a reviewed PR or linked security issue, and
   record the GitHub release immutability decision as a separate governance
   receipt.

### Acceptance criteria

- A new user can identify the supported release line from `SECURITY.md`.
- The site, README, docs index, PyPI metadata, and release notes agree on the
  status they claim.
- Historical release notes remain immutable and clearly labeled.
- CI catches a stale version claim before release publication.

## 7. P2 — restore a clean verification environment

### Observed condition before repair

The original focused test run collected 53 tests and produced 51 passes, but
two MCP tests could not run because the ambient Python installation lacked
`certifi`. `pip-audit` failed for the same environmental reason. This was not
evidence of an application vulnerability, but it prevented a complete security
sign-off at that time. The clean isolated rerun is now recorded as
`VERIFIED LOCALLY` in the current execution status table.

### Repair

1. Run verification in a fresh Python 3.10+ virtual environment using the
   repository's documented development dependencies.
2. Disable unrelated global pytest plugins or run inside an isolated venv.
3. Run the focused MCP/dashboard/security tests and the complete public check.
4. Run dependency auditing against the actual project lock/constraints, not
   only the ambient interpreter.
5. Preserve the exact Python version, dependency resolution, Git SHA, and
   command exit codes in the receipt.

### Acceptance criteria

```text
bash scripts/verify-public.sh
python -m ruff check hyodo tests
python -m ruff format --check hyodo tests
python -m pyright hyodo
python -m pytest tests -q --tb=short
pip-audit --local
npm audit --omit=dev              # from site/
```

All commands must either pass or have an explicit, reviewed `UNOBSERVED`
disposition. A test run blocked by missing dependencies is not green.

## 8. P2 — make the installer release-bound

### Observed condition

The installer previously cloned the moving default branch and recommended an
editable development install. That path was weaker than the signed/tagged
release path used by the public package.

### Repair

`install.sh` and `install_interactive.sh` now default to the version tag from
the local `VERSION` file. An operator may explicitly provide `HYODO_REF` as a
release tag or a full commit SHA. Before installation continues, the installer
resolves the selected tag (or uses the supplied SHA), checks out the source,
and compares the resulting `HEAD` to the expected SHA. Package installation is
non-editable.

### Acceptance criteria

- The default installer does not clone an unqualified moving branch.
- A moved or changed tag causes installation to fail closed.
- A full commit SHA can be selected explicitly and is verified after clone.
- The installer does not recommend `pip install -e` for the runtime path.

## 9. P3 — tighten the public site's CSP

### Observed condition

`hyodo.app` currently returns useful headers including HSTS, frame blocking,
`nosniff`, and CSP. The CSP still contains `'unsafe-inline'` for scripts and
styles and permits `connect-src https:` broadly.

No immediate DOM XSS was confirmed in the static Evidence Graph review:
dynamic text is escaped before the graph panel uses `innerHTML`. Nevertheless,
the current CSP leaves less defense-in-depth than a nonce/hash-based policy.
The repository-owned landing and Evidence Graph outputs contain zero inline
script/style tags and style attributes after module/CSS extraction. The
post-build artifact pass also externalizes Starlight-generated inline scripts
and style attributes into same-origin content-addressed assets. The strict CSP
is encoded locally in `site/vercel.json`. The generated docs artifact has been
browser-tested locally: extracted assets resolve and no inline script, style
tag, or style attribute remains. Production rollout and header readback remain
unobserved until this branch is published and deployed.

### Repair

1. Replace inline scripts with external static assets where practical.
2. Replace `'unsafe-inline'` script permission with a nonce or exact hash for
   the remaining bootstrap code.
3. Move inline styles to generated CSS or use a narrowly scoped style policy.
4. Replace `connect-src https:` with the exact origins the site needs; use
   `connect-src 'self'` if no remote client connection is required.
5. If the deployment operator requires a staged rollout, begin with the same
   policy in report-only mode, inspect violations, then enforce it; the local
   artifact is already tested against the enforcing policy.
6. Retain `frame-ancestors 'none'`, `form-action 'self'`, HSTS, and
   `X-Content-Type-Options` while tightening the policy.

The custom-page and generated-artifact extraction is implemented and locally
browser-verified under the enforcing strict CSP header; the remaining work is
production header rollout and fresh production readback.

The static build still emits nonblocking warnings for a large client chunk, an
empty `i18n` collection, and the generated `docs → 404` content entry. These
are not evidence of a CSP bypass or a failed build, but they remain separate
site-quality follow-ups and must not be silently counted as zero warnings.

### Acceptance criteria

- The public pages load with JavaScript enabled and disabled as intended.
- Evidence Graph local-file loading still stays browser-local.
- No unexpected external origin appears in the enforced CSP.
- A fresh header readback confirms the deployed policy, not just source config.

## 10. Already-healthy boundaries to preserve

The following controls were observed or supported by focused source review and
must not regress during remediation:

- MCP loopback binding uses `127.0.0.1`; public `0.0.0.0` binding is rejected.
- MCP workspace paths are locked to the configured root.
- Paired HTTP authentication compares bearer tokens and re-reads revocation
  state.
- Default event storage is digest-only; full-body storage requires operator
  consent at server start.
- Evidence Graph values are escaped before dynamic HTML insertion.
- `hyodo.app` sends HSTS, CSP, frame denial, `nosniff`, and restrictive browser
  policy headers.
- The remote MCP endpoint is documented and observed as unavailable rather
  than being presented as a live connector.
- Public package metadata uses a small runtime dependency surface and PyPI
  Trusted Publishing is documented as the release path.

## 11. Closure template

Each repaired finding should be closed with the following fields:

```yaml
finding_id: P1-compose
status: IMPLEMENTED_AND_VERIFIED
source_sha: "<exact commit>"
changed_files:
  - docker-compose.minimal.yml
tests:
  - command: "<command>"
    exit_code: 0
    result: PASS
artifact_or_runtime_readback:
  - target: "<container/site/PyPI/GitHub surface>"
    observed: "<exact fact>"
remaining_risk: "<none or explicit residual>"
owner: "<named owner>"
verified_at: "<UTC timestamp>"
```

Do not use `PASS` for an unexecuted lane. Use `UNOBSERVED`, `HOLD`, or
`RECONCILIATION_REQUIRED` when the relevant external surface was not measured.

## 12. Operator handoff for the remaining external actions

These actions cross repository-owner, credential-owner, or deployment
authority boundaries. They are intentionally documented but were not executed
from this worktree.

### 12.1 Historical finding disposition

The [metadata-only register](security/GITLEAKS_DISPOSITION.md) records the
current disposition. Keep raw values, populated `.env` files, and unredacted
scanner reports outside Git. Any newly discovered or unexplained finding still
requires owner review and, when validity is uncertain, revocation or rotation
before a fresh full-history and artifact scan.

### 12.2 Review and publish the local remediation

After review, publish the local changes through the normal protected-branch PR
path. The PR must include the exact source SHA, the public verification
receipt, the site build/browser receipt, and the owner links for any findings
that remain `HOLD`. After merge, confirm that the remote workflow exists and
that its three checks are visible on a fresh PR before adding them to required
checks. Do not infer either condition from a successful local `actionlint`.

### 12.3 Container and production readback

On a host with Docker, run the Compose parse and isolated startup/readback with
a shell-provided `HYODO_POSTGRES_PASSWORD`; do not print the value. Build the
multi-stage image from the pinned lock input, record the image digest and SBOM,
and verify the final image is non-root and contains no development tooling.
After the site PR is deployed, read the response headers from
`https://hyodo.app/` and a representative docs route, then run the browser
smoke against that deployment. Record the deployment URL, response policy,
observed asset routes, and source/deployment SHA separately.

### 12.4 Governance decision

The repository owner must decide whether to require at least one approving
review, signed commits/tags, and the new security checks. Record that decision
as a governance receipt; the current remote observation is only partial
protection and must not be described as security enforcement.

## 13. Recommended execution sequence

1. Investigate and rotate any possibly real historical credential.
2. Harden Compose defaults and update its local-only documentation.
3. Create a clean verification environment and rerun the complete test/audit
   matrix.
4. Make the Docker build deterministic and generate its SBOM.
5. Reconcile version/support claims across source, docs, PyPI, GitHub, and the
   site.
6. Publish and require the security workflow after review.
7. Publish the strict CSP, then perform a fresh production header and browser
   readback against the deployed artifact.
8. Complete the operator handoff above and perform a final independent
   third-party readback of all six proof axes.

Until step 8 is complete, the appropriate external statement is:

> HyoDo has a documented remediation plan and several strong local/public
> controls. Compose runtime readback, historical secret disposition, Docker
> reproducibility, remote security-workflow enforcement, and CSP tightening
> remain open or explicitly unobserved.
