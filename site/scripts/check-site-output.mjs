import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
const output = readFileSync(join(root, '..', 'dist', '404.html'), 'utf8');
const homepage = readFileSync(join(root, '..', 'dist', 'index.html'), 'utf8');
const messages = JSON.parse(readFileSync(join(root, '..', 'src', 'content', 'i18n', 'en.json'), 'utf8'));
const homepageMissing = [];
const required = [
	'<meta name="robots" content="noindex"',
	'<link rel="canonical" href="https://hyodo.app/404.html"',
	messages['404.text'],
];

const missing = required.filter((fragment) => !output.includes(fragment));
if (!/<h1\b[^>]*>\s*Page not found\s*<\/h1>/.test(output)) {
	missing.push('404 heading');
}
if (!new RegExp(`<a\\b[^>]*href="/"[^>]*>\\s*${messages['404.action']}\\s*<\\/a>`).test(output)) {
	missing.push('home action link');
}
if (missing.length > 0) {
	throw new Error(`Generated 404 page is missing required output: ${missing.join('; ')}`);
}

const homepageRequired = [
	'<link rel="canonical" href="https://hyodo.app/"',
	'<meta property="og:title"',
	'<meta property="og:description"',
	'<meta property="og:url" content="https://hyodo.app/"',
	'<meta name="twitter:card"',
];
homepageMissing.push(...homepageRequired.filter((fragment) => !homepage.includes(fragment)));
if (!/<a\b[^>]*class="[^"]*\bskip-link\b[^"]*"[^>]*href="#main-content"[^>]*>Skip to content<\/a>/.test(homepage)) {
	homepageMissing.push('skip link');
}
if (!/<main\b[^>]*id="main-content"/.test(homepage)) homepageMissing.push('main landmark');
if (!/<p\b[^>]*id="copy-status"[^>]*role="status"[^>]*aria-live="polite"/.test(homepage)) {
	homepageMissing.push('accessible copy status');
}
if (!/<a\b[^>]*class="[^"]*\bquickstart-link\b[^"]*"[^>]*href="\/docs\/quickstart\/"/.test(homepage)) {
	homepageMissing.push('hero quickstart link');
}

const navLinks = homepage.match(/<div class="nav-links[^\"]*">([\s\S]*?)<\/div>/);
const navHrefs = [...(navLinks?.[1] ?? '').matchAll(/<a\b[^>]*href="([^"]+)"/g)].map((match) => match[1]);
const expectedNavHrefs = [
	'/docs/quickstart/',
	'https://github.com/lofibrainwav/HyoDo',
	'https://pypi.org/project/hyodo/',
];
if (JSON.stringify(navHrefs) !== JSON.stringify(expectedNavHrefs)) {
	homepageMissing.push(`primary navigation must contain exactly Docs, GitHub, PyPI; found ${navHrefs.join(', ') || 'none'}`);
}
if (/<style\b/i.test(homepage)) homepageMissing.push('inline style element conflicts with strict CSP');
if (!/<h1\b[^>]*id="hero-heading"/.test(homepage) || !/<canvas\b[^>]*aria-hidden="true"/.test(homepage)) {
	homepageMissing.push('accessible hero heading or decorative canvas contract');
}
if (homepageMissing.length > 0) {
	throw new Error(`Generated homepage is missing required output: ${homepageMissing.join('; ')}`);
}

console.log('Static 404 and homepage output contracts: PASS');
