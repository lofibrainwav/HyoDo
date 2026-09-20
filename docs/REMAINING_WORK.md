# HyoDo remaining work and handoff

Handoff snapshot: 2026-09-19, revised after the 4.19.9 release. This is a
bounded work register, not a live status feed or a claim that every possible
defect has been discovered. Refresh linked evidence before starting or closing
an item.

Observations in this file are timestamped. An earlier observation is not
retracted when a later one supersedes it — it is kept, dated, as the record of
what was true then. "Current state" below always means the most recent dated
reading.

**Disposition:** HyoDo public readiness is the current priority, ahead of other
work. "Open" does not mean the repository is public; it means a first-time
visitor can reproduce a result in their own project using the version the
documentation points them at. Source merged is not that state.

That priority orders the work in *this* register. It does not rank another
owner's queue and does not make their work wait on HyoDo — see "KINGDOM handoff
boundary" for why ordering and ownership are separate questions here.

**Current state (2026-09-19, after the 4.19.9 release).** All six audited
storefront items are closed on the surface a visitor actually meets. HyoDo
4.19.9 is published; `main` is `897112b`. One residual remains, and it is a
metadata field rather than a defect a reader hits: `project_urls` Homepage and
Documentation are repointed at `hyodo.app` in source but still read GitHub on
the published 4.19.9 page. It is queued for whenever a release is next
authorized for other reasons — it does not itself call for one.

See "Public readiness" for each item and the evidence behind it.

## Public readiness

Audit of 2026-09-19 raised six storefront items. "Closed" here means the state a
first-time visitor actually meets, not that a pull request merged.

The website and the package deploy on different schedules. The site redeploys on
merge to `main`; the package only changes when a release is published. Holding
both to "wait for the next release" was wrong, and the two halves are tracked
separately below.

### Observed 2026-09-19, ~20:25 UTC — before the 4.19.9 release

Kept as the record of the pre-release state. Superseded by the next section; not
retracted.

Website, verified against the deployed site:

- `https://hyodo.app/` and `https://hyodo.app/docs/quickstart/` both HTTP 200.
- Served stylesheet `/_astro/index.rIW0wefB.css` **was** byte-identical
  (SHA-256 `c7645a4e…1eee`) to the local build of merged `main` `0ae0040`, and
  carries `.hero-content{…position:relative}` with no `position:absolute`, plus
  `.hero{…padding-top:var(--navbar-height)}` and `--navbar-height:3.5rem`.
- Deployment identity at read time: `x-vercel-id: sfo1::5mbt4-1789849846551-…`,
  `last-modified: Sat, 19 Sep 2026 20:25:26 GMT`.

Published package, verified against `https://pypi.org/pypi/hyodo/json`:

- Latest version **was** `4.19.8`, whose description carried **18** relative
  links, including `./QUICK_START.md`, `./docs/GATES_SYNTAX.md` and `./LICENSE`.
- `project_urls` Homepage and Documentation both pointed at GitHub, not at
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

### Observed 2026-09-19, ~22:40–23:00 UTC — after the 4.19.9 release

This is the current reading. It supersedes the section above.

Published package, verified against `https://pypi.org/pypi/hyodo/json`:

- Latest version is **`4.19.9`**; `description_content_type` is `text/markdown`.
- Its description carries **0** relative links and **18** links pinned to
  `/blob/v4.19.9/`, with **0** pinned to any other ref. All 18 were requested and
  all 18 returned **HTTP 200**, including `QUICK_START.md`,
  `docs/GATES_SYNTAX.md` and `LICENSE`.
- `project_urls` Homepage and Documentation still point at GitHub. The source
  fix landed after the tag, so the published metadata keeps the old values.

Clean install, in a pipx home/bin/man sandbox isolated from the machine's real
pipx:

- `pipx install hyodo` installed **4.19.9**; `hyodo --version` reported
  `HyoDo v4.19.9`. The first attempt resolved 4.19.8 from a local pip HTTP
  cache — with the cache disabled it resolved 4.19.9, and `/simple/hyodo/`
  listed 4.19.9 with both files throughout. Recorded because "the index shows
  the new version" and "a fresh install gets it" are different observations.
