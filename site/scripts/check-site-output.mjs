import { readdirSync, readFileSync } from 'node:fs';
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
if (!/<h1\b[^>]*id="page-title"[^>]*>\s*This page isn’t here\.\s*<\/h1>/.test(output)) {
	missing.push('404 heading');
}
if (!new RegExp(`<a\\b[^>]*href="/"[^>]*>[\\s\\S]*?${messages['404.action']}[\\s\\S]*?<\\/a>`).test(output)) {
	missing.push('home action link');
}
if (!/<a\b[^>]*href="\/docs\/quickstart\/"[^>]*>[\s\S]*?Read the quickstart[\s\S]*?<\/a>/.test(output)) {
	missing.push('quickstart recovery link');
}
if (!/<main\b[^>]*>[\s\S]*?<\/main>/.test(output) || !/<nav\b[^>]*aria-label="Primary navigation"/.test(output)) {
	missing.push('semantic landmarks');
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

/*
 * Hero layout contract.
 *
 * The hero copy used to be `position: absolute; bottom: 4rem`, which took it out
 * of flow: the section could not grow to fit it, so on a 320px-wide screen or a
 * short landscape window the heading was pushed above the top of the viewport
 * entirely, and the fixed navbar covered whatever was left. Keeping the copy in
 * flow is the fix, so assert the shape that makes it true rather than trusting a
 * comment to survive the next edit.
 *
 * This reads the built stylesheet, not the source, because the built stylesheet
 * is what a visitor actually receives. It is a structural check: it does not
 * measure pixels. Geometry is verified against a served build.
 */
const astroDir = join(root, '..', 'dist', '_astro');
const homepageCss = readdirSync(astroDir)
	.filter((name) => /^index\..*\.css$/.test(name))
	.map((name) => readFileSync(join(astroDir, name), 'utf8'))
	.join('\n');
const heroMissing = [];

if (!homepageCss) heroMissing.push('no built homepage stylesheet found');

// The homepage hero is the one that reserves a full viewport; other pages
// define their own .hero with a different scope hash.
const heroRule = homepageCss.match(/\.hero:where\([^)]*\)\{([^}]*min-height:100svh[^}]*)\}/);
const contentRules = [...homepageCss.matchAll(/\.hero-content:where\([^)]*\)\{([^}]*)\}/g)];

if (!heroRule) {
	heroMissing.push('no .hero rule reserving min-height:100svh');
} else {
	const declarations = heroRule[1];
	if (!/padding-top:var\(--navbar-height\)/.test(declarations)) {
		heroMissing.push('.hero must reserve --navbar-height so the fixed navbar cannot cover the copy');
	}
	if (/(^|;)overflow:hidden/.test(declarations)) {
		heroMissing.push('.hero must not clip; copy that outgrows a short viewport would be cut off');
	}
}

if (contentRules.length === 0) {
	heroMissing.push('no .hero-content rule found');
}
for (const [, declarations] of contentRules) {
	if (/position:absolute/.test(declarations)) {
		heroMissing.push('.hero-content must stay in flow; position:absolute stops .hero growing to fit it');
	}
}

if (!/--navbar-height:/.test(homepageCss)) {
	heroMissing.push('--navbar-height must be declared, not estimated at each use');
}

if (heroMissing.length > 0) {
	throw new Error(`Hero layout contract failed: ${heroMissing.join('; ')}`);
}

console.log('Static 404 and homepage output contracts: PASS');
