// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://hyodo.app',
	// Ship source maps: the hero bundle is large and the repository is public.
	vite: {
		build: {
			sourcemap: true,
			// The hero renderer is intersection-lazy. Its ~915 KB minified chunk
			// is ~248 KB over gzip; scripts/check-bundle-size.mjs enforces the
			// user-transfer budget instead of Vite's source-byte heuristic.
			chunkSizeWarningLimit: 1000,
		},
	},
	integrations: [
		starlight({
			title: 'HyoDo',
			disable404Route: true,
			customCss: ['./src/styles/starlight.css'],
			head: [
				{
					// Default to the dark theme through an external asset so the
					// repository-owned bootstrap does not require unsafe-inline.
					tag: 'script',
					attrs: { src: '/theme-default.js' },
				},
			],
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/lofibrainwav/HyoDo' },
			],
			// The "/" route is a custom landing page owned by src/pages/index.astro,
			// not Starlight's default splash. Docs content is nested one level
			// under src/content/docs/docs/ so generated routes land at /docs/*
			// (see site/README.md for the full explanation).
			sidebar: [
				{ label: 'Quickstart', slug: 'docs/quickstart' },
				{ label: 'Why HyoDo', slug: 'docs/why-hyodo' },
				{ label: 'Philosophy → Math → Code', slug: 'docs/philosophy' },
				{ label: 'Evidence Graph', slug: 'docs/evidence-graph' },
				{ label: 'Skills', slug: 'docs/skills' },
				{ label: 'Inspect', slug: 'docs/inspect' },
				{ label: 'Graph Export', slug: 'docs/graph-export' },
				{ label: 'Eye', slug: 'docs/eye' },
				{ label: 'Connect', slug: 'docs/connect' },
				{ label: 'Friction Contribution', slug: 'docs/friction-contribution' },
				{ label: 'ACL — Adaptive Collaboration Layer', slug: 'docs/acl' },
				{ label: 'Research', slug: 'docs/research' },
				{ label: 'Roadmap', slug: 'docs/roadmap' },
				{ label: 'Trust', slug: 'docs/trust' },
				{ label: 'Runtime identity', slug: 'docs/runtime-identity' },
				{ label: 'Product boundary', slug: 'docs/product-boundary' },
			],
		}),
	],
});
