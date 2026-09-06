// HyoDo Evidence Graph prototype — fixture data + renderer.
//
// This module renders a fixed, in-memory demo fixture (no network, no
// storage) as a rows-by-steps grid of events connected by two kinds of
// edges: `parentEventId` ("result of") and `evidenceRefs` ("decided
// from"). See site/src/content/docs/docs/evidence-graph.md for the field
// mapping and which fields are real in the shipped schema today.
//
// Edge geometry (rounded elbow for parent, single-bow bezier for
// evidence, dash-vs-shape rather than color, hand-drawn broken stub) is
// informed by the MIT-licensed diagram-technique collection at
// fiv.co.kr/diagram; no markup from that collection is reproduced here.
//
// All `document`/`window` access lives inside mountEvidenceGraph() — this
// module has no top-level DOM access, so it is safe to import during SSR.

export type Decision = 'ALLOW' | 'ASK' | 'DENY' | 'UNOBSERVED';

/** Mirrors the shipped hyodo.agent-event/v1 `kind` enum (hyodo/events.py EVENT_KINDS). */
export type SchemaEventKind =
	| 'prompt'
	| 'tool_call'
	| 'tool_result'
	| 'model_response'
	| 'error'
	| 'decision';

/** Page-only chip taxonomy, NOT a schema field; derived from schemaKind + tool.name + policy.decision. */
export type DisplayKind =
	| 'mission'
	| 'read_file'
	| 'write_file'
	| 'run_tests'
	| 'scan'
	| 'approve'
	| 'decision'
	| 'unobserved';

export type Row = 'human' | 'planner' | 'executor' | 'reviewer';

export interface EvidenceEvent {
	eventId: string;
	runId: string;
	ts: string;
	schemaKind: SchemaEventKind;
	displayKind: DisplayKind;
	/** Illustrative label ("agent:planner"); the shipped schema's actor is coarse (agent|human|hyodo). */
	actor: string;
	row: Row;
	stepIndex: number;
	tool: { name: string; paths: string[]; urls: string[] } | null;
	policy: { decision: Decision; ruleId: string | null; reason: string | null } | null;
	/** PROPOSED field — not in the shipped hyodo.agent-event/v1 schema yet. */
	parentEventId: string | null;
	/** PROPOSED field — not in the shipped hyodo.agent-event/v1 schema yet. */
	evidenceRefs: string[];
	/** Prototype-only narrative used for the "why" field when policy.reason is absent. */
	note: string;
}

const RUN_ID = 'run-2026-09-06-001';

