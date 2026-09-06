// Capability gate for the hero scene. Anything that fails here means the
// static poster (public/hero-poster.svg) stays visible and no WebGPU/WebGL2
// work happens at all.

// Devices at or below this core count skip the scene to protect low-power
// hardware (e.g. budget phones reporting hardwareConcurrency <= 2).
const MIN_USEFUL_CORES = 2;

export interface AnimateDecision {
	ok: boolean;
	reason: string;
}

function hasWebGL2(): boolean {
	try {
		const canvas = document.createElement('canvas');
		return canvas.getContext('webgl2') !== null;
	} catch {
		return false;
	}
}

/**
 * Decide whether the three.js hero scene should mount. Never throws: any
 * detection failure is treated as "do not animate".
 */
export function shouldAnimate(): AnimateDecision {
	if (typeof window === 'undefined' || typeof navigator === 'undefined') {
		return { ok: false, reason: 'no-browser-environment' };
	}

	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
		return { ok: false, reason: 'prefers-reduced-motion' };
	}

	// `?hero=off` forces the poster path. The evidence-graph verifier uses it so a
	// software-GL render loop on CI runners cannot starve the checks it runs.
	if (new URLSearchParams(window.location.search).get('hero') === 'off') {
		return { ok: false, reason: 'query-hero-off' };
	}

	const cores = navigator.hardwareConcurrency ?? MIN_USEFUL_CORES + 1;
	if (cores <= MIN_USEFUL_CORES) {
		return { ok: false, reason: 'low-core-count' };
	}

	const hasWebGPU = 'gpu' in navigator;
	if (!hasWebGPU && !hasWebGL2()) {
		return { ok: false, reason: 'no-gpu-backend' };
	}

	return { ok: true, reason: 'ready' };
}
