import { EVENTS, mountEvidenceGraph } from '../graph/evidence-graph';
import { fromEvidenceGraphV1, inspectEvidenceGraphV1 } from '../graph/from-v1';

const root = document.getElementById('eg-root');
const banner = document.getElementById('eg-banner');
const fileInput = document.getElementById('eg-file');
const resetBtn = document.getElementById('eg-reset');
const consoleSession = document.getElementById('eg-console-session');
const consoleView = document.getElementById('eg-console-view');
const consoleSteps = document.getElementById('eg-console-steps');
const consoleBoundary = document.getElementById('eg-console-boundary');
const fixtureBannerHtml = banner?.innerHTML ?? '';

let dispose = () => {};
if (root) dispose = mountEvidenceGraph(root);

function escapeHtml(value: string): string {
	return value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;');
}

function remount(events: typeof EVENTS): void {
	dispose();
	if (root) dispose = mountEvidenceGraph(root, events);
}

function showFixture(): void {
	remount(EVENTS);
	if (consoleSession) consoleSession.textContent = 'SESSION / FIXTURE';
	if (consoleView) consoleView.textContent = 'STATIC VIEW';
	if (consoleSteps) consoleSteps.textContent = 't0 — t7';
	if (consoleBoundary) consoleBoundary.textContent = 'DEMO DATA / NOT LIVE';
	if (banner) {
		banner.innerHTML = fixtureBannerHtml;
		banner.dataset.source = 'fixture';
	}
}

fileInput?.addEventListener('change', async () => {
	const input = fileInput as HTMLInputElement;
	const file = input.files?.[0];
	input.value = '';
	if (!file || !banner) return;

	let parsed: unknown;
	try {
		parsed = JSON.parse(await file.text());
	} catch {
		showFixture();
		banner.innerHTML =
			'<strong>Load failed.</strong> That file is not valid JSON. Still showing the demo fixture. Nothing was uploaded, stored, or fetched from a network.';
		banner.dataset.source = 'fixture';
		return;
	}

	const info = inspectEvidenceGraphV1(parsed);
	if (!info.ok) {
		showFixture();
		const why = info.reason ? ` (${escapeHtml(info.reason)})` : '';
		banner.innerHTML =
			`<strong>Load failed.</strong> Not a <code>hyodo.evidence-graph/v1</code> graph${why}. Still showing the demo fixture. Nothing was uploaded, stored, or fetched from a network.`;
		banner.dataset.source = 'fixture';
		return;
	}

	remount(fromEvidenceGraphV1(parsed));
	const graphNodes = Array.isArray((parsed as { nodes?: unknown }).nodes)
		? (parsed as { nodes: Array<{ step_index?: unknown }> }).nodes
		: [];
	const steps = graphNodes
		.map((node) => (typeof node.step_index === 'number' ? node.step_index : null))
		.filter((step): step is number => step !== null);
	const maxStep = steps.length > 0 ? Math.max(...steps) : 0;
	if (consoleSession) consoleSession.textContent = 'SESSION / LOCAL JSON';
	if (consoleView) consoleView.textContent = 'STATIC VIEW';
	if (consoleSteps) consoleSteps.textContent = `t0 — t${maxStep}`;
	if (consoleBoundary) consoleBoundary.textContent = 'LOCAL DATA / NOT SEALED';
	const status = escapeHtml(info.status ?? 'unknown');
	const reason = info.reason ? ` (${escapeHtml(info.reason)})` : '';
	const unobserved = info.status === 'UNOBSERVED' ? ' Unobserved is never a pass.' : '';
	banner.innerHTML =
		`<strong>Local file.</strong> Showing a <code>hyodo.evidence-graph/v1</code> payload selected in this browser — not a remote ledger. Graph status: <code>${status}</code>${reason}.${unobserved} Nothing was uploaded, stored, or fetched. Live ledger: <code>hyodo dashboard</code> at <code>/graph</code>.`;
	banner.dataset.source = 'local';
});

resetBtn?.addEventListener('click', () => showFixture());