export const EVENTS: readonly EvidenceEvent[] = [
	{
		eventId: 'evt-h0',
		runId: RUN_ID,
		ts: '2026-09-06T09:00:00Z',
		schemaKind: 'prompt',
		displayKind: 'mission',
		actor: 'human:operator',
		row: 'human',
		stepIndex: 0,
		tool: null,
		policy: null,
		parentEventId: null,
		evidenceRefs: [],
		note: 'Incident: repeated HTTP 500s from unbounded login attempts. Mission: ship a rate-limit fix today.',
	},
	{
		eventId: 'evt-p1',
		runId: RUN_ID,
		ts: '2026-09-06T09:01:00Z',
		schemaKind: 'tool_call',
		displayKind: 'read_file',
		actor: 'agent:planner',
		row: 'planner',
		stepIndex: 1,
		tool: { name: 'read_file', paths: ['src/auth/rate_limit.py'], urls: [] },
		policy: null,
		parentEventId: 'evt-h0',
		evidenceRefs: [],
		note: 'Inspect the current rate-limit implementation before proposing a fix.',
	},
	{
		eventId: 'evt-p2',
		runId: RUN_ID,
		ts: '2026-09-06T09:02:00Z',
		schemaKind: 'tool_result',
		displayKind: 'read_file',
		actor: 'agent:planner',
		row: 'planner',
		stepIndex: 2,
		tool: { name: 'read_file', paths: ['src/auth/rate_limit.py'], urls: [] },
		policy: null,
		parentEventId: 'evt-p1',
		evidenceRefs: [],
		note: 'Result of the read_file call at step 1 — needed before drafting a patch.',
	},
	{
		eventId: 'evt-p3',
		runId: RUN_ID,
		ts: '2026-09-06T09:03:00Z',
		schemaKind: 'decision',
		displayKind: 'decision',
		actor: 'agent:planner',
		row: 'planner',
		stepIndex: 3,
		tool: { name: 'read_file', paths: ['src/auth/rate_limit.py'], urls: [] },
		policy: {
			decision: 'ALLOW',
			ruleId: 'path_inside_root',
			reason:
				'Path is inside the workspace root; read-only access does not require confirmation.',
		},
		parentEventId: 'evt-p2',
		evidenceRefs: [],
		note: 'Read access to the workspace tree is trusted by default.',
	},
	{
		eventId: 'evt-e1',
		runId: RUN_ID,
		ts: '2026-09-06T09:02:10Z',
		schemaKind: 'tool_call',
		displayKind: 'write_file',
		actor: 'agent:executor',
		row: 'executor',
		stepIndex: 2,
		tool: { name: 'write_file', paths: ['/home/runner/.ssh/config'], urls: [] },
		policy: null,
		parentEventId: 'evt-h0',
		evidenceRefs: [],
		note: 'Attempted to add a deploy-time SSH config entry needed for the hotfix rollout.',
	},
	{
		eventId: 'evt-e2',
		runId: RUN_ID,
		ts: '2026-09-06T09:03:10Z',
		schemaKind: 'decision',
		displayKind: 'decision',
		actor: 'agent:executor',
		row: 'executor',
		stepIndex: 3,
		tool: { name: 'write_file', paths: ['/home/runner/.ssh/config'], urls: [] },
		policy: {
			decision: 'ASK',
			ruleId: 'path_outside_root',
			reason:
				'Target path resolves outside the workspace root; writes outside the workspace require human confirmation. Citing evt-p3 (an ALLOW read on this file tree) as evidence that read access here was already trusted — write access still needs a human.',
		},
		parentEventId: 'evt-e1',
		evidenceRefs: ['evt-p3'],
		note: 'Write access outside the workspace root always pauses for a human.',
	},
	{
		eventId: 'evt-h1',
		runId: RUN_ID,
		ts: '2026-09-06T09:04:00Z',
		schemaKind: 'prompt',
		displayKind: 'approve',
		actor: 'human:operator',
		row: 'human',
		stepIndex: 4,
		tool: null,
		policy: null,
		parentEventId: 'evt-e2',
		evidenceRefs: [],
		note: 'Approved for this run only, in reply to the ASK gate raised at step 3.',
	},
	{
		eventId: 'evt-e3',
		runId: RUN_ID,
		ts: '2026-09-06T09:05:00Z',
		schemaKind: 'tool_result',
		displayKind: 'write_file',
		actor: 'agent:executor',
		row: 'executor',
		stepIndex: 5,
		tool: { name: 'write_file', paths: ['/home/runner/.ssh/config'], urls: [] },
		policy: null,
		parentEventId: 'evt-h1',
		evidenceRefs: [],
		note: 'Executes the write_file call that the step 3 ASK gate had paused, now approved at step 4.',
	},
	{
		eventId: 'evt-e4',
		runId: RUN_ID,
		ts: '2026-09-06T09:06:00Z',
		schemaKind: 'tool_call',
		displayKind: 'run_tests',
		actor: 'agent:executor',
		row: 'executor',
		stepIndex: 6,
		tool: { name: 'run_tests', paths: ['tests/test_rate_limit.py'], urls: [] },
		policy: null,
		parentEventId: 'evt-e3',
		evidenceRefs: [],
		note: 'Verify the fix does not regress existing rate-limit behavior before merge.',
	},
	{
		eventId: 'evt-e5',
		runId: RUN_ID,
		ts: '2026-09-06T09:07:00Z',
		schemaKind: 'tool_result',
		displayKind: 'run_tests',
		actor: 'agent:executor',
		row: 'executor',
		stepIndex: 7,
		tool: { name: 'run_tests', paths: ['tests/test_rate_limit.py'], urls: [] },
		policy: null,
		parentEventId: 'evt-e4',
		evidenceRefs: [],
		note: 'Result of the run_tests call at step 6 — tests passed; safe to proceed toward merge.',
	},
	{
		eventId: 'evt-r1',
		runId: RUN_ID,
		ts: '2026-09-06T09:04:10Z',
		schemaKind: 'tool_call',
		displayKind: 'scan',
		actor: 'agent:reviewer',
		row: 'reviewer',
		stepIndex: 4,
		tool: { name: 'run_scan', paths: ['config/secrets.yaml'], urls: [] },
		policy: null,
		parentEventId: 'evt-h0',
		evidenceRefs: [],
		note: 'Routine pre-merge secret scan of changed configuration files.',
	},
	{
		eventId: 'evt-r2',
		runId: RUN_ID,
		ts: '2026-09-06T09:05:10Z',
		schemaKind: 'decision',
		displayKind: 'decision',
		actor: 'agent:reviewer',
		row: 'reviewer',
		stepIndex: 5,
		tool: { name: 'run_scan', paths: ['config/secrets.yaml'], urls: [] },
		policy: {
			decision: 'DENY',
			ruleId: 'secret_scan',
			reason:
				'Hardcoded credential pattern detected in config/secrets.yaml; merge blocked until the secret is removed and rotated. Citing evt-p2 (an earlier clean read result) as evidence the secret was introduced after that read.',
		},
		parentEventId: 'evt-r1',
		evidenceRefs: ['evt-p2'],
		note: 'A detected secret blocks merge until it is removed and rotated.',
	},
	{
		eventId: 'evt-r3',
		runId: RUN_ID,
		ts: '2026-09-06T09:06:10Z',
		schemaKind: 'tool_call',
		displayKind: 'scan',
		actor: 'agent:reviewer',
		row: 'reviewer',
		stepIndex: 6,
		tool: { name: 'notify', paths: [], urls: ['https://example.com/oncall-hook'] },
		policy: null,
		// Deliberately broken: this id does not resolve to any event in the
		// fixture, so the renderer draws it as a broken edge instead of
		// silently dropping or resolving it.
		parentEventId: 'evt-r2-unresolved',
		evidenceRefs: [],
		note: 'Attempting to escalate the blocked secret to the on-call channel. The recorded parent event does not resolve to any event in this run — the causal link back to the DENY at step 5 was lost when the process restarted before that event finished committing to the log. Rendered as a broken edge.',
	},
	{
		eventId: 'evt-r4',
		runId: RUN_ID,
		ts: '2026-09-06T09:07:10Z',
		schemaKind: 'decision',
		displayKind: 'unobserved',
		actor: 'agent:reviewer',
		row: 'reviewer',
		stepIndex: 7,
		tool: null,
		policy: { decision: 'UNOBSERVED', ruleId: null, reason: null },
		parentEventId: 'evt-r3',
		evidenceRefs: [],
		note: 'No policy engine record exists for this step — the process was killed before a decision was logged. Treat as neither approved nor denied; flagged for manual audit.',
	},
];

