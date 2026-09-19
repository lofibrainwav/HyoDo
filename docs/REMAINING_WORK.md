# HyoDo remaining work and handoff

Handoff snapshot: 2026-09-19. This is a bounded work register, not a live
status feed or a claim that every possible defect has been discovered.
Refresh linked evidence before starting or closing an item.

**Disposition:** HyoDo public readiness is the current priority, ahead of other
work. "Open" does not mean the repository is public; it means a first-time
visitor can reproduce a result in their own project using the version the
documentation points them at. Source merged is not that state.

That priority orders the work in *this* register. It does not rank another
owner's queue and does not make their work wait on HyoDo — see "KINGDOM handoff
boundary" for why ordering and ownership are separate questions here.

The storefront repairs in PR #420, #421 and #422 are merged and verified in
source, and the website half is already served. The published package still
carries the pre-repair description, so the package half stays open until the
next approved release is read back. See "Public readiness" below for what is
closed, what is open, and on what evidence.

## Public readiness

Audit of 2026-09-19 raised six storefront items. "Closed" here means the state a
first-time visitor actually meets, not that a pull request merged.

The website and the package deploy on different schedules. The site redeploys on
merge to `main`; the package only changes when a release is published. Holding
both to "wait for the next release" was wrong, and the two halves are tracked
separately below.

### Observed on 2026-09-19

Website, verified against the deployed site:

- `https://hyodo.app/` and `https://hyodo.app/docs/quickstart/` both HTTP 200.
- Served stylesheet `/_astro/index.rIW0wefB.css` is byte-identical
  (SHA-256 `c7645a4e…1eee`) to the local build of merged `main` `0ae0040`, and
  carries `.hero-content{…position:relative}` with no `position:absolute`, plus
  `.hero{…padding-top:var(--navbar-height)}` and `--navbar-height:3.5rem`.
- Deployment identity at read time: `x-vercel-id: sfo1::5mbt4-1789849846551-…`,
  `last-modified: Sat, 19 Sep 2026 20:25:26 GMT`.

Published package, verified against `https://pypi.org/pypi/hyodo/json`:

- Latest version is still `4.19.8`, whose description carries **18** relative
  links, including `./QUICK_START.md`, `./docs/GATES_SYNTAX.md` and `./LICENSE`.
- `project_urls` Homepage and Documentation both point at GitHub, not at
  `hyodo.app`.

Source, verified on merged `main` `0ae0040`:

- `ruff check` / `ruff format --check` over `hyodo tests scripts`: clean.
- `pyright hyodo`: 0 errors.
- `pytest tests`: 1716 passed, 2 skipped. The skips are the opt-in SBOM
  integration lane (`HYODO_SBOM_INTEGRATION=1`) and the built-artifact metadata
  check, which reports UNOBSERVED rather than passing when no build is present.
- Rebuild of merged `main`: `twine check` passed for sdist and wheel,
  `verify_sdist_scope.py` PASS (92 members), and the built `PKG-INFO` and
  `METADATA` carry zero relative links.

### Status

<!-- markdownlint-disable MD013 -->

| Item | Website | Package | Evidence / residual |
| --- | --- | --- | --- |
| A1 published links | n/a | **open** | Source merged in #420 and a readback check added to `verify-pypi-release.py`. The live 4.19.8 description still 404s. Closes when the next published release is read back. |
| A2 small screens | **closed** | n/a | Measured on the deployed site at 1440×900, 390×844, 375×667, 360×640, 320×568 and 844×390: content above the hero is 0px everywhere, the heading never starts above the fixed navbar, both hero controls are fully visible, and the page scrolls. |
| A3 first install | **closed** (guidance) | **open** (package) | The deployed quickstart carries the prerequisites, `cd your-project`, and the per-installer extra step. The clean install itself is still only verified against a locally built wheel; it closes against the published package after the next release. |
| A4 representative result | **source complete**, serves on merge | n/a | `/docs/worked-example/` carries one run of the published 4.19.9 wheel on a three-file project: the input files, the command, verbatim output, and exit codes `0` / `1` / `2` asserted against that wheel. Closes on the deployed page. |
| A5 doc entry path | **source complete**, serves on merge | n/a | Sidebar regrouped into Start here / Scope and boundaries / Using HyoDo / Project, and every label now equals its page's frontmatter title. Quickstart gained a support-scope table. A regression gate asserts the label match. Closes on the deployed page. |
| A6 contact and data boundary | **partly source complete** | **open** | Footer gained questions, security-reporting and maintenance links plus a web-vs-local data-boundary statement, and `og:image` now ships — all serve on merge. `project_urls` Homepage and Documentation are repointed at `hyodo.app` in source, but the **published 4.19.9 metadata still points at GitHub**; that half closes only on the next release. |

<!-- markdownlint-enable MD013 -->

A4–A6 were presentation work and are no longer prerequisites for anything: the
4.19.9 release that closed A1 and A3 shipped before them.

