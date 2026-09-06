# 02 Architecture

## Stack

- Astro (static output) with Starlight for `/docs/*`.
- `src/pages/index.astro` owns `/` and is not a Starlight page.
- three.js `three/webgpu` + `three/tsl` for the hero canvas, with automatic
  WebGL2 fallback. No React, no Tailwind.
- GSAP (ScrollTrigger, SplitText) and Lenis for scroll and text motion.
- Deployed to Vercel: root directory `site`, build `npm run build`, output
  `dist`, install `npm ci`.

### Hero dependency versions (pinned exact, 2026-09-06)

- `three` 0.185.1 — confirmed `three/webgpu` (`WebGPURenderer`, core classes)
  and `three/tsl` (`uniform`, `time`, `mix`, `sin`, `clamp`,
  `instancedBufferAttribute`, `instancedDynamicBufferAttribute`, etc.) both
  exist as package exports in this version (`node_modules/three/package.json`
  `exports` map: `"./webgpu"` and `"./tsl"`).
- `@types/three` 0.185.4 — matched to the `three` version above.
- `gsap` 3.15.0 — ScrollTrigger and SplitText both ship in the base package
  (`gsap/ScrollTrigger`, `gsap/SplitText`) and are free to use un-licensed
  since 3.13; confirmed by reading `node_modules/gsap/src/SplitText.ts`
  (`static create()`, `.words`, `.revert()` all present); `motion.ts` uses
  `SplitText.create()`.
- `lenis` 1.3.26 — current package name (the old `@studio-freight/lenis` is
  retired). Default export is the `Lenis` class; `lenis.raf(time)` expects a
  millisecond timestamp, driven from `gsap.ticker` (`time * 1000`), per the
  documented Lenis + GSAP integration pattern.
- `@astrojs/check` 0.9.10 and `typescript` 5.9.3 (devDependencies, exact
  pins). Not in the original list; added because `03-code-standards.md`
  requires TypeScript strict for every `.ts` file, and there was no way to
  actually check that without them — `three` ships no `.d.ts` files at all
  (types come entirely from `@types/three`), and `astro build` type-strips
  without type-checking. `typescript@7.0.2` (latest) was tried first and
  rejected: `@astrojs/check@0.9.10`'s peer range is `^5.0.0 || ^6.0.0`, so
  5.9.3 was pinned instead. Dev-only; no runtime bundle impact. Running
  `npx astro check` with this in place caught three real type errors in
  `scene.ts` (see below) that `npm run build` alone did not.

### Hero implementation notes (deviations from the initial brief)

- **No GPU compute / storage-buffer feedback loop.** Per-tile intensity
  needs to persist and decay across frames (glow fades after the pointer
  passes), which requires per-instance state carried between frames. A
  WebGPU compute shader could do this, but compute shaders are not
  available on the automatic WebGL2 fallback, so it would break the
  fallback path. Instead, `src/hero/scene.ts` keeps a plain
  `Float32Array` per instance, updates it on the CPU each frame (decay,
  pointer distance, center distance), and pushes it to the GPU as a
  `THREE.InstancedBufferAttribute` read in TSL via
  `instancedDynamicBufferAttribute`. The region index (0..5) is static and
  uses `instancedBufferAttribute` (no per-frame upload). This is why the
  "screen-space distance uniform" in the brief became a CPU-side distance
  calculation in grid space instead of a GPU uniform.
- `time`, `uniform`, `mix`, `sin`, `clamp`, `float` are all real exports of
  `three/tsl` at this version — verified against
  `node_modules/three/build/three.tsl.js` before use, not assumed from the
  brief.
- `mount.ts` does not set `alpha: true` on `WebGPURenderer`; the scene sets
  `scene.background` from `--color-bg` instead, so the small gaps between
  tiles (`TILE_FILL`) render the page background instead of relying on
  canvas transparency.
- The hero JS chunk (three + gsap + lenis + hero code, minified) is
  ~991 KB raw, ~283 KB gzip / ~227 KB brotli as of this build. It is loaded
  only via a runtime `import()` gated on `requestIdleCallback` +
  `IntersectionObserver`, never referenced from the initial HTML.
- **TSL generic type-argument gotcha found by `astro check`**: `three`
  ships no `.d.ts` at all; `@types/three` types `instancedBufferAttribute`
  and `instancedDynamicBufferAttribute` as
  `<TNodeType>(array, type?: TNodeType | null, ...) => Node<TNodeType>`.
  Calling `instancedBufferAttribute(attr, 'float')` lets TS infer
  `TNodeType` from a bare string-literal argument, which **widens to
  `string`**, not `'float'` — so the result loses the `.mul()`/`.add()`
  arithmetic overloads that only exist on `Node<'float'>` (via declaration
  merging keyed on the literal type). Fix used in `scene.ts`: pass the type
  argument explicitly — `instancedBufferAttribute<'float'>(attr, 'float')`.
  Caught 3 real type errors this way; `npm run build` alone did not surface
  them since esbuild strips types without checking them.

## Boundaries

- Content SSOT lives in the repository root (`README.md`, `PHILOSOPHY.md`,
  `ROADMAP.md`, `SECURITY.md`). Site pages summarize and link; they never
  invent claims.
- The hero is progressive enhancement. The page must be complete and
  readable with JavaScript disabled or with `prefers-reduced-motion`.
- The hero bundle is loaded lazily after the headline is painted. It never
  blocks LCP.
- No network calls from the page except loading its own assets.

## Directory rules

```text
site/
  context/                 six context files (this directory)
  src/pages/index.astro    landing page shell, hero mount point
  src/hero/                three.js scene, TSL nodes, motion, fallbacks
  src/styles/              global CSS and tokens
  src/content/docs/docs/   Starlight pages (plain .md only)
  public/                  static assets, poster image for fallback
```
