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
const DECAY = 0.94; // per-frame intensity falloff, applied once per rendered frame
const POINTER_RADIUS = 0.22; // grid-space units the pointer glow reaches
const POINTER_GAIN = 2.5; // intensity gained per second at the pointer center (dt-scaled)
const CENTER_RADIUS = 0.35; // ambient "viewport center" glow radius
const CENTER_GAIN = 0.9; // per-second gain at the exact center; settles near 0.25 at 60fps
const BREATH_AMPLITUDE = 0.06; // whisper-quiet: well under the 0.08 ceiling
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

export interface HeroScene {
	scene: Scene;
	camera: OrthographicCamera;
	coherenceUniform: { value: number };
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
		intensityAttribute.needsUpdate = true;
	}

	layout(initialAspect);

	const unlitColor = uniform(readColor('--color-tile-unlit', '#1a1f25'));
	const observedColor = uniform(readColor('--color-tile-observed', '#3ddc84'));
	const coherenceUniform = uniform(0);

	// Explicit type arguments: without them TS widens the 'float' literal to
	// `string`, which drops the .mul()/.add() node-arithmetic overloads.
	const intensityNode = instancedDynamicBufferAttribute<'float'>(intensityAttribute, 'float');
	const regionNode = instancedBufferAttribute<'float'>(regionAttribute, 'float');

	// Each region breathes at a slightly different rate and phase, drifting
	// apart when coherence is 0 and settling in sync as coherence rises. The
	// amplitude is deliberately tiny: this is a whisper, not a light show.
	const regionRate = regionNode.mul(0.35).add(0.6);
	const phase = regionNode.mul(2.399);
	const breathing = sin(time.mul(regionRate).add(phase))
		.mul(float(1).sub(coherenceUniform))
		.mul(BREATH_AMPLITUDE);
	const visibleIntensity = clamp(intensityNode.add(breathing), 0, 1);
	material.colorNode = mix(unlitColor, observedColor, visibleIntensity);

	const pointerGrid = { x: OFFSCREEN, y: OFFSCREEN };

	return {
		scene,
		camera,
		coherenceUniform,
		setPointer(ndcX, ndcY) {
			pointerGrid.x = ndcX * camera.right;
			pointerGrid.y = ndcY * camera.top;
		},
		update(dt) {
			for (let i = 0; i < activeCount; i += 1) {
				let value = intensity[i] * DECAY;

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
		},
	};
}