- Without the extra, `hyodo mcp stdio` exited **2** and printed both installer
  paths (`pip install 'hyodo[mcp]'`, `pipx install --force 'hyodo[mcp]'`).
- After `pipx install --force 'hyodo[mcp]'`, the MCP SDK (2.2.0) landed in the
  same environment, and a client harness confirmed protocol rather than
  liveness: `initialize` returned `HyoDo 4.19.9`, `list_tools` returned exactly
  the six documented tools, and a read-only `get_local_context` call returned
  valid JSON.

Release chain, written by `verify_release_chain 4.19.9`: all nine steps
`OBSERVED` — verified tag `v4.19.9` → `c2b85e8`, evidence run `35473900611`,
publish run `35473994781`, wheel sha256 `7895a1c1fcf00a1f`.

Website, verified against the deployed site after `897112b`:

- `/docs/worked-example/` HTTP 200 and serving the real output lines
  (`measured by hyodo 4.19.9 (wheel)`, `HYODO PASS`, `HYODO FAIL`,
  `HYODO UNOBSERVED`, `unsupported schema None`).
- The four sidebar groups serve; the label reads `From values to evidence` and
  the old `Philosophy → Math → Code` label is gone.
- The footer serves the contact, security-reporting and maintenance links and
  the data-boundary paragraph.
- `og:image` meta is present and absolute; `https://hyodo.app/og-image.png`
  returns 200 `image/png` and is SHA-256 identical (`d612719d…4e96`) to the
  committed file.
- One transient `404` was seen on `/docs/worked-example/` seconds after the
  merge and resolved on the next probe: CDN propagation, not a routing defect.

### Status

<!-- markdownlint-disable MD013 -->

| Item | Website | Package | Evidence / residual |
| --- | --- | --- | --- |
| A1 published links | n/a | **closed** | The published 4.19.9 description carries 0 relative links and 18 pinned to `/blob/v4.19.9/`; all 18 were requested and returned HTTP 200. `verify-pypi-release.py` re-checks this on every future release. |
| A2 small screens | **closed** | n/a | Measured on the deployed site at 1440×900, 390×844, 375×667, 360×640, 320×568 and 844×390: content above the hero is 0px everywhere, the heading never starts above the fixed navbar, both hero controls are fully visible, and the page scrolls. See "How A2 was measured" for what that does not cover. |
| A3 first install | **closed** | **closed** | The deployed quickstart carries the prerequisites, `cd your-project`, and the per-installer extra step. Against the published 4.19.9 package in an isolated pipx sandbox: `hyodo mcp stdio` exits 2 with both installer paths, and after the advised extra install the MCP client completes initialize / list_tools (six tools) / a read-only call. |
| A4 representative result | **closed** | n/a | `/docs/worked-example/` is served and carries one run of the published 4.19.9 wheel on a three-file project — input files, command, verbatim output, and exit codes `0` / `1` / `2` asserted against that wheel, including the malformed-config case that reports `UNOBSERVED` rather than a pass. |
| A5 doc entry path | **closed** | n/a | Four sidebar groups serve, every label equals its page's frontmatter title, and the quickstart carries a support-scope table. `site/scripts/check-site-output.mjs` fails the build on a label mismatch or a dangling slug; adding it caught two mismatches beyond the audited one. |
| A6 contact and data boundary | **closed** | **residual** | The footer's contact, security-reporting and maintenance links, the web-vs-local data-boundary paragraph, and `og:image` are all served and verified. Residual: `project_urls` Homepage and Documentation are repointed at `hyodo.app` in source but still read GitHub on the published 4.19.9 page. Queued for the next authorized release; it does not call for one. |

<!-- markdownlint-enable MD013 -->

All six audited items are closed on the surface a visitor meets. A4–A6 were
presentation work and were never prerequisites for the 4.19.9 release, which
shipped before them and closed A1 and A3.

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
- **The data-boundary claim was verified, not asserted — within a stated
  scope.** The live site sends no `Set-Cookie`, loads no third-party `src`, and
  is served under `script-src 'self'; connect-src 'self'`, which makes
  third-party scripts and page-originated cross-origin calls impossible rather
  than merely absent. That scope has two edges the earlier wording overreached.
  `connect-src` governs the page's own fetch/XHR/WebSocket destinations, not
  every outbound request: images and fonts fall under `img-src`/`font-src`,
  which the deployed policy opens to `https:`. And no client-side policy speaks
  to what the host records about a request, so hosting-side request logging
  stays `UNOBSERVED` rather than disproved. The local claim was checked too:
  after a full `hyodo check` run the tool had written only
  `.hyodo/gates-trust.json` inside the project, and nothing under `$HOME`; that
  covers HyoDo's own writes, not the gate commands a user registers or an MCP
  host they deliberately connect.

