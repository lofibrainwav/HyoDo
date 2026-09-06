# hyodo.app site

The public marketing/docs site for HyoDo, built with
[Astro](https://astro.build) and [Starlight](https://starlight.astro.build).

## Routing

- `/` is a hand-written landing page owned by `src/pages/index.astro`. It is
  a plain Astro page, not a Starlight page, so it is never overridden by
  Starlight's default splash template.
- All documentation content lives under `src/content/docs/docs/*.md` (note
  the doubled `docs/docs` — the outer `docs` is Starlight's fixed content
  collection root; the inner `docs` is a subdirectory inside it). Starlight's
  `docsLoader` derives each page's route from its path relative to the
  collection root, so a file at `src/content/docs/docs/quickstart.md`
  is served at `/docs/quickstart/`, `src/content/docs/docs/trust.md` at
  `/docs/trust/`, and so on.
- This keeps all prose content under a single `/docs/*` prefix without
  needing a custom Starlight route-prefix integration, while still using
  Starlight's content collection, sidebar, and search out of the box.
- The sidebar (`astro.config.mjs`) points at the `docs/<slug>` paths
  directly (for example `slug: 'docs/quickstart'`) so navigation matches
  the generated routes.

## Local development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output goes to `dist/`, with `dist/index.html` for the landing page and
`dist/docs/*/index.html` for each doc page.

## Deploying on Vercel

`site/vercel.json` is not present; instead, configure the following in the
Vercel project settings:

| Setting | Value |
| --- | --- |
| Root Directory | `site` |
| Framework Preset | Astro |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm ci` |

## CI

`.github/workflows/site.yml` runs `npm ci` and `npm run build` in this
directory on any pull request or push that touches `site/**`.