const ROW_ORDER: readonly Row[] = ['human', 'planner', 'executor', 'reviewer'];
const ROW_LABEL: Record<Row, string> = {
	human: 'Human',
	planner: 'Planner',
	executor: 'Executor',
	reviewer: 'Reviewer',
};
const ROW_SUB: Record<Row, string> = {
	human: 'operator',
	planner: 'agent',
	executor: 'agent',
	reviewer: 'agent',
};

const DECISION_GLYPH: Record<Decision, string> = {
	ALLOW: '✓', // ✓
	ASK: '?',
	DENY: '✕', // ✕
	UNOBSERVED: '—', // —
};

const HOW_BY_SCHEMA_KIND: Record<SchemaEventKind, string> = {
	prompt: 'Typed by the human operator.',
	tool_call: 'Agent invoked a tool via the HyoDo tool runner.',
	tool_result: 'Tool runner returned this result to the agent.',
	model_response: 'Model produced this response.',
	error: 'A tool or the runtime raised an error.',
	decision: 'HyoDo policy engine evaluated the gate for this event.',
};

const COLUMN_WIDTH = 104;

function byId(id: string): EvidenceEvent | undefined {
	return EVENTS.find((e) => e.eventId === id);
}

function chipGlyph(ev: EvidenceEvent): string {
	if (ev.schemaKind === 'decision' && ev.policy) return DECISION_GLYPH[ev.policy.decision];
	if (ev.schemaKind === 'tool_call') return 'C';
	if (ev.schemaKind === 'tool_result') return 'R';
	if (ev.schemaKind === 'prompt') return 'P';
	if (ev.schemaKind === 'error') return '!';
	return '?';
}

