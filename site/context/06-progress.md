# 06 Progress

State of the site, newest first. Every entry names the command that proved
it.

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