### What A4–A6 closed on, and what stays UNOBSERVED

Measured on 2026-09-19 against the published 4.19.9 wheel and the live site:

- **A4 is a real result, not a mock.** Every output block on
  `/docs/worked-example/` was pasted from a terminal running
  `hyodo` 4.19.9 installed from PyPI into an empty pipx home. The three exit
  codes were asserted, not described: `0` gates passed, `1` a gate failed, `2`
  nothing measured. The `2` case includes a malformed `.hyodo/gates.toml`, which
  the tool reports as `UNOBSERVED` rather than as a pass.
- **A5's label agreement is now a gate, not a promise.**
  `site/scripts/check-site-output.mjs` compares every sidebar label to the target
  page's frontmatter `title` and fails the build on a mismatch or a dangling
  slug. Adding it immediately caught two mismatches beyond the audited one
  (`docs/connect`, `docs/runtime-identity`), which were fixed.
- **A6 is deliberately split.** The site half — contact, security reporting,
  maintenance scope, the data-boundary statement, `og:image` — serves on merge.
  The package half does not: PyPI keeps 4.19.9's metadata until a new release, so
  `project_urls` Homepage and Documentation still point at GitHub for anyone
  reading the published page today.
- **The data-boundary claim was verified, not asserted.** The live site sends no
  `Set-Cookie`, loads no third-party `src`, and is served under
  `script-src 'self'; connect-src 'self'`, which makes third-party scripts and
  cross-origin calls impossible rather than merely absent. The local claim was
  checked too: after a full `hyodo check` run the tool had written only
  `.hyodo/gates-trust.json` inside the project, and nothing under `$HOME`.

Still `UNOBSERVED`:

- All three closures are measured on source and on a local build. The deployed
  page is a separate readback, taken after merge.
- `og:image` is verified to ship in `dist/index.html` with the correct absolute
  URL and to exist at `dist/og-image.png`. How any particular social platform
  renders or caches it is not observed.
- The published `project_urls` fix is source-only until the next release.

### How A2 was measured, and what that does not cover

Chrome 153.0.8010.48 driven over the DevTools Protocol against the live site,
using real viewport emulation (`Emulation.setDeviceMetricsOverride`) rather than
an iframe, and real `Tab` key events. Enlarged text was applied through the
browser's own default font size (`Page.setFontSizes`, 16px → 32px), because the
site's `style-src 'self'` policy correctly blocks an injected stylesheet — an
earlier attempt to inject `html{font-size:200%}` silently did nothing and its
results were discarded.

At 32px base the hero grows to 3209px on a 320×568 screen and the heading, at
484px tall, no longer fits beside the navbar in one screen; it stays reachable
and readable by scrolling and both controls remain fully visible. Scrolling the
heading to the top of the viewport places its first line under the fixed navbar,
which a `scroll-margin-top` would address; recorded as an observation, not fixed
here.

Not covered: real handsets, screen readers, and any browser other than the one
above. A separate profile was used because the extension bridge to the everyday
browser was unavailable at the time; fonts and user settings therefore differ
from a real visitor's.

## What is already closed

