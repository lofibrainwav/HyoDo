// The unlit grid: an InstancedMesh field that only glows where it is
// observed (near the pointer, near the viewport center) and fades otherwise.
// Per-instance intensity lives in a CPU-updated InstancedBufferAttribute
// (not a GPU compute/storage buffer) so the same code path works on the
// automatic WebGL2 fallback, which has no compute shaders.
import {
	Scene,
	OrthographicCamera,
	InstancedMesh,
	PlaneGeometry,
	InstancedBufferAttribute,
	MeshBasicNodeMaterial,
	Object3D,
	Color,
	Vector4,
} from 'three/webgpu';
import {
	uniform,
	time,
	mix,
	sin,
	clamp,
	float,
	instancedBufferAttribute,
	instancedDynamicBufferAttribute,
} from 'three/tsl';

const REGION_COUNT = 6; // one region per HyoDo virtue pillar
const TILE_FILL = 0.82; // tile size as a fraction of its grid cell (leaves a gap)
const OVERFILL = 1.02; // grid overfills the camera frustum by this factor so no edge bands show
const HEADROOM = 1.4; // allocate this many times the target tile count so resize can reflow
// Time-based decay: exp(-dt / DECAY_TAU) instead of a frame-based x0.94, so a
// stationary tile fades at the same real-world rate at 60Hz and 120Hz (a
// frame-based multiplier applied twice as often at 120Hz would decay twice as
// fast in wall-clock time).
const DECAY_TAU = 0.28; // seconds; matches the previous ~0.94-per-frame-at-60fps feel
const POINTER_RADIUS = 0.22; // grid-space units the pointer glow reaches
const POINTER_GAIN = 2.5; // intensity gained per second at the pointer center (dt-scaled)
const CENTER_RADIUS = 0.35; // ambient "viewport center" glow radius
// Per-second gain at the exact center. Tuned by Node simulation (see
// context/06-progress.md) so the rest-state mean stays <=0.05 and at least
// 90% of tiles stay <=0.06 across desktop and mobile aspect ratios, while the
// center island still peaks under the 0.25 ceiling.
const CENTER_GAIN = 0.75;
// Breathing amplitude at coherence 0 (rest) and coherence 1 (fully
// synchronized), mixed by coherenceUniform. Rest is whisper-quiet and well
// under the 0.03 ceiling by construction (it IS the ceiling); the coherent
// peak is exactly the 0.08 ceiling.
const REST_AMPLITUDE = 0.03;
const COHERENT_AMPLITUDE = 0.08;
const TWO_PI = Math.PI * 2;
const OFFSCREEN = 1000; // pointer default: far enough to touch no tile
const SEED_RADIUS = 0.22; // matches the poster's sparse cluster, for a seamless mount

function readColor(varName: string, fallback: string): Color {
	if (typeof window === 'undefined') return new Color(fallback);
	const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
	return new Color(value || fallback);
}

// Cheap deterministic hash in [0, 1), matching the one used to generate
// public/hero-poster.svg, so the first live frame reads as a continuation of
// the poster instead of a flash-to-black.
function seededNoise(i: number): number {
	const s = Math.sin(i * 12.9898) * 43758.5453;
	return s - Math.floor(s);
}

// A second, independent hash keyed on (row, col) rather than instance index,
// used to give every tile its own breathing phase offset. Independent from
// seededNoise() above (different magic constants) so the poster's sparse
// cluster and the breathing phase never correlate into a visible pattern.
function hash2(row: number, col: number): number {
	const s = Math.sin(row * 12.9898 + col * 78.233) * 43758.5453;
	return s - Math.floor(s);
}

export interface HeroScene {
	scene: Scene;
	camera: OrthographicCamera;
	coherenceUniform: { value: number };
	uHandoff: { value: number };
	setHandoff(cells: HTMLElement[], canvasRect: DOMRect): void;
	setPointer(ndcX: number, ndcY: number): void;
	update(dt: number): void;
	resize(width: number, height: number): void;
	dispose(): void;
}