Still `UNOBSERVED`, after the deployed readback:

- How any particular social platform renders or caches `og:image`. What was
  verified is that the meta tag is absolute and that the URL serves the
  committed bytes.
- The published `project_urls` values. The source fix exists; the published page
  keeps the old ones until a release is next authorized.
- Everything named under "How A2 was measured, and what that does not cover" —
  real handsets, screen readers, and any browser other than the one used.

These A4–A6 closures are evidence about the storefront items only. They do not
close H2–H5: the data-boundary paragraph is a statement about two surfaces, not
the surface-by-surface privacy audit H3 asks for, and the A2 keyboard walk is
one journey in one browser, not the accessibility verification H4 asks for.

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
| H1 | P1 / CLOSED for 4.19.9 (2026-09-19) | Released 4.19.9 under the release checklist after an explicit authorization naming commit `c2b85e8`. The next release decision is a fresh instance of this item, not a continuation of this one. | HyoDo release maintainer | Verified tag `v4.19.9` → `c2b85e8` (GitHub `verification.verified: true`); durable SBOM plus SHA-256 receipt on the published Release, checksum re-verified independently; publish run `35473994781` with provenance and install smoke green; wheel sha256 `7895a1c1fcf00a1f`; `verify_release_chain 4.19.9` records all nine steps `OBSERVED`; published description and isolated clean install read back by hand. Carried forward: `project_urls` Homepage/Documentation, fixed in source after the tag. |
| H2 | P1 / UNOBSERVED | Audit public MCP wording, especially `mcp.hyodo.app`, against the actual supported service. Keep hosted contract-only status clear. | HyoDo public surface maintainer | Dated page/endpoint evidence and matching documentation; either supported behavior verified or unsupported/unavailable status stated clearly. Building a hosted service is not implied. |
| H3 | P1 / UNOBSERVED | Audit privacy statements against actual collection, retention, consent, and deletion behavior of each advertised surface. | HyoDo public surface maintainer | Surface-specific data-flow evidence, matching public explanation, and disposition of each discrepancy. No private payloads in public receipts. |
| H4 | P1 / UNOBSERVED | Verify accessibility of the advertised public user journeys; inspect existing receipts before defining fresh scope. | HyoDo UI maintainer | Dated keyboard, focus, labeling, and contrast checks for named journeys; defects fixed or explicitly scoped and tracked. |
| H5 | P1 / UNOBSERVED | Check provenance of public evidence claims and provide a reproducible, non-private example. | HyoDo evidence maintainer | Source/version/method-bound receipt and independent reproduction instructions with expected results and limitations. Private ledger counts remain sample reports unless reproducible evidence is supplied. |
| H6 | P2 / OPEN | Review dependency PR #418 separately (unchanged by the 4.19.9 release); refresh its base and inspect compatibility before deciding to merge. | HyoDo dependency maintainer | Reviewed dependency diff, relevant site checks, exact-head CI and post-merge evidence, or a documented decision to close/defer. |
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
   Storefront work done in September 2026 touched adjacent ground — a
   data-boundary statement near H3, a keyboard walk near H4 — but neither is the
   audit those items ask for, and neither closes them.
3. H1 is closed for 4.19.9. A further release is a new instance of H1 and needs
   its own authorization and verification gates; the `project_urls` residual
   rides along with whatever release is next authorized rather than justifying
   one.
4. Handle H6 and H8 independently; neither automatically expands release
   scope or authorizes rewriting history.
5. Record each item's evidence link, observed date, final state, and owner
   disposition here when it changes. Do not replace UNOBSERVED with PASS
   merely because source tests pass, and keep a superseded observation in place
   with its date rather than overwriting it.

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
