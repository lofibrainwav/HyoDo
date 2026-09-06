// Lazy entry point for the hero scene. index.astro dynamically imports this
// module and calls mountHero() only after the headline has painted and the
// canvas is intersecting. Every listener added here is removed by the
// returned dispose().
import { WebGPURenderer } from 'three/webgpu';
import { createHeroScene } from './scene';
import { shouldAnimate } from './fallback';
import type { MotionOptions } from './motion';

const DPR_CAP = 1.5; // cap device pixel ratio to bound fill-rate cost
const MOBILE_QUERY = '(max-width: 768px)';
const DESKTOP_TILE_COUNT = 4000;
const MOBILE_TILE_COUNT = 1200;

const NOOP = () => {};

export default async function mountHero(canvas: HTMLCanvasElement): Promise<() => void> {
	if (!shouldAnimate().ok) return NOOP;

	const container = canvas.parentElement;
	if (!container) return NOOP;

	const renderer = new WebGPURenderer({ canvas, antialias: true });
	try {
		await renderer.init();
	} catch {
		renderer.dispose();
		return NOOP;
	}

	const isMobile = window.matchMedia(MOBILE_QUERY).matches;
	// Read the real container size up front so the grid is laid out for the
	// actual aspect ratio from its first frame, not a square guess that
	// resize() then has to correct.
	const initialRect = container.getBoundingClientRect();
	const initialAspect = initialRect.width / (initialRect.height || initialRect.width) || 1;
	const hero = createHeroScene(isMobile ? MOBILE_TILE_COUNT : DESKTOP_TILE_COUNT, initialAspect);

	const applySize = () => {
		const rect = container.getBoundingClientRect();
		if (rect.width === 0 || rect.height === 0) return;
		renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, DPR_CAP));
		renderer.setSize(rect.width, rect.height, false);
		hero.resize(rect.width, rect.height);
	};
	applySize();

	const onPointerMove = (event: PointerEvent) => {
		const rect = container.getBoundingClientRect();
		const ndcX = ((event.clientX - rect.left) / rect.width) * 2 - 1;
		const ndcY = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
		hero.setPointer(ndcX, ndcY);
	};
	window.addEventListener('pointermove', onPointerMove, { passive: true });

	const resizeObserver = new ResizeObserver(applySize);
	resizeObserver.observe(container);

	// Docking (GSAP + ScrollTrigger + SplitText + Lenis, ~280 KiB gzip) is
	// not needed for the hero's first frame — only once the visitor starts
	// scrolling toward the embedded evidence graph. Load it lazily so it
	// never rides along in the initial hero chunk: on the first scroll, or
	// as soon as `.eg-embed` is within one viewport of the screen
	// (rootMargin: '100% 0px', matching the trigger index.astro uses to
	// import the graph module itself), whichever fires first.
	const motionOptions: MotionOptions = {
		coherenceUniform: hero.coherenceUniform,
		uHandoff: hero.uHandoff,
		setHandoff: hero.setHandoff,
		canvasWrap: container,
		headline: document.querySelector<HTMLElement>('[data-hero-headline]'),
		navbar: document.querySelector<HTMLElement>('[data-hero-navbar]'),
	};
	let stopMotion: (() => void) | null = null;
	let motionLoading: Promise<void> | undefined;
	const startMotion = (): Promise<void> =>
		(motionLoading ??= import('./motion').then(({ initMotion }) => {
			stopMotion = initMotion(motionOptions);
		}));

	let motionTriggered = false;
	const triggerMotion = () => {
		if (motionTriggered) return;
		motionTriggered = true;
		cleanupMotionTriggers();
		void startMotion();
	};
	const onFirstScroll = () => triggerMotion();
	window.addEventListener('scroll', onFirstScroll, { passive: true });
	const embedEl = document.querySelector<HTMLElement>('.eg-embed');
	const motionObserver =
		embedEl && 'IntersectionObserver' in window
			? new IntersectionObserver(
					(entries) => {
						if (entries.some((entry) => entry.isIntersecting)) triggerMotion();
					},
					{ rootMargin: '100% 0px' },
				)
			: null;
	motionObserver?.observe(embedEl!);
	function cleanupMotionTriggers() {
		window.removeEventListener('scroll', onFirstScroll);
		motionObserver?.disconnect();
	}

	let lastFrame = performance.now();
	const animate = (now: number) => {
		const dt = Math.min((now - lastFrame) / 1000, 0.1);
		lastFrame = now;
		hero.update(dt);
		renderer.render(hero.scene, hero.camera);
	};

	const onVisibility = () => {
		if (document.visibilityState === 'visible') {
			lastFrame = performance.now();
			renderer.setAnimationLoop(animate);
		} else {
			renderer.setAnimationLoop(null);
		}
	};
	document.addEventListener('visibilitychange', onVisibility);

	renderer.setAnimationLoop(animate);
	// The poster sits above the canvas by default (see index.astro) so it
	// covers the scene until we know a frame has actually been rendered.
	const poster = container.querySelector<HTMLElement>('[data-hero-poster]');
	if (poster) poster.hidden = true;

	return () => {
		renderer.setAnimationLoop(null);
		window.removeEventListener('pointermove', onPointerMove);
		document.removeEventListener('visibilitychange', onVisibility);
		resizeObserver.disconnect();
		cleanupMotionTriggers();
		// Motion may still be mid-import (dynamic `import('./motion')` is
		// in flight) when this fires; wait for it so stopMotion() always
		// runs once it exists, instead of a no-op no one awaits.
		if (motionLoading) void motionLoading.then(() => stopMotion?.());
		else stopMotion?.();
		hero.dispose();
		renderer.dispose();
		if (poster) poster.hidden = false;
	};
}
