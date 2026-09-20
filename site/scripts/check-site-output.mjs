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

// Sidebar label contract. A visitor who clicks a sidebar entry and lands on a
// page with a different heading cannot tell whether they arrived in the right
// place. The audit of 2026-09-19 found exactly one such pair — "Philosophy →
// Math → Code" pointing at a page titled "From values to evidence" — so the
// agreement is asserted here rather than left to review.
const configSource = readFileSync(new URL('../astro.config.mjs', import.meta.url), 'utf8');
const sidebarEntries = [...configSource.matchAll(/label:\s*'((?:[^'\\]|\\.)*)'\s*,\s*slug:\s*'([^']+)'/g)]
	.map(([, label, slug]) => ({ label: label.replace(/\\'/g, "'"), slug }));

const labelMismatches = [];
if (sidebarEntries.length === 0) {
	labelMismatches.push('no sidebar entries with a slug were found; the label contract did not run');
}
for (const { label, slug } of sidebarEntries) {
	const pagePath = new URL(`../src/content/${slug.startsWith('docs/') ? 'docs/' : ''}${slug}.md`, import.meta.url);
	let source;
	try {
		source = readFileSync(pagePath, 'utf8');
	} catch {
		labelMismatches.push(`${slug}: sidebar points at a page that does not exist`);
		continue;
	}
	const title = source.match(/^title:\s*(.+)$/m);
	if (!title) {
		labelMismatches.push(`${slug}: page has no frontmatter title to compare the sidebar label against`);
		continue;
	}
	const pageTitle = title[1].trim().replace(/^['"]|['"]$/g, '');
	if (pageTitle !== label) {
		labelMismatches.push(`${slug}: sidebar says "${label}" but the page is titled "${pageTitle}"`);
	}
}

if (labelMismatches.length > 0) {
	throw new Error(`Sidebar label contract failed: ${labelMismatches.join('; ')}`);
}

// Current-version contract. The audit of 2026-09-19 found the storefront calling
// 4.19.8 the current public package while VERSION, the latest tag and PyPI all
// said 4.19.9, so a released version shipped a page describing the previous one.
// Only sentences that assert what is current are checked. Historical readings —
// the 4.19.5 snapshot table, "before 4.19.6", a link to an older release receipt
// — are legitimate and must keep their own versions. Each anchor is also
// required to match at least once, so rewording a claim fails the build instead
// of silently removing it from coverage.
const currentVersion = readFileSync(join(root, '..', '..', 'VERSION'), 'utf8').trim();
const currencyAnchors = [
	{
		what: 'homepage public-version line',
		source: homepage,
		pattern: /Public version:\s*<strong[^>]*>HyoDo\s+([\d.]+)<\/strong>/g,
	},
	{
		what: 'current-state summary sentence',
		source: readFileSync(join(root, '..', 'src', 'content', 'docs', 'docs', 'current-state.md'), 'utf8'),
		pattern: /HyoDo \*\*([\d.]+)\*\* is the current public package/g,
	},
	{
		what: 'current-state latest-package bullet',
		source: readFileSync(join(root, '..', 'src', 'content', 'docs', 'docs', 'current-state.md'), 'utf8'),
		pattern: /Latest public package:\s*\*\*([\d.]+)\*\*/g,
	},
];

const currencyFailures = [];
for (const { what, source, pattern } of currencyAnchors) {
	const found = [...source.matchAll(pattern)];
	if (found.length === 0) {
		currencyFailures.push(`${what}: no longer matches; reword the contract here or the claim goes unchecked`);
		continue;
	}
	for (const [, claimed] of found) {
		if (claimed !== currentVersion) {
			currencyFailures.push(`${what}: claims ${claimed} is current, but VERSION says ${currentVersion}`);
		}
	}
}

if (currencyFailures.length > 0) {
	throw new Error(`Current-version contract failed: ${currencyFailures.join('; ')}`);
}

// Public-language contract. Internal project lineage must not leak back into
// product-facing source or visitor-visible generated HTML. Stable URL paths
// such as /docs/acl/ and academic URL identifiers are not visible text, so
// they remain compatible without weakening this check.
const repoRoot = join(root, '..', '..');
const publicSourceFiles = [
	join(repoRoot, 'README.md'),
	join(repoRoot, 'PHILOSOPHY.md'),
	join(repoRoot, 'docs', 'PRODUCT_BOUNDARY.md'),
	join(repoRoot, 'site', 'context', '01-project-overview.md'),
	...[
		'product-boundary.md',
		'why-hyodo.md',
		'trust.md',
		'philosophy.md',
		'current-state.md',
		'roadmap.md',
		'research.md',
		'friction-contribution.md',
		'acl.md',
	].map((name) => join(repoRoot, 'site', 'src', 'content', 'docs', 'docs', name)),
];

const publicBuiltFiles = [
	'index.html',
	...[
		'product-boundary',
		'why-hyodo',
		'trust',
		'philosophy',
		'current-state',
		'roadmap',
		'research',
		'friction-contribution',
		'acl',
	].map((slug) => join('docs', slug, 'index.html')),
].map((rel) => join(repoRoot, 'site', 'dist', rel));

const forbiddenPublicTerms = [
	['KINGDOM', /\\bKINGDOM\\b/],
	['BB', /\\bBB\\b/],
	['EROS', /\\bEROS\\b/],
	['HYOGOOK', /\\bHYOGOOK\\b/],
	['Wisdom Reflex', /Wisdom Reflex/],
	['Adaptive Collaboration Layer', /Adaptive Collaboration Layer/],
	['ACL', /\\bACL\\b/],
];

const stripMarkdownDestinations = (text) => text.replace(/\\]\\([^)]*\\)/g, ']');
const visibleHtmlText = (html) => html
	.replace(/<script\\b[\\s\\S]*?<\\/script>/gi, ' ')
	.replace(/<style\\b[\\s\\S]*?<\\/style>/gi, ' ')
	.replace(/<[^>]+>/g, ' ')
	.replace(/&nbsp;|&#160;/g, ' ');

const publicLanguageFailures = [];
for (const file of publicSourceFiles) {
	const text = stripMarkdownDestinations(readFileSync(file, 'utf8'));
	for (const [label, pattern] of forbiddenPublicTerms) {
		if (pattern.test(text)) publicLanguageFailures.push(file + ': visitor-facing source contains ' + label);
	}
}
for (const file of publicBuiltFiles) {
	const text = visibleHtmlText(readFileSync(file, 'utf8'));
	for (const [label, pattern] of forbiddenPublicTerms) {
		if (pattern.test(text)) publicLanguageFailures.push(file + ': generated visible text contains ' + label);
	}
}

if (publicLanguageFailures.length > 0) {
	throw new Error('Public-language contract failed: ' + publicLanguageFailures.join('; '));
}

console.log(`Sidebar label contract: PASS (${sidebarEntries.length} entries agree with their page titles)`);
console.log(`Current-version contract: PASS (${currencyAnchors.length} anchors agree with VERSION ${currentVersion})`);
console.log('Public-language contract: PASS (source + generated visible text)');\nconsole.log('Static 404 and homepage output contracts: PASS');
