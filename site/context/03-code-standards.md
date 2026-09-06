# 03 Code standards

- TypeScript strict for every `.ts` file under `src/hero/`. Astro components
  keep their scripts as `<script>` modules that import from `src/hero/`.
- One module, one job: `scene.ts` (objects and materials), `motion.ts`
  (scroll and text), `fallback.ts` (capability checks, poster), `mount.ts`
  (lazy init, resize, visibility, teardown).
- No global mutable state outside the mount function. Every listener that is
  added is removed in a returned `dispose()`.
- Constants live at the top of the file with a comment stating the unit and
  the reason for the value (tile count, DPR cap, breakpoints).
- Colors and spacing come from CSS custom properties in `src/styles/tokens.css`
  and are read into the scene once at mount, not hardcoded twice.
- Plain `.md` for content. No `.mdx`. The repository language gate scans every
  tracked `.md` and `.py` file for non-English prose.
- Markdown lines stay under 80 characters except tables and URLs.
- English only in code, comments, and copy.

- Astro trims whitespace-only text nodes next to inline tags — keep `text <code>x</code> text` joins on one source line.
- Verify pages headlessly through CDP device emulation (`Emulation.setDeviceMetricsOverride`), not `--window-size` screenshots, which do not honour the mobile viewport.
