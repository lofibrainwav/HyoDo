# 06 Progress

State of the site, newest first. Every entry names the command that proved
it.

## 2026-09-06 (layer 4: evidence graph prototype surface)

Added a public, browser-only prototype of the evidence graph at
`/evidence-graph/`, plus its docs page. New: `src/graph/evidence-graph.ts`
(14-event fixed fixture + renderer, ~470 lines), `src/styles/evidence-graph.css`,
`src/pages/evidence-graph.astro`, `src/content/docs/docs/evidence-graph.md`.
Updated `astro.config.mjs` sidebar, `index.astro` nav, and `roadmap.md`
(Stage 1 row, shipped/not-built table, "Next" list) to match v4.13.0 and
the prototype. All fixture data is privacy-scrubbed (`human:operator`,
`https://example.com/oncall-hook`) — no real usernames or internal hosts.

Two rounds of self-review against screenshots found and fixed real defects:

1. **Astro whitespace-trim bug**: a text node that is pure
   newline+indentation immediately before/after an inline tag (`<code>`,
   `<a>`) is trimmed to nothing rather than collapsed to a space, so
   `network. The\n<code>` rendered as `network. Thecode` in the built
   HTML. Fixed by keeping each such join on one source line (no line
   break directly adjacent to an inline tag) in `evidence-graph.astro`.
2. **Mobile column-flex overflow**: `.graph-wrap` (a flex item) computed
   its own width via fit-content of its child `.grid` (`width:
   max-content`, ~950px) once `.eg-main` switched to
   `flex-direction: column` under 900px, because `align-items:
   flex-start` sizes cross-axis to content instead of stretching —
   pushing the whole page wider than the viewport. Fixed with `max-width:
   100%` on `.graph-wrap`, `align-items: stretch` and explicit `width:
   100%` in the mobile media query, plus `overflow-x: hidden` on
   `.eg-page` as a backstop.
3. **Evidence edges crossing decision-node text**: the `evt-p3 → evt-e2`
   evidence edge (same column, adjacent rows) used left/right ports like
   every other edge, so its bezier bow crossed straight over both
   `path_inside_root` and `path_outside_root` labels. Fixed by routing
   same-column evidence edges through top/bottom ports (the row gap)
   instead of left/right; widened the grid gap to 14px and shrank the
   arrowhead markers (7→6) so adjacent same-row parent edges keep a
   visible line segment instead of rendering as a bare floating
   arrowhead; increased the evidence-curve bow factor (0.16→0.26) so the
   longer diagonal evidence edge arcs further from decision cells it
   would otherwise graze.
4. Added an interaction-only cell hover/focus lift (`translateY(-1px)`,
   120ms), gated entirely inside `@media (prefers-reduced-motion:
   no-preference)` so it is absent, not just un-transitioned, under
   reduced motion.

Verification: `npx astro check` → 0 errors/warnings/hints (10 files).
`npm run build` → 9 routes (previous 7 + `/evidence-graph/` +
`/docs/evidence-graph/`). `grep -c 'Prototype'
dist/evidence-graph/index.html` → 1. Privacy grep
(`brnestrm|hooks.internal|kingdom|embedding|vector`) over
`src/graph`, the new page/docs, and their `dist/` output → no matches.
Network-API grep (`fetch\(|XMLHttpRequest|WebSocket|localStorage`) over
`evidence-graph.ts` → no matches. `pytest tests/test_public_language.py`
→ 3 passed. Desktop (1440×1000) and docs (1440×1000) screenshots via
headless Chrome `--screenshot` matched the fix in every check above.

**Not verified**: the `--headless=new --window-size=375,900 --screenshot`
CLI path was flaky in this sandbox specifically for this page — it
reproducibly rendered as if the viewport were wider than 375px (text
failing to wrap, right edge clipped), even after a rebuild and with
`--force-device-scale-factor=1`/`--virtual-time-budget` added. A CDP
session with an explicit `Emulation.setDeviceMetricsOverride({width:375,
height:900})` and a real `Page.navigate` + wait, querying
`document.body.scrollWidth`, confirmed no horizontal overflow at 375px
CSS width (`bodyScrollWidth: 370` vs `innerWidth: 375`) — so the mobile
fix is verified, but not by the exact CLI command specified for this
task; that command's screenshot in the report should not be read at
face value for this page. Keyboard interaction (Tab/Escape) was not
exercised by an automated tool in this pass — left for a real-browser
check.

