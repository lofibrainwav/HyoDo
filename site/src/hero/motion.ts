// Scroll choreography: Lenis smooth scroll drives GSAP ScrollTrigger, which
// drives the coherence uniform and the canvas clip-path shrink. The headline
// gets a one-time word stagger on load. The navbar hides on scroll down.
import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';

gsap.registerPlugin(ScrollTrigger, SplitText);

// Ignore scroll jitter under this many pixels before toggling the navbar.
const NAV_HIDE_THRESHOLD = 12;

export interface MotionOptions {
	coherenceUniform: { value: number };
	canvasWrap: HTMLElement;
	uHandoff: { value: number };
	setHandoff(cells: HTMLElement[], canvasRect: DOMRect): void;
	headline?: HTMLElement | null;
	navbar?: HTMLElement | null;
}

export function initMotion(options: MotionOptions): () => void {
	const { coherenceUniform, canvasWrap, headline, navbar } = options;
	const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	const lenis = new Lenis({ duration: reduceMotion ? 0 : 1.1, smoothWheel: !reduceMotion });
	const onTick = (rafTime: number) => lenis.raf(rafTime * 1000);
	gsap.ticker.add(onTick);
	gsap.ticker.lagSmoothing(0);
	lenis.on('scroll', ScrollTrigger.update);

	const embed = document.querySelector<HTMLElement>('.eg-embed');
	const graph = embed?.querySelector<HTMLElement>('.graph-wrap');
	const originalStyle = canvasWrap.getAttribute('style');
	const scrim = canvasWrap.querySelector<HTMLElement>('.hero-scrim');
	// Docking timing contract (kept in sync with site/context/05-ui-context.md):
	// the handoff tile pattern is fully lit by 45% of the scroll range, then the
	// crossfade (canvas 1->0, .eg-embed 0->1) runs from 45% to 75%, so the real
	// grid is fully visible well before the timeline ends. The timeline itself
	// ends no later than the point where the .eg-embed section's top reaches
	// 20% of the viewport height.
	const HANDOFF_END = 0.45;
	const FADE_END = 0.75;
	const applyDock = (progress: number) => {
		if (reduceMotion || !embed || !graph) return;
		if (progress > 0) embed.dispatchEvent(new Event('eg-mount'));
		const cells = [...graph.querySelectorAll<HTMLElement>('button.cell')];
		if (cells.length !== 14) return;
		const active = progress > 0 && progress < 1;
		canvasWrap.style.position = active ? 'fixed' : 'absolute';
		canvasWrap.style.zIndex = active ? '5' : '0';
		canvasWrap.style.pointerEvents = 'none';
		const rect = canvasWrap.getBoundingClientRect();
		const target = graph.getBoundingClientRect();
		options.setHandoff(cells, rect);
		options.uHandoff.value = Math.min(1, progress / HANDOFF_END);
		coherenceUniform.value = options.uHandoff.value;
		const fade = Math.min(1, Math.max(0, (progress - HANDOFF_END) / (FADE_END - HANDOFF_END)));
		canvasWrap.style.opacity = String(1 - fade);
		embed.style.opacity = String(fade);
		if (scrim) scrim.style.opacity = String(1 - options.uHandoff.value);
		const p = options.uHandoff.value;
		const left = (target.left - rect.left) * p;
		const top = (target.top - rect.top) * p;
		const right = rect.width + (target.right - rect.right) * p;
		const bottom = rect.height + (target.bottom - rect.bottom) * p;
		canvasWrap.style.clipPath = `polygon(${left}px ${top}px,${right}px ${top}px,${right}px ${bottom}px,${left}px ${bottom}px)`;
	};
	// End the timeline no later than the point where the .eg-embed section's
	// top reaches 20% of the viewport height. Measured from the section
	// itself (not the inner grid) so the boundary matches the contract above;
	// the function is re-evaluated by ScrollTrigger.refresh(), which GSAP
	// already calls on window resize.
	const scrollDriver = ScrollTrigger.create({
		trigger: document.body,
		start: 'top top',
		end: () => `+=${Math.max(1, (embed?.getBoundingClientRect().top ?? innerHeight) + scrollY - innerHeight * 0.2)}`,
		scrub: true,
		invalidateOnRefresh: true,
		onUpdate: self => applyDock(self.progress),
		onRefresh: self => applyDock(self.progress),
	});
	const onReady = () => { ScrollTrigger.refresh(); applyDock(scrollDriver.progress); };
	embed?.addEventListener('eg-ready', onReady);

	let splitInstance: SplitText | null = null;
	if (headline) {
		const stagger = reduceMotion ? 0 : 0.04;
		const duration = reduceMotion ? 0 : 0.6;
		const yOffset = reduceMotion ? 0 : 18;
		try {
			splitInstance = SplitText.create(headline, { type: 'words' });
			gsap.from(splitInstance.words, { opacity: 0, y: yOffset, duration, stagger, ease: 'power2.out' });
		} catch {
			// SplitText unavailable in this GSAP build: split on spaces by hand.
			const words = (headline.textContent ?? '').split(' ');
			headline.innerHTML = words.map((word) => `<span class="hero-word">${word}</span>`).join(' ');
			gsap.from(headline.querySelectorAll('.hero-word'), {
				opacity: 0,
				y: yOffset,
				duration,
				stagger,
				ease: 'power2.out',
			});
		}
	}

	let lastScroll = window.scrollY;
	const onScroll = () => {
		if (!navbar) return;
		const current = window.scrollY;
		if (Math.abs(current - lastScroll) < NAV_HIDE_THRESHOLD) return;
		const scrollingDown = current > lastScroll && current > NAV_HIDE_THRESHOLD;
		navbar.classList.toggle('nav-hidden', scrollingDown);
		lastScroll = current;
	};
	window.addEventListener('scroll', onScroll, { passive: true });

	return () => {
		window.removeEventListener('scroll', onScroll);
		gsap.ticker.remove(onTick);
		scrollDriver.kill();
		embed?.removeEventListener('eg-ready', onReady);
		if (embed) embed.style.removeProperty('opacity');
		if (originalStyle === null) canvasWrap.removeAttribute('style');
		else canvasWrap.setAttribute('style', originalStyle);
		if (scrim) scrim.style.removeProperty('opacity');
		options.uHandoff.value = 0;
		splitInstance?.revert();
		lenis.destroy();
	};
}
