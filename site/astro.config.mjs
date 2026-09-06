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
				{ label: 'Roadmap', slug: 'docs/roadmap' },
				{ label: 'Trust', slug: 'docs/trust' },
			],
		}),
	],
});