function shortLabel(ev: EvidenceEvent): string {
	if (ev.schemaKind === 'decision' && ev.policy) return ev.policy.ruleId ?? 'unobserved';
	if (ev.tool) return ev.tool.name;
	if (ev.displayKind === 'mission') return 'mission';
	if (ev.displayKind === 'approve') return 'approve';
	return ev.displayKind;
}

function describeEvent(ev: EvidenceEvent): string {
	const decisionSuffix =
		ev.schemaKind === 'decision' && ev.policy ? ` — ${ev.policy.decision}` : '';
	return `${ev.displayKind}${decisionSuffix} by ${ev.actor} at step ${ev.stepIndex}`;
}

function fieldWhat(ev: EvidenceEvent): string {
	const toolPart = ev.tool ? ` — ${ev.tool.name}` : '';
	if (ev.schemaKind === 'decision' && ev.policy) {
		const rule = ev.policy.ruleId ? ` (${ev.policy.ruleId})` : '';
		return `${ev.displayKind} / ${ev.schemaKind}: ${ev.policy.decision}${rule}${toolPart}`;
	}
	return `${ev.displayKind} / ${ev.schemaKind}${toolPart}`;
}

function fieldWhere(ev: EvidenceEvent): string {
	if (ev.tool?.paths.length) return ev.tool.paths.join(', ');
	if (ev.tool?.urls.length) return ev.tool.urls.join(', ');
	return '—';
}

function fieldWhy(ev: EvidenceEvent): string {
	if (ev.policy?.reason) return ev.policy.reason;
	return ev.note || '—';
}

function fieldHow(ev: EvidenceEvent): string {
	let base = HOW_BY_SCHEMA_KIND[ev.schemaKind] ?? '';
	if (ev.schemaKind === 'decision' && ev.policy?.ruleId) {
		base += ` Rule: ${ev.policy.ruleId}.`;
	}
	return base;
}

function escapeHtml(value: string): string {
	return value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;');
}

const PANEL_PLACEHOLDER =
	'<h2>5W1H</h2><p class="placeholder">Hover or focus (Tab) a cell to inspect its record — who, when, what, where, how, why.</p>';

function renderPanelHtml(ev: EvidenceEvent): string {
	const row5 = (label: string, html: string) =>
		`<div class="row"><b>${escapeHtml(label)}</b><span>${html}</span></div>`;

	const parent = ev.parentEventId
		? byId(ev.parentEventId)
			? escapeHtml(ev.parentEventId)
			: `<span class="broken-ref">unresolved: ${escapeHtml(ev.parentEventId)}</span>`
		: '— (run root)';
	const evidence = ev.evidenceRefs.length ? ev.evidenceRefs.map(escapeHtml).join(', ') : 'none';

	return (
		`<h2>5W1H — ${escapeHtml(ev.eventId)}</h2>` +
		row5('Who', `${escapeHtml(ev.actor)} (${escapeHtml(ROW_LABEL[ev.row])})`) +
		row5('When', `${escapeHtml(ev.ts)} · step ${ev.stepIndex}`) +
		row5('What', escapeHtml(fieldWhat(ev))) +
		row5('Where', escapeHtml(fieldWhere(ev))) +
		row5('How', escapeHtml(fieldHow(ev))) +
		row5('Why', escapeHtml(fieldWhy(ev))) +
		`<div class="row links"><b>Links</b><span>Parent: ${parent} · Evidence: ${evidence}</span></div>`
	);
}

