const section = document.querySelector<HTMLElement>('.eg-embed');
const root = section?.querySelector<HTMLElement>('.graph-wrap');
if (section && root) {
	let mounting: Promise<void> | undefined;
	const mount = () =>
		(mounting ??= import('../graph/evidence-graph').then((m) => {
			m.mountEvidenceGraph(root);
			section.dataset.mounted = 'true';
			section.dispatchEvent(new Event('eg-ready'));
		}));
	section.addEventListener('eg-mount', mount);
	const observer = new IntersectionObserver(
		(entries) => {
			if (entries.some((entry) => entry.isIntersecting)) {
				observer.disconnect();
				void mount();
			}
		},
		{ rootMargin: '100% 0px' },
	);
	observer.observe(section);
}

const btn = document.getElementById('copy-btn');
const cmd = document.getElementById('install-cmd');
const copyStatus = document.getElementById('copy-status');
btn?.addEventListener('click', async () => {
	const text = cmd?.textContent ?? '';
	try {
		await navigator.clipboard.writeText(text);
		const original = btn.textContent;
		btn.textContent = 'Copied';
		if (copyStatus) copyStatus.textContent = 'Install command copied to clipboard.';
		setTimeout(() => {
			btn.textContent = original;
		}, 1500);
	} catch {
		if (copyStatus) copyStatus.textContent = 'Clipboard unavailable. Select and copy the install command above.';
	}
});

// Load the hero scene only after the headline has painted and only once the
// canvas is actually visible. mountHero() decides whether to animate.
const canvas = document.getElementById('hero-canvas');
if (canvas instanceof HTMLCanvasElement) {
	const start = () => {
		const observer = new IntersectionObserver((entries) => {
			for (const entry of entries) {
				if (!entry.isIntersecting) continue;
				observer.disconnect();
				import('../hero/mount').then((module) => module.default(canvas));
			}
		});
		observer.observe(canvas);
	};

	if ('requestIdleCallback' in window) {
		requestIdleCallback(start);
	} else {
		setTimeout(start, 0);
	}
}