- [PR #417](https://github.com/lofibrainwav/HyoDo/pull/417): admission,
  orchestration-observation, and release-gate evidence boundary repairs.
- [PR #414](https://github.com/lofibrainwav/HyoDo/pull/414): host observation
  report, with sample limitations and HyoDo/host ownership made explicit.
- PR #414 head checks: 24 successful check runs. Its merged main snapshot:
  20 successful checks, no failures or pending checks, and one expected
  PR-only dependency-review skip.
- Local verification of that candidate: `bash scripts/verify-public.sh`
  exited 0, with 1,698 tests passed and no skipped tests; document lint and
  local links passed. These results do not cover future changes.
- [4.19.8 release record](./releases/4.19.8.md): the existing release closure
  remains valid within its recorded scope. It does not publish later merges.

## Remaining HyoDo work

P1 means resolve or explicitly disposition before claiming the affected
public surface is complete. P2 means maintenance or evidence follow-up.
UNOBSERVED means verification is missing, not that a defect is confirmed.
Roles below identify responsibility; no individual assignee is designated.

<!-- markdownlint-disable MD013 -->

| ID | Priority / state | Work and next action | Responsible role | Completion evidence |
| --- | --- | --- | --- | --- |
| H1 | P1 / OPEN | Decide whether to release post-4.19.8 source changes. Review the complete release delta and prepare the next version under the release checklist. | HyoDo release maintainer | Approved release scope; candidate checks; published version, artifact hashes, SBOM/provenance, clean install and behavior readback. A main merge alone does not close this. |
| H2 | P1 / UNOBSERVED | Audit public MCP wording, especially `mcp.hyodo.app`, against the actual supported service. Keep hosted contract-only status clear. | HyoDo public surface maintainer | Dated page/endpoint evidence and matching documentation; either supported behavior verified or unsupported/unavailable status stated clearly. Building a hosted service is not implied. |
| H3 | P1 / UNOBSERVED | Audit privacy statements against actual collection, retention, consent, and deletion behavior of each advertised surface. | HyoDo public surface maintainer | Surface-specific data-flow evidence, matching public explanation, and disposition of each discrepancy. No private payloads in public receipts. |
| H4 | P1 / UNOBSERVED | Verify accessibility of the advertised public user journeys; inspect existing receipts before defining fresh scope. | HyoDo UI maintainer | Dated keyboard, focus, labeling, and contrast checks for named journeys; defects fixed or explicitly scoped and tracked. |
| H5 | P1 / UNOBSERVED | Check provenance of public evidence claims and provide a reproducible, non-private example. | HyoDo evidence maintainer | Source/version/method-bound receipt and independent reproduction instructions with expected results and limitations. Private ledger counts remain sample reports unless reproducible evidence is supplied. |
| H6 | P2 / OPEN | Review dependency PR #418 separately; refresh its base and inspect compatibility before deciding to merge. | HyoDo dependency maintainer | Reviewed dependency diff, relevant site checks, exact-head CI and post-merge evidence, or a documented decision to close/defer. |
| H7 | P2 / OPEN | Refresh dated public claim documentation. The July external audit says `hyodo check` is checkout-only, while current guidance distinguishes BYOG from HyoDo self-verification. | HyoDo documentation maintainer | Dated scope-correct audit tied to current source/package behavior; historical observations labeled as historical. |
| H8 | P2 / RECORDED | Preserve the reported missing model-attribution trailers on historical commits `07fdc0f` and `1b9b3f3`; verify and decide whether an additive correction is needed. | HyoDo repository maintainer | Maintainer disposition or additive attribution record. No history rewrite is required by this register. |

<!-- markdownlint-enable MD013 -->

H2-H5 carry forward reported public-surface concerns. They were not freshly
audited during the #414 closeout and must not be presented as confirmed
vulnerabilities or as completed work. H8 is a reported historical concern,
not a newly verified finding.

## Order of work and closure rule

1. A returning HyoDo maintainer refreshes main, open PRs, the public version,
   and evidence for the affected surfaces; then assigns owners.
2. Resolve H2-H5 and H7 within an explicit public-product scope. A finding can
   close through a verified fix or an honest, documented scope limitation.
3. Use those results to select H1 release scope. Release only after its
   separate authorization and verification gates are satisfied.
4. Handle H6 and H8 independently; neither automatically expands release
   scope or authorizes rewriting history.
5. Record each item's evidence link, observed date, final state, and owner
   disposition here when it changes. Do not replace UNOBSERVED with PASS
   merely because source tests pass.

The affected product scope is complete only when its advertised behavior is
verified, its published artifact or service matches that scope, and each
applicable P1 item has an explicit disposition. This is a checklist for a
maintainer decision, not automatic release or execution authority.

## KINGDOM handoff boundary

KINGDOM work may start now without reopening the closed HyoDo PRs. That is a
statement about dependency, not about priority: KINGDOM has its own owner and
its own register, so nothing in it is blocked by the HyoDo items above, and
nothing in it reorders them. Neither side's progress is evidence about the
other.

<!-- markdownlint-disable MD013 -->

| Concern | Owner and boundary |
| --- | --- |
| Planning, worker lifecycle, execution, recovery, authorization | Integrating host / KINGDOM. Track in its own work register. |
| Fresh Codex/Cursor callbacks, prompt payloads, missing tool results | Host integration investigation. Report actual payload/delivery observations before proposing a reusable HyoDo adapter change. |
| Evidence schema, validation, ledger, attestation, public package | HyoDo. A host finding becomes HyoDo work only with a concrete public contract or reproducible package defect. |
| Durable memory and settled lessons | BB under its own governance; this document does not write or promote memory. |

<!-- markdownlint-enable MD013 -->

Do not copy KINGDOM runtime state into this register or interpret a HyoDo
receipt as execution permission. HyoDo public release, HyoDo served runtime,
and KINGDOM runtime require separate readbacks. Do not expand this handoff
into deployment, host repair, or private data publication.

## Reference entry points

- [Current state](./CURRENT_STATE.md)
- [Product boundary](./PRODUCT_BOUNDARY.md)
- [Release checklist](../RELEASE_CHECKLIST.md)
- [Release pipeline](./RELEASE_PIPELINE.md)
- [Remote MCP contract](./M5_REMOTE_CONNECTOR_CONTRACT.md)
- [Security surface](./SECURITY_SURFACE.md)
- [Measurement provenance](./MEASUREMENT_PROVENANCE.md)
- [Host observation report](./HOST_OBSERVATION_CONTRACT.md)
- [Historical accessibility receipt](./research/ACCESSIBILITY_RECEIPT_2026-09-10.md)
- [Historical external claim audit](./EXTERNAL_CLAIM_AUDIT.md)
- [Dependency PR #418](https://github.com/lofibrainwav/HyoDo/pull/418)