interface Point {
	x: number;
	y: number;
}

interface ParentEdgeRecord {
	sourceId: string;
	targetId: string;
	el: SVGPathElement;
	broken: boolean;
}

interface EvidenceEdgeRecord {
	sourceId: string;
	targetId: string;
	el: SVGPathElement;
	d: string;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl<K extends keyof SVGElementTagNameMap>(
	doc: Document,
	tag: K,
	attrs: Record<string, string | number> = {},
): SVGElementTagNameMap[K] {
	const e = doc.createElementNS(SVG_NS, tag);
	for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
	return e;
}

function elbowPath(x1: number, y1: number, x2: number, y2: number, r = 10): string {
	if (Math.abs(y1 - y2) < 1) return `M ${x1} ${y1} L ${x2} ${y2}`;
	const mx = (x1 + x2) / 2;
	const dy = y2 > y1 ? 1 : -1;
	return [
		'M', x1, y1,
		'H', mx - r,
		'Q', mx, y1, mx, y1 + r * dy,
		'V', y2 - r * dy,
		'Q', mx, y2, mx + r, y2,
		'H', x2,
	].join(' ');
}

function curvePath(x1: number, y1: number, x2: number, y2: number, bowExtra: number): string {
	const dx = x2 - x1;
	const dy = y2 - y1;
	const len = Math.max(1, Math.hypot(dx, dy));
	const px = -dy / len;
	const py = dx / len; // perpendicular unit normal, single consistent side
	const bow = len * 0.26 + bowExtra;
	const mx = (x1 + x2) / 2 + px * bow;
	const my = (y1 + y2) / 2 + py * bow;
	return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

/** Deterministic small hand-drawn jitter for the broken-link stub. */
function brokenStubPath(x: number, y: number): string {
	const pts: Array<[number, number]> = [
		[0, 0],
		[-9, -4],
		[-16, 2],
		[-24, -3],
	];
	let d = `M ${x + pts[0][0]} ${y + pts[0][1]}`;
	for (let i = 1; i < pts.length; i++) d += ` L ${x + pts[i][0]} ${y + pts[i][1]}`;
	return d;
}

export function mountEvidenceGraph(root: HTMLElement): () => void {
	const doc = root.ownerDocument;
	const win = doc.defaultView;
	if (!win) return () => {};

	const gridRootOrNull = root.querySelector<HTMLDivElement>('.grid');
	const svgRootOrNull = root.querySelector<SVGSVGElement>('svg.edges');
	const panel = doc.getElementById('eg-panel');
	if (!gridRootOrNull || !svgRootOrNull) return () => {};
	const gridRoot: HTMLDivElement = gridRootOrNull;
	const svgRoot: SVGSVGElement = svgRootOrNull;

	const maxStep = EVENTS.reduce((m, e) => Math.max(m, e.stepIndex), 0);
	const cols = maxStep + 1;

	const atCell = new Map<string, EvidenceEvent>();
	for (const ev of EVENTS) atCell.set(`${ev.row}:${ev.stepIndex}`, ev);

	// ---- build grid DOM -----------------------------------------------
	gridRoot.innerHTML = '';
	gridRoot.style.gridTemplateColumns = `120px repeat(${cols}, ${COLUMN_WIDTH}px)`;

	function el(tag: string, cls?: string): HTMLElement {
		const e = doc.createElement(tag);
		if (cls) e.className = cls;
		return e;
	}

	gridRoot.appendChild(el('div', 'corner'));
	for (let c = 0; c < cols; c++) {
		const head = el('div', 'colhead');
		head.textContent = `t${c}`;
		gridRoot.appendChild(head);
	}

	const cellEls = new Map<string, HTMLButtonElement>();
	const cleanupFns: Array<() => void> = [];

	for (const row of ROW_ORDER) {
		const rh = el('div', 'rowhead');
		rh.innerHTML = `${ROW_LABEL[row]}<small>${ROW_SUB[row]}</small>`;
		gridRoot.appendChild(rh);

		for (let c = 0; c < cols; c++) {
			const ev = atCell.get(`${row}:${c}`);
			if (!ev) {
				gridRoot.appendChild(el('div', 'cell unlit'));
				continue;
			}

			const btn = doc.createElement('button');
			btn.type = 'button';
			btn.className = 'cell node';
			btn.dataset.eventId = ev.eventId;
			btn.setAttribute('aria-label', describeEvent(ev));

			const chip = el('span', `chip ${ev.schemaKind}`);
			if (ev.schemaKind === 'decision' && ev.policy) {
				chip.classList.add('decision', ev.policy.decision);
			}
			chip.textContent = chipGlyph(ev);
			btn.appendChild(chip);

			const label = el('span', 'node-label');
			label.textContent = shortLabel(ev);
			btn.appendChild(label);

			const onEnter = () => activate(ev.eventId);
			const onLeave = () => deactivate();
			btn.addEventListener('mouseenter', onEnter);
			btn.addEventListener('focus', onEnter);
			btn.addEventListener('mouseleave', onLeave);
			btn.addEventListener('blur', onLeave);
			cleanupFns.push(() => {
				btn.removeEventListener('mouseenter', onEnter);
				btn.removeEventListener('focus', onEnter);
				btn.removeEventListener('mouseleave', onLeave);
				btn.removeEventListener('blur', onLeave);
			});

			gridRoot.appendChild(btn);
			cellEls.set(ev.eventId, btn);
		}
	}

	// ---- edges ----------------------------------------------------------
	let parentEdges: ParentEdgeRecord[] = [];
	let evidenceEdges: EvidenceEdgeRecord[] = [];
	let activeId: string | null = null;
	const activeTokens: SVGGElement[] = [];

	function cellRect(id: string): DOMRect | null {
		const btn = cellEls.get(id);
		if (!btn) return null;
		return btn.getBoundingClientRect();
	}

	/**
	 * Port on one edge of a cell's box. left/right are vertically centered
	 * (used for edges that flow between columns); top/bottom are
	 * horizontally centered (used when source and target share a column, so
	 * the edge travels through the row gap instead of across cell text).
	 */
	function port(rect: DOMRect, side: 'left' | 'right' | 'top' | 'bottom', wrapRect: DOMRect): Point {
		if (side === 'top' || side === 'bottom') {
			const y = side === 'bottom' ? rect.bottom : rect.top;
			return { x: rect.left - wrapRect.left + rect.width / 2, y: y - wrapRect.top };
		}
		const x = side === 'right' ? rect.right : rect.left;
		return { x: x - wrapRect.left, y: rect.top - wrapRect.top + rect.height / 2 };
	}

	function rowIndex(id: string): number {
		const ev = byId(id);
		return ev ? ROW_ORDER.indexOf(ev.row) : -1;
	}

	function drawEdges(): void {
		svgRoot.innerHTML = '';
		parentEdges = [];
		evidenceEdges = [];

		const wrapRect = root.getBoundingClientRect();
		svgRoot.setAttribute('viewBox', `0 0 ${wrapRect.width} ${wrapRect.height}`);

		const defs = svgEl(doc, 'defs');
		defs.innerHTML =
			'<marker id="arrow-parent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--edge-parent)"/></marker>' +
			'<marker id="arrow-evidence" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--edge-evidence)"/></marker>';
		svgRoot.appendChild(defs);

		const gParent = svgEl(doc, 'g', { class: 'layer-parent' });
		const gEvidence = svgEl(doc, 'g', { class: 'layer-evidence' });
		const gBroken = svgEl(doc, 'g', { class: 'layer-broken' });
		svgRoot.appendChild(gParent);
		svgRoot.appendChild(gEvidence);
		svgRoot.appendChild(gBroken);

		// Cells that receive a resolved parent arrow — used below so a
		// co-located evidence arrow can be inset instead of overlapping it.
		const parentTargets = new Set<string>();

		for (const ev of EVENTS) {
			const childRect = cellRect(ev.eventId);
			if (!childRect || !ev.parentEventId) continue;
			const parentEv = byId(ev.parentEventId);
			if (parentEv) {
				const parentRect = cellRect(parentEv.eventId);
				if (parentRect) {
					const forward = parentEv.stepIndex <= ev.stepIndex;
					const p1 = port(parentRect, forward ? 'right' : 'left', wrapRect);
					const p2 = port(childRect, forward ? 'left' : 'right', wrapRect);
					const path = svgEl(doc, 'path', {
						class: 'edge-parent',
						d: elbowPath(p1.x, p1.y, p2.x, p2.y),
						'marker-end': 'url(#arrow-parent)',
					});
					gParent.appendChild(path);
					parentEdges.push({ sourceId: parentEv.eventId, targetId: ev.eventId, el: path, broken: false });
					parentTargets.add(ev.eventId);
					continue;
				}
			}
			// Unresolved parentEventId -> broken link stub, hand-drawn red,
			// stopping short of the child's left port instead of pretending
			// to arrive at a real source.
			const target = port(childRect, 'left', wrapRect);
			const stub = svgEl(doc, 'path', {
				class: 'edge-broken',
				d: brokenStubPath(target.x - 6, target.y),
			});
			gBroken.appendChild(stub);
			const mark = svgEl(doc, 'text', {
				class: 'break-mark-text',
				x: target.x - 32,
				y: target.y - 6,
			});
			mark.textContent = '?';
			gBroken.appendChild(mark);
			parentEdges.push({ sourceId: ev.parentEventId, targetId: ev.eventId, el: stub, broken: true });
		}

		// Bucket evidence edges by (columnDelta, rowDelta) so overlapping
		// bows fan out instead of stacking exactly on top of each other.
		// NOTE: with only two evidence edges in this fixture the buckets
		// rarely collide; larger runs would want dedicated skip lanes per
		// row pair instead of ad hoc bow widening — documented follow-up,
		// not implemented here.
		const bucketCounts = new Map<string, number>();

		for (const ev of EVENTS) {
			const childRect = cellRect(ev.eventId);
			if (!childRect) continue;
			for (const refId of ev.evidenceRefs) {
				const refEv = byId(refId);
				const sourceRect = refEv ? cellRect(refEv.eventId) : null;
				if (!refEv || !sourceRect) continue;

				const colDelta = ev.stepIndex - refEv.stepIndex;
				const rowDelta = rowIndex(ev.eventId) - rowIndex(refEv.eventId);
				const bucketKey = `${colDelta}:${rowDelta}`;
				const bucketIndex = bucketCounts.get(bucketKey) ?? 0;
				bucketCounts.set(bucketKey, bucketIndex + 1);
				const bowExtra = bucketIndex * 10;

				let p1: Point;
				let p2: Point;

				if (colDelta === 0) {
					// Source and target share a column: route through the row
					// gap (top/bottom ports) instead of left/right, so the
					// curve arcs beside the cells' labels instead of over them.
					const forward = rowDelta >= 0;
					p1 = port(sourceRect, forward ? 'bottom' : 'top', wrapRect);
					p2 = port(childRect, forward ? 'top' : 'bottom', wrapRect);
				} else {
					const forward = refEv.stepIndex <= ev.stepIndex;
					p1 = port(sourceRect, forward ? 'right' : 'left', wrapRect);
					p2 = port(childRect, forward ? 'left' : 'right', wrapRect);

					// A parent arrow and an evidence arrow landing on the same
					// cell would overlap at the port; inset the evidence anchor.
					if (parentTargets.has(ev.eventId)) {
						p2 = { x: p2.x, y: p2.y + 6 };
					}
				}

				const d = curvePath(p1.x, p1.y, p2.x, p2.y, bowExtra);
				const path = svgEl(doc, 'path', {
					class: 'edge-evidence',
					d,
					'marker-end': 'url(#arrow-evidence)',
				});
				gEvidence.appendChild(path);
				evidenceEdges.push({ sourceId: refEv.eventId, targetId: ev.eventId, el: path, d });
			}
		}
	}

	// ---- interaction ------------------------------------------------------

	function clearActive(): void {
		if (activeId) cellEls.get(activeId)?.classList.remove('is-active');
		gridRoot.classList.remove('is-focused');
		svgRoot.classList.remove('is-focused');
		for (const rec of parentEdges) rec.el.classList.remove('active');
		for (const rec of evidenceEdges) rec.el.classList.remove('active');
		for (const token of activeTokens) token.remove();
		activeTokens.length = 0;
	}

	function reducedMotion(): boolean {
		return win?.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
	}

	function activate(eventId: string): void {
		clearActive();
		activeId = eventId;
		const ev = byId(eventId);
		if (!ev) return;

		cellEls.get(eventId)?.classList.add('is-active');
		gridRoot.classList.add('is-focused');
		svgRoot.classList.add('is-focused');

		for (const rec of parentEdges) {
			if (rec.sourceId === eventId || rec.targetId === eventId) rec.el.classList.add('active');
		}
		for (const rec of evidenceEdges) {
			if (rec.sourceId === eventId || rec.targetId === eventId) rec.el.classList.add('active');
		}

		if (!reducedMotion()) {
			const feeding = evidenceEdges.filter((rec) => rec.targetId === eventId);
			for (const rec of feeding) {
				const g = svgEl(doc, 'g');
				const dot = svgEl(doc, 'circle', { r: 4, class: 'token-dot' });
				const motion = doc.createElementNS(SVG_NS, 'animateMotion');
				motion.setAttribute('dur', '1.3s');
				motion.setAttribute('repeatCount', 'indefinite');
				motion.setAttribute('path', rec.d);
				dot.appendChild(motion);
				g.appendChild(dot);

				const label = svgEl(doc, 'text', { class: 'token', x: 0, y: -8, 'text-anchor': 'middle' });
				label.textContent = rec.sourceId.replace('evt-', '');
				const motion2 = doc.createElementNS(SVG_NS, 'animateMotion');
				motion2.setAttribute('dur', '1.3s');
				motion2.setAttribute('repeatCount', 'indefinite');
				motion2.setAttribute('path', rec.d);
				label.appendChild(motion2);
				g.appendChild(label);

				svgRoot.querySelector('.layer-evidence')?.appendChild(g);
				activeTokens.push(g);
			}
		}

		if (panel) panel.innerHTML = renderPanelHtml(ev);
	}

	function deactivate(): void {
		clearActive();
		activeId = null;
		if (panel) panel.innerHTML = PANEL_PLACEHOLDER;
	}

	const onKeydown = (e: KeyboardEvent) => {
		if (e.key === 'Escape') deactivate();
	};
	root.addEventListener('keydown', onKeydown);

	function redraw(): void {
		drawEdges();
		if (activeId) activate(activeId);
	}

	const resizeObserver = new win.ResizeObserver(() => redraw());
	resizeObserver.observe(root);

	// Initial paint: layout must settle before measuring cell rects.
	redraw();

	return function dispose(): void {
		root.removeEventListener('keydown', onKeydown);
		resizeObserver.disconnect();
		for (const fn of cleanupFns) fn();
		activeTokens.length = 0;
	};
}
