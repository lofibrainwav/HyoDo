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

## Copy

- Headline: *When your AI says "done", HyoDo tells you whether that is true.*
- Subline: *Honest local guardrails for AI-assisted development. Unobserved
  is never green.*
- Install: `pipx install hyodo`
- Layer titles: *If you build with AI but cannot read the code* / *If you
  read the code* / *If you have to prove it*.
