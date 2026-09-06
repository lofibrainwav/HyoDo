# 05 UI context

## Feel

Serene front, furious back. The page is calm, dark, and quiet. The hero
computes constantly but shows little: a field of unlit tiles that only light
up where they are observed. Nothing shouts. One headline, one install
command, one scroll.

## Hero scene (decided)

Concept A + C combined:

- **The unlit grid**: thousands of small tiles (InstancedMesh) on a plane,
  dim by default. Tiles near the cursor and near the viewport center light up
  toward verified green, then dim again after the cursor passes. Only what is
  observed is green.
- **Six-pillar rhythm**: the grid is divided into six regions, one per
  virtue. Each region breathes at its own rhythm. As the visitor scrolls, a
  coherence value rises and the rhythms synchronize.
- On scroll the canvas shrinks by `clip-path` into a centered polygon while
  the docs sections take over.

## Tokens

- Background `#0b0d10`. Text `#e6e8eb`. Muted `#8b929a`.
- Unlit tile `#1a1f25`. Observed green `#3ddc84`. Warning amber `#f5b400`.
  Deny red `#ff5c5c`. Ask blue `#5aa9ff`.
- Type: system UI stack for body; a single display face for the headline
  (Inter or Geist, loaded locally, `font-display: swap`).
- Motion: ease-out curves, 400–900 ms. Never bounce. Reduced motion means no
  motion.

## Evidence graph prototype (`/evidence-graph/`)

- Each event cell is a real `<button type="button" class="cell node">`
  with an `aria-label`, not a `<div>` — focusable and activatable by
  keyboard, not just mouse.
- Decision fill colors reuse `tokens.css` exactly: ALLOW =
  `--color-tile-observed`, ASK = `--color-ask`, DENY = `--color-deny`,
  UNOBSERVED = `--color-text-dim`. No new decision colors were invented.
- The side panel is `aria-live="polite"` and re-renders on every
  focus/hover; `Escape` clears it back to the placeholder without moving
  focus off the current cell.
- Motion budget is interaction-only: a cell hover/focus lift and the
  evidence-token animation both live entirely inside `@media
  (prefers-reduced-motion: no-preference)` — absent, not just
  un-transitioned, under reduced motion. Nothing animates ambiently.
- Edge geometry carries the parent/evidence distinction by shape (rounded
  elbow vs. bezier curve) and dash, never by color alone, so it survives
  a static screenshot and grayscale/colorblind viewing.

## Copy

- Headline: *When your AI says "done", HyoDo tells you whether that is true.*
- Subline: *Honest local guardrails for AI-assisted development. Unobserved
  is never green.*
- Install: `pipx install hyodo`
- Layer titles: *If you build with AI but cannot read the code* / *If you
  read the code* / *If you have to prove it*.

- The evidence graph is embedded below the landing hero and mounted lazily within 200px of the viewport.
- Hero-to-graph docking timing contract (`site/src/hero/motion.ts`): the
  handoff tile pattern is fully lit by 45% of the docking scroll range;
  the crossfade (hero canvas opacity 1→0, `.eg-embed` opacity 0→1) runs
  between 45% and 75% of that range; the timeline itself ends no later
  than the point where the `.eg-embed` section's top reaches 20% of the
  viewport height. Keep the real grid visible well before the section is
  fully in view — do not let the docking timeline reserve most of its
  range for opaque hero tiles.
- `.eg-embed` defaults to `opacity: 1` in CSS with no ambient dimming;
  only the docking script (WebGPU/WebGL2 hero running, no reduced motion)
  drives it toward 0 during the crossfade above. With JS disabled, the
  poster fallback, or `prefers-reduced-motion: reduce`, the section stays
  at `opacity: 1` and no docking timeline runs at all.
