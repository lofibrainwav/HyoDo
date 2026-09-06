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
// Clip-path shrink at full scroll progress, in percent inset from each edge.
const CLIP_INSET_MAX = 18;

export interface MotionOptions {
	coherenceUniform: { value: number };
	canvasWrap: HTMLElement;
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

	const scrollDriver = ScrollTrigger.create({
		trigger: document.body,
		start: 'top top',
		end: '+=100%',
		scrub: true,
		onUpdate(self) {
			coherenceUniform.value = self.progress;
			const inset = CLIP_INSET_MAX * self.progress;
			const top = inset * 0.5;
			canvasWrap.style.clipPath =
				`polygon(${inset}% ${top}%, ${100 - inset}% ${top}%, ` +
				`${100 - inset}% ${100 - top}%, ${inset}% ${100 - top}%)`;
		},
	});

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
		splitInstance?.revert();
		lenis.destroy();
	};
}