export function createHeroScene(tileCount: number, initialAspect: number): HeroScene {
	const scene = new Scene();
	scene.background = readColor('--color-bg', '#0b0d10');
	const camera = new OrthographicCamera(-initialAspect, initialAspect, 1, -1, 0.1, 10);
	camera.position.z = 5;

	const maxCount = Math.max(1, Math.ceil(tileCount * HEADROOM));
	const intensity = new Float32Array(maxCount);
	const region = new Float32Array(maxCount);
	const tileHash = new Float32Array(maxCount);
	const positions = new Float32Array(maxCount * 2);

	const dummy = new Object3D();
	// Unit tile: actual on-screen size comes from the per-instance scale set
	// in layout(), so a resize never needs to touch the geometry itself.
	const geometry = new PlaneGeometry(TILE_FILL, TILE_FILL);
	const material = new MeshBasicNodeMaterial();
	const mesh = new InstancedMesh(geometry, material, maxCount);
	mesh.frustumCulled = false; // visibility is managed via mesh.count, not bounds
	scene.add(mesh);

	const intensityAttribute = new InstancedBufferAttribute(intensity, 1);
	const regionAttribute = new InstancedBufferAttribute(region, 1);
	const tileHashAttribute = new InstancedBufferAttribute(tileHash, 1);

	let activeCount = 0;

	// Recomputes how many tiles fit the current aspect ratio (near-square,
	// picking rows/cols from the target count) and their pitch, so the grid
	// overfills the visible frustum by OVERFILL on both axes without ever
	// distorting a tile away from square.
	function layout(aspect: number): void {
		const frustumHeight = camera.top - camera.bottom; // fixed at 2
		const rows = Math.max(1, Math.round(Math.sqrt(tileCount / aspect)));
		const cols = Math.max(1, Math.round(rows * aspect));
		const count = Math.min(maxCount, cols * rows);
		const cellSize = (frustumHeight * OVERFILL) / rows;
		const gridWidth = cellSize * cols;
		const gridHeight = cellSize * rows;

		for (let i = 0; i < count; i += 1) {
			const col = i % cols;
			const row = Math.floor(i / cols);
			const x = (col + 0.5) * cellSize - gridWidth / 2;
			const y = (row + 0.5) * cellSize - gridHeight / 2;
			positions[i * 2] = x;
			positions[i * 2 + 1] = y;
			region[i] = Math.min(REGION_COUNT - 1, Math.floor((col / cols) * REGION_COUNT));
			tileHash[i] = hash2(row, col);

			const distFromCenter = Math.hypot(x, y);
			const noise = seededNoise(i);
			intensity[i] =
				distFromCenter < SEED_RADIUS && noise > 0.55 ? 0.5 + noise * 0.5 : 0;

			dummy.position.set(x, y, 0);
			dummy.scale.set(cellSize, cellSize, 1);
			dummy.updateMatrix();
			mesh.setMatrixAt(i, dummy.matrix);
		}

		mesh.count = count;
		activeCount = count;
		mesh.instanceMatrix.needsUpdate = true;
		regionAttribute.needsUpdate = true;
		tileHashAttribute.needsUpdate = true;
		intensityAttribute.needsUpdate = true;
	}

	layout(initialAspect);

	const unlitColor = uniform(readColor('--color-tile-unlit', '#1a1f25'));
	const observedColor = uniform(readColor('--color-tile-observed', '#3ddc84'));
	const coherenceUniform = uniform(0);
	const uHandoff = uniform(0);
	// Pixel origin and pitch bridge measured DOM layout to both render backends.
	const handoffLayout = uniform(new Vector4());
	const handoffMaterial = new MeshBasicNodeMaterial();
	handoffMaterial.transparent = true;
	handoffMaterial.opacityNode = uHandoff;
	const handoff = new InstancedMesh(geometry, handoffMaterial, 14);
	handoff.count = 0;
	handoff.frustumCulled = false;
	scene.add(handoff);
	material.transparent = true;
	material.opacityNode = float(1).sub(uHandoff);


	// Explicit type arguments: without them TS widens the 'float' literal to
	// `string`, which drops the .mul()/.add() node-arithmetic overloads.
	const intensityNode = instancedDynamicBufferAttribute<'float'>(intensityAttribute, 'float');
	const regionNode = instancedBufferAttribute<'float'>(regionAttribute, 'float');
	const tileHashNode = instancedBufferAttribute<'float'>(tileHashAttribute, 'float');

	// Each region has its own rate and a "converged" phase. At coherence 0
	// every tile instead uses its OWN phase, derived from a hash of its
	// (row, col) — never the region's shared phase — so a region never reads
	// as a solid breathing band at rest: neighboring tiles are out of step
	// with each other by construction. As coherence rises toward 1, each
	// tile's phase is blended toward its region's shared phase, so the
	// region's tiles visibly fall into step together only once coherence
	// gets there. Amplitude rises the same way: a whisper at rest, a real
	// (but still capped) pulse once synchronized.
	const regionRate = regionNode.mul(0.35).add(0.6);
	const regionPhase = regionNode.mul(2.399);
	const tilePhase = tileHashNode.mul(TWO_PI);
	const phase = mix(tilePhase, regionPhase, coherenceUniform);
	const amplitude = mix(float(REST_AMPLITUDE), float(COHERENT_AMPLITUDE), coherenceUniform);
	const breathing = sin(time.mul(regionRate).add(phase)).mul(amplitude).mul(float(1).sub(uHandoff));
	// No additive floor: at intensity 0 and breathing's trough (clamped at
	// 0), visibleIntensity is exactly 0 and colorNode resolves to
	// unlitColor untouched — nothing here adds a constant baseline.
	const visibleIntensity = clamp(intensityNode.add(breathing), 0, 1);
	material.colorNode = mix(unlitColor, observedColor, visibleIntensity);

	const pointerGrid = { x: OFFSCREEN, y: OFFSCREEN };

	return {
		scene,
		camera,
		coherenceUniform,
		uHandoff,
		setHandoff(cells, rect) {
			if (cells.length !== 14 || !rect.height) { handoff.count = 0; return; }
			const first = cells[0].getBoundingClientRect();
			const grid = cells[0].parentElement!;
			const gap = parseFloat(getComputedStyle(grid).gap) || 14;
			handoffLayout.value.set(first.left - rect.left, first.top - rect.top, first.width + gap, first.height + gap);
			const origin = handoffLayout.value;
			const all = [...grid.querySelectorAll<HTMLElement>('.cell')];
			cells.forEach((cell, i) => {
				const index = all.indexOf(cell);
				const x = origin.x + (index % 8) * origin.z + first.width / 2;
				const y = origin.y + Math.floor(index / 8) * origin.w + first.height / 2;
				dummy.position.set((x / rect.width * 2 - 1) * camera.right, 1 - y / rect.height * 2, 0.1);
				dummy.scale.set(first.width / rect.height * 2 / TILE_FILL, first.height / rect.height * 2 / TILE_FILL, 1);
				dummy.updateMatrix();
				handoff.setMatrixAt(i, dummy.matrix);
				const lit = getComputedStyle(cell).getPropertyValue('--tile-light').trim();
				const color = readColor('--color-tile-unlit', '#1a1f25').lerp(new Color(lit || '#3ddc84'), cell.dataset.decision === 'event' ? 0.18 : 0.34);
				handoff.setColorAt(i, color);
			});
			handoff.count = cells.length;
			handoff.instanceMatrix.needsUpdate = true;
			if (handoff.instanceColor) handoff.instanceColor.needsUpdate = true;
		},
		setPointer(ndcX, ndcY) {
			pointerGrid.x = ndcX * camera.right;
			pointerGrid.y = ndcY * camera.top;
		},
		update(dt) {
			// exp(-dt / tau): the same wall-clock fade regardless of how often
			// update() is called, unlike a flat per-frame multiplier.
			const decayFactor = Math.exp(-dt / DECAY_TAU);
			for (let i = 0; i < activeCount; i += 1) {
				let value = intensity[i] * decayFactor;

				const px = positions[i * 2];
				const py = positions[i * 2 + 1];

				const pointerDist = Math.hypot(px - pointerGrid.x, py - pointerGrid.y);
				if (pointerDist < POINTER_RADIUS) {
					value += (1 - pointerDist / POINTER_RADIUS) * POINTER_GAIN * dt;
				}

				const centerDist = Math.hypot(px, py);
				if (centerDist < CENTER_RADIUS) {
					value += (1 - centerDist / CENTER_RADIUS) * CENTER_GAIN * dt;
				}

				intensity[i] = value > 1 ? 1 : value < 0 ? 0 : value;
			}
			intensityAttribute.needsUpdate = true;
		},
		resize(width, height) {
			const aspect = width / height || 1;
			camera.left = -aspect;
			camera.right = aspect;
			camera.top = 1;
			camera.bottom = -1;
			camera.updateProjectionMatrix();
			layout(aspect);
		},
		dispose() {
			geometry.dispose();
			material.dispose();
			handoffMaterial.dispose();
		},
	};
}
