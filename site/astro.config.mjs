// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://hyodo.app',
	// Keep the strict `style-src 'self'` policy effective: Astro's default
	// `auto` may inline small global stylesheets as blocked `<style>` elements.
	build: { inlineStylesheets: 'never' },
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
			// Sidebar labels must match each page's frontmatter `title`. A visitor
			// who clicks "Philosophy → Math → Code" and lands on a page headed
			// "From values to evidence" cannot tell whether they arrived in the
			// right place; site/scripts/check-site-output.mjs asserts the match.
			sidebar: [
				{
					label: 'Start here',
					items: [
						{ label: 'Quickstart', slug: 'docs/quickstart' },
						{ label: 'A worked result', slug: 'docs/worked-example' },
						{ label: 'Why HyoDo', slug: 'docs/why-hyodo' },
					],
				},
				{
					label: 'Scope and boundaries',
					items: [
						{ label: 'Product boundary', slug: 'docs/product-boundary' },
						{ label: 'From values to evidence', slug: 'docs/philosophy' },
						{ label: 'Trust', slug: 'docs/trust' },
					],
				},
				{
					label: 'Using HyoDo',
					items: [
						{ label: 'Connect', slug: 'docs/connect' },
						{ label: 'Inspect', slug: 'docs/inspect' },
						{ label: 'Evidence Graph', slug: 'docs/evidence-graph' },
						{ label: 'Graph Export', slug: 'docs/graph-export' },
						{ label: 'Eye', slug: 'docs/eye' },
						{ label: 'Skills', slug: 'docs/skills' },
						{ label: 'Runtime identity v1', slug: 'docs/runtime-identity' },
					],
				},
				{
					label: 'Project',
					items: [
						{ label: 'Roadmap', slug: 'docs/roadmap' },
						{ label: 'Research', slug: 'docs/research' },
						{ label: 'Friction Contribution', slug: 'docs/friction-contribution' },
					],
				},
			],
		}),
	],
});
