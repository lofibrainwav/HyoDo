# HyoDo remaining work and handoff

Handoff snapshot: 2026-09-20, revised after the 4.20.0 release. This is a
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

**Current state (2026-09-20, after the 4.20.0 release).** HyoDo 4.20.0 is
published; `main` is `b86931f`. All six audited storefront items are closed on
the surface a visitor actually meets, and the 4.19.9 `project_urls` residual is
closed too: the published 4.20.0 page reads Homepage `https://hyodo.app` and
Documentation `https://hyodo.app/docs/quickstart/`. The register items below
each carry a dated disposition; none is left silently `UNOBSERVED`.

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

### Observed 2026-09-20, ~23:00 UTC — after the 4.20.0 release and #438

This is the current reading. It supersedes the sections above where they
disagree; they are kept, dated, as the record of what was true then.

Published package and release, verified against PyPI, GitHub, and CI:

- Latest version is **`4.20.0`**; `project_urls` Homepage and Documentation now
  read `https://hyodo.app` and `https://hyodo.app/docs/quickstart/` on the
  published page. The 4.19.9 metadata residual is closed.
- GitHub Release `v4.20.0` reports `immutable: true` (API readback 2026-09-20),
  with SBOM and SHA-256 receipt assets attached. The `v4.19.5` immutability
  residual recorded in the third-party register is superseded by this release.
- `main` is `b86931f`; its check runs are 20 success and 1 expected
  PR-only dependency-review skip. Open pull requests: 0. Dependency PR #418
  (`@types/three` 0.185.4 → 0.186.0) merged at 2026-09-20T18:35Z; its merge
  commit is an ancestor of `main` and the lock carries `@types/three` 0.186.0.

Website, verified against the deployed site:

- `https://hyodo.app/` returns HTTP 200 with a strict same-origin CSP
  (`default-src 'self'`, plus `frame-ancestors 'none'`, `form-action 'self'`,
  `base-uri 'self'`, `object-src 'none'`) and **no `unsafe-inline`**. No
  `Set-Cookie` is sent. The only external URLs in the served HTML are plain
  links (GitHub, PyPI); the page loads no third-party script, image, font, or
  fetch origin.

Remote MCP boundary, verified by endpoint probe:

- `https://mcp.hyodo.app/mcp` and `https://mcp.hyodo.app/` both return
  HTTP 404, matching the repository's contract-only documentation on every
  surface checked (README, ONBOARDING, SECURITY_SURFACE, the MCP design and
  M5 contract documents). No hosted MCP service is advertised as live.

Package data boundary, verified by source inspection of `main`:

- `hyodo/` contains no HTTP client import and no telemetry or analytics
  integration; runtime dependencies are `jsonschema`, `referencing`, `typer`,
  `rich`, and the Python 3.10 `tomli` backport. The one raw-socket use is a
  local port-availability probe. Combined with the 2026-09-19 local-write
  check (only `.hyodo/gates-trust.json` written; nothing under `$HOME`), the
  package-side privacy statement holds within its stated scope;
  hosting-side request logging remains honestly `UNOBSERVED`.

Accessibility, measured on the deployed site (see H4):

- All three advertised journeys pass keyboard, focus, labeling, and AA
  contrast checks within the stated scope (driven Chromium only). One minor
  defect (a swallowed Tab after the last evidence-graph cell) and one
  advisory (sub-3:1 tile fills, redundant with text) are recorded in the H4
  row rather than fixed here.

### Status

<!-- markdownlint-disable MD013 -->

