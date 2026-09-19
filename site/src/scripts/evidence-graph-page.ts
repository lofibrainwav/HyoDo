import { EVENTS, mountEvidenceGraph } from '../graph/evidence-graph';
import { fromEvidenceGraphV1, inspectEvidenceGraphV1 } from '../graph/from-v1';
import {
	fromVerificationView,
	inspectVerificationView,
} from '../graph/from-verification-view';

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

	// A verification view is the canonical input: lanes, roles, and the
	// decision a viewer may show all arrive already decided. A raw evidence
	// graph still loads, but this page will not decide for it — see the
	// banner text below and the note in `from-v1.ts`.
	const viewInfo = inspectVerificationView(parsed);
	if (viewInfo.ok) {
		remount(fromVerificationView(parsed));
		const status = escapeHtml(viewInfo.status ?? 'unknown');
		const withheld = viewInfo.allowWithheld
			? ' An ALLOW recorded under this graph is withheld as <code>UNOBSERVED</code>.'
			: '';
		if (consoleSession) consoleSession.textContent = 'SESSION / LOCAL VERIFICATION VIEW';
		if (consoleView) consoleView.textContent = 'STATIC VIEW';
		if (consoleBoundary) consoleBoundary.textContent = 'LOCAL DATA / NOT SEALED';
		banner.innerHTML =
			`<strong>Local file.</strong> Showing a <code>hyodo.verification-view/v0</code> payload selected in this browser — not a remote ledger. Status: <code>${status}</code>.${withheld} Nothing was uploaded, stored, or fetched.`;
		banner.dataset.source = 'local';
		return;
	}

	const info = inspectEvidenceGraphV1(parsed);
	if (!info.ok) {
		showFixture();
		const why = info.reason ? ` (${escapeHtml(info.reason)})` : '';
		banner.innerHTML =
			`<strong>Load failed.</strong> Not a <code>hyodo.verification-view/v0</code> view or a <code>hyodo.evidence-graph/v1</code> graph${why}. Still showing the demo fixture. Nothing was uploaded, stored, or fetched from a network.`;
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
		`<strong>Local file.</strong> Showing a <code>hyodo.evidence-graph/v1</code> payload selected in this browser — not a remote ledger. Graph status: <code>${status}</code>${reason}.${unobserved} A raw graph carries no decided view, so every decision reads <code>UNOBSERVED</code> here; load <code>hyodo.verification-view/v0</code> from <code>/api/verification-view</code> to see decisions and roles. Nothing was uploaded, stored, or fetched. Live ledger: <code>hyodo dashboard</code> at <code>/graph</code>.`;
	banner.dataset.source = 'local';
});

resetBtn?.addEventListener('click', () => showFixture());
