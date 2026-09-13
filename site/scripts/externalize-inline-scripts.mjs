import { createHash } from 'node:crypto';
import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = fileURLToPath(new URL('../dist/', import.meta.url));
const ASSET_DIR = join(DIST, '_csp');
const SCRIPT_RE = /<script([^>]*)>([\s\S]*?)<\/script>/g;
const TAG_STYLE_RE = /<([A-Za-z][^>]*?\sstyle="[^"]*"[^>]*)>/g;
const STYLE_ATTR_RE = /\sstyle="([^"]*)"/;

async function htmlFiles(directory) {
	const entries = await readdir(directory, { withFileTypes: true });
	const files = [];
	for (const entry of entries) {
		const path = join(directory, entry.name);
		if (entry.isDirectory()) files.push(...(await htmlFiles(path)));
		else if (entry.isFile() && entry.name.endsWith('.html')) files.push(path);
	}
	return files;
}

await mkdir(ASSET_DIR, { recursive: true });
const files = await htmlFiles(DIST);
const emitted = new Map();
const emittedStyles = new Map();
let replaced = 0;
let styleAttributesReplaced = 0;

for (const file of files) {
	const original = await readFile(file, 'utf8');
	let updated = original.replace(SCRIPT_RE, (full, attrs, body) => {
		if (/\bsrc\s*=/.test(attrs)) return full;
		if (/<\/script/i.test(body)) {
			throw new Error(`Cannot externalize script containing </script>: ${relative(DIST, file)}`);
		}
		const hash = createHash('sha256').update(body, 'utf8').digest('hex').slice(0, 16);
		const assetName = `inline-${hash}.js`;
		if (!emitted.has(assetName)) {
			emitted.set(assetName, body);
		}
		replaced += 1;
		return `<script${attrs} src="/_csp/${assetName}"></script>`;
	});
	updated = updated.replace(TAG_STYLE_RE, (full) => {
		const match = full.match(STYLE_ATTR_RE);
		if (!match) return full;
		const declaration = match[1];
		const hash = createHash('sha256').update(declaration, 'utf8').digest('hex').slice(0, 16);
		const className = `csp-style-${hash}`;
		emittedStyles.set(className, declaration);
		styleAttributesReplaced += 1;
		const withoutStyle = full.replace(STYLE_ATTR_RE, '');
		const classMatch = withoutStyle.match(/\sclass="([^"]*)"/);
		if (classMatch) {
			return withoutStyle.replace(
				/\sclass="([^"]*)"/,
				` class="${classMatch[1]} ${className}"`,
			);
		}
		return withoutStyle.replace(/>$/, ` class="${className}">`);
	});
	if (updated !== original) await writeFile(file, updated, 'utf8');
}

for (const [name, body] of emitted) {
	await writeFile(join(ASSET_DIR, name), body, 'utf8');
}
if (emittedStyles.size > 0) {
	const css = [...emittedStyles.entries()]
		.map(([className, declaration]) => `.${className}{${declaration}}`)
		.join('\n');
	await writeFile(join(ASSET_DIR, 'inline-styles.css'), css, 'utf8');
	for (const file of files) {
		const html = await readFile(file, 'utf8');
		if (!html.includes('/_csp/inline-styles.css')) {
			await writeFile(
				file,
				html.replace('</head>', '<link rel="stylesheet" href="/_csp/inline-styles.css"></head>'),
				'utf8',
			);
		}
	}
}

console.log(
	`Externalized ${replaced} inline scripts and ${styleAttributesReplaced} style attributes ` +
		`into ${emitted.size} JS assets and ${emittedStyles.size} CSS rules.`,
);
