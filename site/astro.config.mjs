// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://hyodo.app',
	// Ship source maps: the hero bundle is large and the repository is public.
	vite: { build: { sourcemap: true } },
	integrations: [
		starlight({
			title: 'HyoDo',
			customCss: ['./src/styles/starlight.css'],
			head: [
				{
					// Default to the dark theme (the landing page is always dark) until
					// the visitor picks one with the theme selector.
					tag: 'script',
					content:
						"try{if(!localStorage.getItem('starlight-theme')){localStorage.setItem('starlight-theme','dark')}}catch(e){}",
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
				{ label: 'Research', slug: 'docs/research' },
				{ label: 'Roadmap', slug: 'docs/roadmap' },
				{ label: 'Trust', slug: 'docs/trust' },
			],
		}),
	],
});
