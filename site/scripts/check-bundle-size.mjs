import { readFileSync, readdirSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
const assetsDir = join(root, '..', 'dist', '_astro');
const maxGzipBytes = 275_000;
const assets = readdirSync(assetsDir)
	.filter((name) => name.endsWith('.js'))
	.map((name) => ({
		name,
		bytes: statSync(join(assetsDir, name)).size,
		gzipBytes: gzipSync(readFileSync(join(assetsDir, name))).length,
	}))
	.sort((a, b) => b.gzipBytes - a.gzipBytes);

if (assets.length === 0) {
	throw new Error(`No JavaScript assets found in ${assetsDir}`);
}

const largest = assets[0];
console.log(
	`JavaScript gzip budget: largest ${largest.name} is ${largest.gzipBytes} bytes ` +
	`(${largest.bytes} minified), limit ${maxGzipBytes} bytes`,
);

const oversized = assets.filter((asset) => asset.gzipBytes > maxGzipBytes);
if (oversized.length > 0) {
	for (const asset of oversized) {
		console.error(`OVER BUDGET: ${asset.name}: ${asset.gzipBytes} gzip bytes`);
	}
	process.exitCode = 1;
}
