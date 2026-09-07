// Lazy entry point for the hero scene. index.astro dynamically imports this
// module and calls mountHero() only after the headline has painted and the
// canvas is intersecting. Every listener added here is removed by the
// returned dispose().
import { WebGPURenderer } from 'three/webgpu';
import { createHeroScene } from './scene';
import { shouldAnimate } from './fallback';

const DPR_CAP = 1.5; // cap device pixel ratio to bound fill-rate cost
const MOBILE_QUERY = '(max-width: 768px)';
const DESKTOP_TILE_COUNT = 4000;
const MOBILE_TILE_COUNT = 1200;

const NOOP = () => {};

export default async function mountHero(canvas: HTMLCanvasElement): Promise<() => void> {
	if (!shouldAnimate().ok) return NOOP;

	const container = canvas.parentElement;
	if (!container) return NOOP;

	// Start the docking/motion module's fetch as early as mountHero() runs,
	// in parallel with the WebGPU/WebGL renderer's own init below (which can
	// be genuinely slow on a cold shader cache) — not serialized after it.
	// initMotion() itself still needs `hero`'s uniforms, which don't exist
	// until after renderer.init() resolves, so only the network fetch +
	// parse of the module is kicked off here; the actual initMotion() call
	// happens once hero exists (see `startMotion` below), reusing this same
	// in-flight import. Without this, a visitor who scroll-jumps straight
	// to the docking point right as the hero appears could still see a
	// noticeable delay before docking applies — not from motion.ts's own
	// logic (see its race-guard comment), but simply because the two async
	// chains (renderer init, then motion.ts fetch) ran one after the other
	// instead of overlapping.
	let motionModule: Promise<typeof import('./motion')> | undefined;
	const preloadMotion = () => (motionModule ??= import('./motion'));
	let motionTriggered = false;
	let onMotionTriggeredEarly: (() => void) | null = null;
	const triggerMotion = () => {
		if (motionTriggered) return;
		motionTriggered = true;
		cleanupMotionTriggers();
		void preloadMotion();
		onMotionTriggeredEarly?.();
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

	const renderer = new WebGPURenderer({ canvas, antialias: true });
	try {
		await renderer.init();
	} catch {
		renderer.dispose();
		cleanupMotionTriggers();
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

	// Docking (GSAP + ScrollTrigger + SplitText + Lenis, ~52 KiB gzip) is
	// not needed for the hero's first frame — only once the visitor starts
	// scrolling toward the embedded evidence graph. `preloadMotion`/
	// `triggerMotion` above already started the module fetch as early as
	// possible; here we only need to call `initMotion()` with the real
	// `hero` uniforms once both the module and `hero` exist.
	let stopMotion: (() => void) | null = null;
	let motionInit: Promise<void> | undefined;
	const startMotion = (): Promise<void> =>
		(motionInit ??= preloadMotion().then(({ initMotion }) => {
			stopMotion = initMotion({
				coherenceUniform: hero.coherenceUniform,
				uHandoff: hero.uHandoff,
				setHandoff: hero.setHandoff,
				canvasWrap: container,
				headline: document.querySelector<HTMLElement>('[data-hero-headline]'),
				navbar: document.querySelector<HTMLElement>('[data-hero-navbar]'),
			});
		}));
	if (motionTriggered) void startMotion();
	else onMotionTriggeredEarly = () => void startMotion();

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
		// runs once it exists, instead of a no-op no one awaits. `motionInit`
		// covers the normal case (initMotion() already scheduled); the
		// `motionModule` fallback covers triggerMotion() having fired (and
		// preloadMotion() having started) before `hero` existed, in the rare
		// case dispose() runs in that same narrow window.
		if (motionInit) void motionInit.then(() => stopMotion?.());
		else if (motionModule) void motionModule.then(() => stopMotion?.());
		else stopMotion?.();
		hero.dispose();
		renderer.dispose();
		if (poster) poster.hidden = false;
	};
}