| Item | Website | Package | Evidence / residual |
| --- | --- | --- | --- |
| A1 published links | n/a | **closed** | The published 4.19.9 description carries 0 relative links and 18 pinned to `/blob/v4.19.9/`; all 18 were requested and returned HTTP 200. `verify-pypi-release.py` re-checks this on every future release. |
| A2 small screens | **closed** | n/a | Measured on the deployed site at 1440×900, 390×844, 375×667, 360×640, 320×568 and 844×390: content above the hero is 0px everywhere, the heading never starts above the fixed navbar, both hero controls are fully visible, and the page scrolls. See "How A2 was measured" for what that does not cover. |
| A3 first install | **closed** | **closed** | The deployed quickstart carries the prerequisites, `cd your-project`, and the per-installer extra step. Against the published 4.19.9 package in an isolated pipx sandbox: `hyodo mcp stdio` exits 2 with both installer paths, and after the advised extra install the MCP client completes initialize / list_tools (six tools) / a read-only call. |
| A4 representative result | **closed** | n/a | `/docs/worked-example/` is served and carries one run of the published 4.19.9 wheel on a three-file project — input files, command, verbatim output, and exit codes `0` / `1` / `2` asserted against that wheel, including the malformed-config case that reports `UNOBSERVED` rather than a pass. |
| A5 doc entry path | **closed** | n/a | Four sidebar groups serve, every label equals its page's frontmatter title, and the quickstart carries a support-scope table. `site/scripts/check-site-output.mjs` fails the build on a label mismatch or a dangling slug; adding it caught two mismatches beyond the audited one. |
| A6 contact and data boundary | **closed** | **closed** | The footer's contact, security-reporting and maintenance links, the web-vs-local data-boundary paragraph, and `og:image` are all served and verified. The `project_urls` residual closed with 4.20.0: the published page reads `hyodo.app` for Homepage and Documentation (readback 2026-09-20). |

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
| H1 | P1 / CLOSED for 4.20.0 (2026-09-20) | Released 4.20.0 from tag target `a5ecdcd`; all nine release-chain steps `OBSERVED` (verified tag signature, release evidence run, SBOM and SHA-256 receipt assets, PyPI publish and provenance, install smoke, wheel sha256 `b96759ca26c067e9`); the GitHub Release reports `immutable: true`. The 4.19.9 `project_urls` carry-forward closed with this release. The next release decision is a fresh instance of this item, not a continuation of this one. | HyoDo release maintainer | `docs/releases/4.20.0.md` receipt; PyPI and GitHub API readback 2026-09-20 recorded above. |
| H2 | P1 / CLOSED (2026-09-20) | Audited public MCP wording against the actual supported service. Endpoint probe: `mcp.hyodo.app/mcp` and `/` both return HTTP 404; every surface checked (README, ONBOARDING, SECURITY_SURFACE, M5 contract, MCP design docs) states contract-only / not live. No surface advertises a hosted MCP service. Building a hosted service was never implied and is not begun. | HyoDo public surface maintainer | Dated probe and wording sweep across `main`, 2026-09-20, recorded above. |
| H3 | P1 / CLOSED within stated scope (2026-09-20) | Site: no `Set-Cookie`, no third-party load origins, strict CSP without `unsafe-inline`, `connect-src 'self'`. Package: no network client, no telemetry, five declared runtime deps, local writes confined to `.hyodo/` (2026-09-19 check). Hosting-side request logging stays explicitly `UNOBSERVED` — a stated scope limit, not an unexamined gap. No private payloads appear in public receipts. | HyoDo public surface maintainer | Dated header/HTML readback and source inspection, 2026-09-20, recorded above. |
| H4 | P1 / CLOSED within measured scope (2026-09-20) | Audited the three advertised journeys on the deployed site. Keyboard: full walk of `/` (34 focus stops, visible `:focus-visible` outline at every stop, skip-link present and functional), quickstart (78 stops, `lang=en`, main landmark, 0 images without alt), evidence-graph prototype (cells are real buttons with descriptive `aria-label`s; Escape clears the panel without losing focus; DOM order equals visual order). Contrast, computed from the served CSS: body text 15.85:1, secondary text 6.19:1, panel text 5.27:1, ask 7.93:1, warn badge ink 10.57:1, focus ring 3.96:1 vs node fill — all pass AA (4.5:1 text / 3:1 UI). Two recorded non-blockers: one Tab press is consumed by `BODY` after the last graph cell (the cell's blur handler resets the side panel with an innerHTML swap that destroys the `<summary>` which was the next focus target mid transfer, so focus aborts to `BODY`; the next Tab reaches the link — exactly one wasted keypress, nothing unreachable, non-recurring), and decision-tile fills sit below 3:1 but the decision is redundantly available as cell text (advisory). Not covered, stated as scope: screen readers, real handsets, browsers other than the driven Chromium. | HyoDo UI maintainer | Dated keyboard/focus/labeling/contrast evidence above, 2026-09-20; defect and advisory explicitly scoped rather than silently passed. |
| H5 | P1 / CLOSED (2026-09-20) | Public evidence claims carry reproducible provenance: the worked-example page reproduces one full run of the published wheel (input files, command, verbatim output, asserted exit codes `0`/`1`/`2`), and the 4.20.0 release receipt records the full chain with wheel sha256 and a verified tag. Private ledger counts are not cited as public evidence. | HyoDo evidence maintainer | `/docs/worked-example/` served output; `docs/releases/4.20.0.md` nine-step `OBSERVED` receipt. |
| H6 | P2 / CLOSED (2026-09-20) | Dependency PR #418 reviewed and merged (2026-09-20T18:35Z); the merge commit is an ancestor of `main`, `site/package-lock.json` carries `@types/three` 0.186.0, and `main` CI is green after it (20 success + 1 expected skip). | HyoDo dependency maintainer | GitHub API readback 2026-09-20 recorded above. |
| H7 | P2 / CLOSED (2026-09-20) | `docs/EXTERNAL_CLAIM_AUDIT.md` now carries a dated 2026-09-20 scope-supersession note marking the 2026-07-21 audit as historical and recording the current `check` scope (BYOG gates in any project; sampled language-agnostic gates as the no-config default; HyoDo self-verification a separate checkout-scoped path), with dependency/MCP findings re-observed unchanged. Landed with this register update. | HyoDo documentation maintainer | Dated note in the audit document itself. |
| H8 | P2 / DISPOSITIONED (2026-09-20) | `07fdc0f` and `1b9b3f3` were verified to carry no model-attribution trailer; both predate the recorded convention. History is not rewritten. The repository convention (CLAUDE.md) requires model attribution via `Co-Authored-By` going forward and recent history shows it in use. No additive correction record is owed beyond this entry. | HyoDo repository maintainer | This register entry is the disposition record. |

<!-- markdownlint-enable MD013 -->

H2, H3, H5, H6, and H7 now carry dated 2026-09-20 dispositions in the rows
above. The 2026-09-19 note that H2–H5 "carry forward reported public-surface
concerns" was true then and is superseded by those rows. H8 is dispositioned
without history rewrite.

## Order of work and closure rule

1. A returning HyoDo maintainer refreshes main, open PRs, the public version,
   and evidence for the affected surfaces; then assigns owners.
2. Resolve H2-H5 and H7 within an explicit public-product scope. A finding can
   close through a verified fix or an honest, documented scope limitation.
   Storefront work done in September 2026 touched adjacent ground — a
   data-boundary statement near H3, a keyboard walk near H4 — but neither is the
   audit those items ask for, and neither closes them.
3. H1 is closed for 4.19.9 and 4.20.0. A further release is a new instance of
   H1 and needs its own authorization and verification gates. The
   `project_urls` residual closed with 4.20.0 and no longer rides along.
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
