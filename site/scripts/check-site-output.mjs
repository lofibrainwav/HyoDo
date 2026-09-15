import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
const output = readFileSync(join(root, '..', 'dist', '404.html'), 'utf8');
const messages = JSON.parse(readFileSync(join(root, '..', 'src', 'content', 'i18n', 'en.json'), 'utf8'));
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

console.log('Static 404 output contract: PASS');