## 2026-09-06 (unlit-grid fix: banding, rest brightness, time-based decay, poster)

Root cause of "the whole grid reads as bright green vertical bands" (measured
on the live site, Lighthouse mobile emulation and desktop Chrome
screenshots): breathing was keyed only on `regionNode` (one shared rate and
phase per six-column region), so every tile in a region breathed in lock-step
— a solid pulsing band, not a whisper. Rest-state brightness was also too
high. Fixed entirely in `src/hero/scene.ts`:

1. **Per-tile phase, not per-region phase.** Added a `tileHash` per-instance
   `InstancedBufferAttribute`, filled by a new `hash2(row, col)` (a second,
   independent hash from the existing index-based `seededNoise()`, so the
   poster's seeded cluster and the breathing phase never correlate). The
   breathing phase is now `mix(tilePhase, regionPhase, coherenceUniform)`:
   at coherence 0 every tile uses its own hash-derived phase (no two
   neighboring tiles in step), and only as coherence rises toward 1 does
   each tile's phase blend toward its region's shared phase — so a region
   only reads as a synchronized band once coherence actually gets there, per
   the spec ("phases converge, never a solid band at rest"). Amplitude is
   `mix(REST_AMPLITUDE, COHERENT_AMPLITUDE, coherenceUniform)` = `mix(0.03,
   0.08, coherence)` — quiet at rest, a real (still capped) pulse once
   synchronized. Verified the phase spread numerically (Node script,
   `region 3`, `n=658` tiles): stddev 1.77 rad (fully scattered across
   [0, 2π)) at coherence 0, stddev `4e-14` (== 0, floating-point noise) at
   coherence 1 — phases genuinely converge only at full coherence.
2. **Rest-state brightness.** Re-tuned `CENTER_GAIN` from `0.9` to `0.75` by
   Node simulation (below) so the mean and 90th-percentile bounds hold
   across both desktop (4,000 tiles) and mobile (1,200 tiles) aspect ratios,
   not just the one viewport shape checked before.
3. **Time-based decay (was frame-based).** Replaced `intensity[i] * 0.94`
   (once per rendered frame, so decay rate depended on refresh rate) with
   `intensity[i] * Math.exp(-dt / DECAY_TAU)`, `DECAY_TAU = 0.28` (computed
   once per `update(dt)` call, not per tile). Pointer gain/radius are
   unchanged (`POINTER_GAIN = 2.5`, `POINTER_RADIUS = 0.22`) — only the
   decay multiplier changed, per the brief ("pointer glow unchanged").
4. **No additive floor.** Confirmed (and left a comment) that
   `material.colorNode = mix(unlitColor, observedColor, visibleIntensity)`
   has no constant added anywhere in the chain — at `intensity = 0` and
   breathing's trough (clamped at 0), `visibleIntensity` is exactly 0 and
   the tile renders as `--color-tile-unlit` (`#1a1f25`), untouched.
5. **`public/hero-poster.svg` regenerated** from the identical `layout()`
   math (`rows = round(sqrt(tileCount/aspect))`, `cols = round(rows *
   aspect)`, `cellSize`, `TILE_FILL = 0.82`) at the poster's own 16:9
   reference aspect (800×450) and `tileCount = 4000` (matching
   `DESKTOP_TILE_COUNT`), so first paint matches the live grid's tile size:
   `rows=47, cols=84, count=3948`, tile size `8.0px` on a `9.77px` pitch.
   Kept the sparse seeded cluster (identical `seededNoise()` +
   `SEED_RADIUS` condition as `scene.ts`'s initial fill) — 32 lit tiles.
   Rendering all 3,948 tiles as individual `<rect>`s (the previous approach)
   would be roughly 350KB at this density; instead all unlit tiles share one
   fill and are drawn as a single `<path>` (`M{x},{y}h{w}v{h}h{-w}Z` per
   tile), with only the 32 lit tiles as individual `<rect fill-opacity=...>`
   overlays (alpha-composited over the unlit path underneath, reproducing
   the shader's `mix(unlit, observed, intensity)` exactly). Result: **78,633
   bytes raw** (well under the 100KB budget), 12,499 bytes gzipped, valid
   XML (`python3 -c "import xml.dom.minidom as m; m.parse(...)"` → OK).
   Confirmed byte-identical between `public/hero-poster.svg` and
   `dist/hero-poster.svg` after build.

**Simulation numbers** (Node script mirroring `scene.ts`'s `layout()` +
`update()` + breathing math exactly; steps `dt=1/60` for 3 simulated seconds
from the seeded initial state, no pointer, `coherence=0`, then samples the
rendered `visibleIntensity = clamp(intensity + breathing, 0, 1)` at that
instant — the same methodology as the prior verification pass):

| case (tiles, grid) | mean | frac ≤ 0.06 | center peak |
|---|---|---|---|
| desktop 16:9 (4000, 47×84=3948) | 0.0131 | 97.1% | 0.2029 |
| desktop 1073/791 (4000, 54×73=3942) | 0.0140 | 96.1% | 0.2047 |
| desktop narrow 0.563 (4000, 84×47=3948) | 0.0199 | 91.3% | 0.2088 |
| mobile 9:16 (1200, 46×26=1196) | 0.0207 | 90.8% | 0.1969 |
| mobile 1:2 (1200, 49×25=1225) | 0.0216 | 90.4% | 0.2163 |

All cases: mean ≤ 0.05 (criterion 1, largest margin: 0.0216 vs. 0.05), at
least 90% of tiles ≤ 0.06 (criterion 1, tightest case: mobile 1:2 at 90.4%),
center island peak ≤ 0.25 within `CENTER_RADIUS = 0.35` (criterion 1, never
exceeds 0.217). Re-ran the desktop/mobile cases at `dt = 1/120` — mean and
peak shift by ≤1.5% relative to 60Hz (e.g. desktop 16:9: mean 0.0131→0.0130,
peak 0.2029→0.1999), confirming criterion 6 (60Hz/120Hz consistency).
Breathing amplitude bounds hold by construction (`sin()` is bounded to
[-1, 1] and multiplied by `mix(0.03, 0.08, coherence)`), satisfying
criterion 2's amplitude ceilings exactly. Pointer decay-from-1.0-to-0.05
takes 0.850s at 60Hz / 0.842s at 120Hz with the new `DECAY_TAU = 0.28`
(criterion 3/6), and a stationary pointer still settles at a non-saturated
`0.721` (criterion 3), both close to the pre-existing verified numbers.

Verification commands (all from `site/`, after `npm ci` — `node_modules` was
not present in this worktree):
- `npx astro check` → `0 errors, 0 warnings, 0 hints`.
- `npm run build` → `[build] Complete!`, 7 routes (pre-existing warnings
  about chunk size, the empty `i18n` collection, and the missing `404`
  content entry are unrelated to this change and were present before it).
- `npx astro preview --port 4322` + `curl -o /dev/null -w '%{http_code}'` →
  `200` for both `/` and `/hero-poster.svg`.
- Puppeteer is not installed in this worktree, so no real headless render
  was captured — per the task brief, relying on the Node simulation above
  plus the build/typecheck results instead.

## 2026-09-06 (second real-browser review: coverage, pointer, serenity)

Three tuning fixes from a real-browser review (Chrome, WebGPU, viewport
1088x792, canvas rect 1073x791), all in `src/hero/scene.ts` plus one
supporting change in `src/hero/mount.ts`. No change was needed to pointer
mapping or the clip-path shrink — both already read the container's live
`getBoundingClientRect()`, so a differently-shaped canvas is not their
problem.

1. **Coverage (tiles only spanned ~73% of canvas width).** Root cause: the
   grid was laid out assuming a square viewport (`cols = round(sqrt(N))`)
   and the camera's ortho bounds were only set to the real aspect ratio
   afterward, in `resize()`. The two never agreed once the real aspect
   ratio was not 1:1. Fixed by:
   - Passing the container's real aspect ratio into `createHeroScene()` at
     construction (`mount.ts` now reads `container.getBoundingClientRect()`
     before creating the scene, not just before the first `applySize()`).
   - A `layout(aspect)` function in `scene.ts`, called at construction and
     on every `resize()`, computing `rows = round(sqrt(tileCount /
     aspect))`, `cols = round(rows * aspect)`, and a single `cellSize =
     (frustumHeight * OVERFILL) / rows` — this keeps tiles exactly square
     while covering both axes, because `cols/rows ≈ aspect` by
     construction. `OVERFILL = 1.02` (2% overfill both axes, verified
     numerically below).
   - Tiles now carry their size via the instance matrix's scale component
     (`dummy.scale.set(cellSize, cellSize, 1)`) against a unit `PlaneGeometry(TILE_FILL,
     TILE_FILL)`, instead of baking a fixed size into the geometry — so a
     resize never needs to touch the geometry, only per-instance
     transforms.
   - `InstancedMesh` is now allocated with `HEADROOM = 1.4` (40%) more
     capacity than the target tile count, and `mesh.count` is set to the
     actual row×col product on every `layout()` call (three.js's
     `InstancedMesh.count` is a plain writable property the renderer reads
     at draw time — verified in `node_modules/three/src/objects/
     InstancedMesh.js`). `mesh.frustumCulled = false` since visibility is
     now managed via `count`, not the geometry's bounding sphere.
   - Verified numerically (not just by reading code) with a standalone
     Node script reproducing the exact layout math at aspect
     1073/791 = 1.357, tileCount = 4000: `rows=54, cols=73, count=3942`,
     grid x-range `±1.379` vs. frustum x-range `±1.357` (1.7% overfill),
     grid y-range `±1.02` vs. frustum `±1` (exactly 2% overfill — the
     first and last columns/rows land past the canvas edges, not short of
     them). Also checked portrait/ultrawide/mobile aspects (0.45–2.5) all
     stay within the 1.4x headroom allocation.
2. **Pointer saturation.** `POINTER_STRENGTH = 0.55` was added as a flat
   amount once per rendered frame (not per `pointermove`, which only ever
   stored the position — `setPointer()` never added intensity) — but a
   flat, non-time-scaled `+0.55` every frame saturates in ~2 frames
   regardless. Fixed: pointer influence is now `gain * falloff * dt`
   (`POINTER_GAIN = 2.5`, `POINTER_RADIUS = 0.22`, both exactly the values
   the review suggested), applied in `update(dt)` after the existing
   frame-based `× DECAY`. Simulated the steady state at a 60fps reference
   (`node -e` script, decay=0.94, dt=1/60): a stationary pointer settles at
   `0.694`, not saturation, and decay-only fade from 1.0 to 0.05 takes 49
   frames (~0.82 s) — matches "fades within ~1 s".
3. **Serenity.** `BREATH_AMPLITUDE` cut from `0.16` to `0.06` (the review's
   ceiling was `≤ 0.08`) — this was the actual cause of "bright green
   bands": breathing was applied to every tile in a region regardless of
   position, so a whole vertical band would light up together at the old
   amplitude. Ambient center glow retuned to the requested `peak ≈ 0.25`,
   `radius ≈ 0.35`: derived `CENTER_GAIN = 0.9` from the same steady-state
   simulation (`gain * dt / (1 - DECAY)` at 60fps reference settles at
   `0.250`, confirmed by the same script). Added a seeded-noise initial
   fill (`seededNoise()`, the identical hash used to generate
   `hero-poster.svg`) so tiles within `SEED_RADIUS = 0.22` of center start
   with a small nonzero intensity on the very first frame — continuing the
   poster's sparse-cluster look instead of a flash-to-black while the
   ambient glow ramps up from zero.
- Known limitation, unchanged from before and not addressed here: decay is
  frame-based (`× 0.94` once per rendered frame) rather than time-based, so
  the steady-state brightness derived above is only exact at the assumed
  60fps reference; a much higher or lower refresh rate will settle at a
  visibly different (though still non-saturated, still soft) brightness.
  This matches the original brief's own phrasing ("decays each frame") and
  was not asked to be fixed.
- Verification commands: `npx astro check` → 0 errors. `npm run build` →
  `[build] Complete!`, 7 routes. Restarted the preview
  (`pkill -f "astro preview"`, then `npx astro preview --port 4321`) —
  `curl -o /dev/null -w '%{http_code}' http://localhost:4321/` → `200`.
  Re-ran `git add -N site && pytest tests/test_public_language.py -q &&
  git reset -- site` → `3 passed`.
- Still not verified here: an actual rendered frame at the exact reported
  brightness/coverage in a live browser — the numeric simulations above
  reproduce the layout and decay/gain math exactly as written in
  `scene.ts`, but the coordinator's separate real-browser session is the
  one confirming the pixels.

## 2026-09-06 (hero build)

- Installed and pinned exact versions: `three@0.185.1`, `gsap@3.15.0`,
  `lenis@1.3.26`, `@types/three@0.185.4` (`npm i ... --save-exact`). Verified
  `three/webgpu` and `three/tsl` exist as package exports before writing any
  code (`node_modules/three/package.json` exports map, and the actual
  exported names in `node_modules/three/build/three.tsl.js` /
  `three.webgpu.js`). See `02-architecture.md` for the version and API
  verification notes and the one real deviation from the brief (CPU-driven
  intensity buffer instead of a GPU screen-space uniform, so the WebGL2
  fallback keeps working without compute shaders).
- Built `src/hero/{scene,motion,fallback,mount}.ts` (line counts: scene 154,
  motion 88, mount 95, fallback 47 — 384 lines total, slightly over the
  ~350 target; kept as-is rather than cutting comments that explain
  non-obvious choices).
  - `scene.ts`: InstancedMesh grid (4,000 desktop / 1,200 mobile, chosen by
    `matchMedia(max-width: 768px)` in `mount.ts`), six regions by column,
    per-instance intensity in a `Float32Array` pushed through
    `InstancedBufferAttribute` + TSL `instancedDynamicBufferAttribute`,
    static region index through `instancedBufferAttribute`. Colors read once
    from `src/styles/tokens.css` custom properties via `getComputedStyle`.
  - `motion.ts`: Lenis + `gsap.ticker` + `ScrollTrigger` drives the
    coherence uniform and a `clip-path: polygon(...)` shrink over the first
    viewport of scroll; `SplitText.create()` staggers headline words on
    load with a manual `<span>`-split fallback in a `catch`; navbar
    hide/show on scroll direction.
  - `fallback.ts`: `shouldAnimate()` checks
    `prefers-reduced-motion`, `hardwareConcurrency <= 2`, and
    `navigator.gpu` / `canvas.getContext('webgl2')` — never throws.
  - `mount.ts`: `await renderer.init()` in a try/catch, DPR capped at 1.5,
    `ResizeObserver` on the canvas container, pause/resume the render loop
    on `visibilitychange`, and a `dispose()` that removes every listener
    and disposes the renderer, geometry, and material.
- `public/hero-poster.svg`: generated programmatically (a small inline Node
  script, not by hand) — a 40x22 static tile grid with a sparse cluster of
  green "observed" tiles near the center, same palette as the live scene.
  78,283 bytes raw, 2,652 bytes gzipped.
- `src/pages/index.astro`: replaced the placeholder hero block with a
  `.hero-canvas-wrap` (fixed `aspect-ratio: 16/9`, `max-height: 640px` —
  zero CLS), containing the poster `<img>` (z-index above the canvas by
  default) and the `<canvas>` (z-index below). A fixed `<nav data-hero-navbar>`
  was added (none existed before) since the brief requires navbar
  hide/show-on-scroll behavior. Added a gated script: waits for
  `requestIdleCallback` (falls back to `setTimeout(0)`), then an
  `IntersectionObserver` on the canvas triggers
  `import('../hero/mount').then(m => m.default(canvas))`. Note: the canvas
  is never given the `hidden` attribute (which would remove its layout box
  and make it permanently non-intersecting for the observer) — instead the
  poster image stacks on top via z-index and `mount.ts` sets
  `poster.hidden = true` only after a successful `renderer.init()`. This
  also means the page is fully readable with JavaScript disabled: the
  poster is the default, always-visible layer with no JS involved.
- `src/styles/tokens.css`: created (did not exist before). Palette matches
  `05-ui-context.md` (`--color-bg`, `--color-tile-unlit`,
  `--color-tile-observed`, plus the warn/deny/ask accents for future UI).
- Verification commands run from `site/`:
  - `npm run build` → 7 routes, `[build] Complete!`.
  - `npx astro check` → **not run**: it requires installing
    `@astrojs/check` and `typescript` as new dependencies (interactive
    prompt), which was outside the dependency scope given for this task.
    Declined both prompts; recorded here as unverified rather than silently
    skipped.
  - `npm run preview -- --port 4321` + `curl localhost:4321/` → byte-identical
    to `dist/index.html` (3,647 bytes). Confirmed present: `<canvas
    id="hero-canvas">`, poster `src="/hero-poster.svg"`, the headline text,
    `pipx install hyodo`, and all three layer sections. Confirmed the hero
    chunk (`_astro/mount.*.js`) is not referenced by any `<script src>` in
    `dist/index.html` — it is only reached through the runtime `import()` in
    the gating script.
  - Hero chunk size: `dist/_astro/mount.*.js` — 991,424 bytes raw, 283,167
    bytes gzip (`gzip -c file | wc -c`), 231,844 bytes brotli. This bundles
    three's WebGPU renderer + TSL node system + gsap + lenis + the hero
    code; it is within the same order of magnitude as the brief's informal
    150–250 KB gz estimate, slightly above it.
  - `git add -N site && ... /Users/brnestrm/HyoDo/.venv/bin/python -m pytest
    tests/test_public_language.py -q && git reset -- site` → `3 passed`.
- Not verified (explicitly out of scope for this pass, no headless browser
  tool available): an actual rendered frame in a real browser (WebGPU or
  WebGL2), a 375px-viewport screenshot, a `prefers-reduced-motion`
  screenshot, and a Lighthouse/CLS measurement. These need a real browser
  and were not run — flagging per the workflow rule against unverified
  claims.
- Next: real-browser review pass (console errors, reduced-motion path,
  375px viewport, actual WebGPU/WebGL2 frame) before calling the hero
  feature reviewed; then Vercel project and domain.

## 2026-09-06 (typecheck + real-browser review fixes)

- Added `@astrojs/check@0.9.10` and `typescript@5.9.3` as exact-pinned
  devDependencies so `npx astro check` can actually run (see
  `02-architecture.md` for why: no `.d.ts` ships in `three` itself, and
  `astro build` does not type-check). `npx astro check` then caught 3 real
  errors in `scene.ts` — TS was widening the `'float'` literal passed to
  `instancedBufferAttribute`/`instancedDynamicBufferAttribute` to `string`,
  which drops the TSL `.mul()`/`.add()` node-arithmetic methods. Fixed by
  passing the type argument explicitly:
  `instancedBufferAttribute<'float'>(attr, 'float')`. `npx astro check` →
  `0 errors, 0 warnings, 0 hints` after the fix.
- Real-browser review (Chrome, WebGPU available) reported two problems,
  fixed both in `src/pages/index.astro`:
  1. **Poster never actually hid.** `mount.ts` sets `poster.hidden = true`
     on success, but the page's own `.hero-canvas-wrap img { display:
     block }` rule (author origin) beat the user-agent stylesheet's
     `[hidden] { display: none }` rule regardless of specificity — author
     rules always win over UA rules in the cascade. Fixed by adding an
     explicit `.hero-canvas-wrap img[hidden] { display: none; }` rule.
  2. **Hero was a boxed 16:9 panel above the fold, not full-viewport.**
     Restructured `header.hero` to `position: relative; min-height:
     100svh` (a fixed CSS value known before any script runs, so CLS stays
     0). `.hero-canvas-wrap` is now `position: absolute; inset: 0;
     object-fit: cover` — a full-bleed background layer (dropped the old
     `aspect-ratio`, `max-height`, `border-radius`, `margin`). Added a
     `.hero-scrim` layer (bottom-anchored `linear-gradient`) for text
     legibility over the tiles, and moved the headline/subline/install
     block into `.hero-content` (`position: absolute; left/right: 0;
     bottom: 4rem`, `.wrap` for max-width/centering) so they overlay the
     lower portion of the full-bleed hero instead of sitting in normal
     flow above it. No code change was needed in `mount.ts`/`scene.ts` for
     pointer mapping or the clip-path shrink: both already read
     `container.getBoundingClientRect()` from `canvas.parentElement`
     (`.hero-canvas-wrap`), which now simply reports the full-viewport
     rect instead of the old boxed one — the same code path is correct for
     either layout.
- Verification: `npm run build` → `[build] Complete!`, 7 routes.
  `npx astro check` → 0 errors. Re-ran the `dist/index.html` presence
  checks (canvas, poster, headline, install command, `.hero-scrim`,
  `.hero-content`, no blocking `/_astro/mount` script reference) — all
  pass. Restarted `npx astro preview --port 4321` (killed the prior
  instance first) for the coordinator's browser re-check; `curl -o /dev/null
  -w '%{http_code}'` → `200`.
- Still not verified by this pass: an actual rendered WebGPU/WebGL2 frame,
  a 375px screenshot, and Lighthouse/CLS numbers — no headless browser tool
  was available here; the coordinator's separate real-browser session is
  covering that.

## 2026-09-06

- Scaffold: Astro 7.2 + Starlight 0.42, five docs pages under `/docs/*`,
  placeholder landing page at `/`. `npm run build` → 7 routes.
  `pytest tests/test_public_language.py` → 3 passed.
- Decisions: hero concept A + C (unlit grid + six-pillar rhythm) with
  three.js WebGPU; GSAP + Lenis for motion; plain `.md` only.
- Next: implement `src/hero/` (scene, motion, fallback, mount), then replace
  the placeholder hero in `index.astro`, then Vercel project and domain.

## 2026-09-06 — Evidence graph follow-up

- Hardened routing first: a colliding orthogonal route retries the next row gap; shared collision sampling uses 2px steps, 1px cell inset and half-stroke margin.
- Added the dependency-free repository CDP verifier and CI preview/artifact steps for both `/evidence-graph/` and `/`, including independent path sampling and endpoint measurements.
- Docked the 5W1H panel beside the graph at 1280px; embedded the graph below the hero with a lazy mount and Docs/GitHub/PyPI navigation.
- Matched square hero tiles and decision colors; the scroll-driven clip and final-20% crossfade use measured graph geometry and a 14-instance handoff. Reserved graph height and unchanged poster/reduced-motion entry paths avoid introducing a mount-time layout jump by design.
- Verification actually run: `npx astro check` (11 files, 0 errors/warnings/hints), `npm run build` (9 pages), `node --check scripts/verify-evidence-graph.mjs`, `git diff --check`, and generated local documentation-link checks passed. Hero entry chunk grew 773 bytes gzip versus the pre-handoff build, below 2KB.
- Browser verification exited 1: Chrome could not expose a DevTools port in the sandbox. Preview on 4326 also exited before readiness; the owned preview process was stopped. No screenshots were produced or inspected. Keyboard, mobile overflow, live edge violations and endpoint deviation were NOT measured. CI was configured, not executed here. Lighthouse: not run (not on PATH); LCP/CLS remain unmeasured.
- Manual check pending outside the sandbox: handoff pattern lights 14 tiles at scroll end, with ALLOW green / ASK blue / DENY red / UNOBSERVED grey; inspect immediately before canvas opacity reaches zero. Check wide/mobile grid clipping, resize and reverse scroll on WebGPU and WebGL2. Exact pixel docking remains unverified; the implementation crossfades into a measured fixture mesh rather than morphing each original hero instance into a graph tile.

## 2026-09-06 — Evidence graph accessibility + landing JS budget

- Fixed the three failing production Lighthouse accessibility audits on `/evidence-graph/` (94 → 100 locally, matches production's 94 before this fix): `.node-label` was 9px `var(--color-text-dim)` (#8b929a), 3.0–3.6:1 on the tinted decision-cell backgrounds; raised to 11px `var(--color-text)` (#e6e8eb), which measures 6.1–9.1:1 against every ALLOW/ASK/DENY/UNOBSERVED/event tint (computed via WCAG relative luminance over each cell's `color-mix()` background). Labels that don't fit one line at 11px/82px (`path_inside_root`, `path_outside_root`) wrap to two lines (`-webkit-line-clamp: 2`, `overflow-wrap: anywhere`) instead of clipping; cell height grew 58px → 64px and the embed's pre-mount `min-height` reservation grew to match, so CLS stays 0.
- `aria-label` now leads with the same string `.node-label` shows (`accessibleCellName()` = `${shortLabel(ev)} — ${describeEvent(ev)}`, e.g. `"read_file — tool_call by agent:planner at step 1"`), fixing `label-content-name-mismatch` on the button itself. The schema/decision chip glyph (`P`/`C`/`R`/`✓`/`?`/`✕`/`—`) is still a second axe-visible-text source even under `aria-hidden` — that rule reads on-screen text, not the accessibility tree — so it's rendered as `::before { content: attr(data-glyph) }` CSS-generated content (not a DOM text node) instead of `chip.textContent`, which axe doesn't walk.
- Added `<main>` around `/evidence-graph/`'s content (nav stays outside) and moved `index.astro`'s existing `<main>` open tag up so it now wraps the `.eg-embed` section too, fixing `landmark-one-main` and "main contains the embedded section" on both pages.
- Landing JS budget: `initMotion` (GSAP + Lenis + ScrollTrigger + SplitText, ~52 KiB gzip) was a static import inside `hero/mount.ts`, so it rode along in the same chunk as three/webgpu and ran synchronously as soon as the hero mounted (essentially immediately, since the hero fills one viewport). Made it a dynamic `import('./motion')`, triggered on the first `scroll` event or once `.eg-embed` is within one viewport (`IntersectionObserver` `rootMargin: '100% 0px'`, matching the trigger `index.astro` already used for the graph module itself, which was tightened from `200px` to the same `100% 0px`). `dist/_astro/mount.*.js` dropped 994,423 → 852,869 bytes raw (284,275 → 231,885 bytes gzip) with the motion code split into its own `dist/_astro/motion.*.js` chunk (140,996 bytes raw / 52,772 bytes gzip). Re-measure on graph mount/resize is unchanged (`eg-ready` listener + GSAP's own resize handling).
- Verification actually run: `npx astro check` (11 files, 0/0/0) and `npm run build` (9 routes) after every edit; `npm run verify:evidence-graph -- http://localhost:4340 verify-output` exit 0 for both pages (keyboard, motion-gating, geometry, mobile, console all clean); Lighthouse (mobile + `--preset=desktop`, `--only-categories=accessibility,performance`) against the local preview for both pages — all four runs scored accessibility 100 / performance 100 locally, with `/` mobile TBT 68–80ms (was 270ms in production) and bootup 0.7–0.8s (was 1.1s in production); a same-machine before/after A/B (via `git stash`) on `/` mobile showed accessibility 94 → 100 on `/evidence-graph/` and TBT 80ms → 68–80ms (run-to-run noise) on `/`, confirming direction without claiming the local numbers reproduce production's stricter throttling. A CDP docking check (1440×1000, no `--disable-gpu`, `--enable-unsafe-swiftshader`, `Emulation.setFocusEmulationEnabled`) scrolled `/` so `.eg-embed`'s top neared 20% of viewport height and confirmed `#hero-canvas-wrap` opacity 0, `.eg-embed` opacity 1, 14 mounted cell buttons, and zero console errors on both pages. `pytest tests/test_public_language.py` → 3 passed.
- Known cosmetic nit, not fixed: `overflow-wrap: anywhere` can break `path_outside_root` mid-syllable (e.g. "ro" / "ot") rather than at the underscore, since the identifier has no space/hyphen for `word-break: break-word` to prefer. Functional (no clipping, no accessibility regression) but not typographically ideal; left as-is rather than risking the shared `shortLabel()` string (also used verbatim in the `aria-label`) with zero-width-space injection this pass.
