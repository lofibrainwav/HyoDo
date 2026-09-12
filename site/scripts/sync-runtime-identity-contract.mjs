import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const destination = resolve(import.meta.dirname, '../public/schemas');
const files = ['runtime-identity-v1.schema.json', 'runtime-identity-v1.pin.json'];

await mkdir(destination, { recursive: true });
for (const file of files) {
	const source = await readFile(resolve(root, 'schemas', file));
	await writeFile(resolve(destination, file), source);
}

// Keep the generated public route byte-identical to the repository contract.
await readFile(resolve(destination, files[0]));
