// Node unit tests for the public evidence-graph adapter.
// Run: node --test site/scripts/test-evidence-graph-adapter.mjs
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { EVENTS, renderIntentReview, timelineProjection } from '../src/graph/evidence-graph.ts';
import { fromEvidenceGraphV1, inspectEvidenceGraphV1 } from '../src/graph/from-v1.ts';
import {
	fromVerificationView,
	inspectVerificationView,
	verificationProjectionContext,
} from '../src/graph/from-verification-view.ts';

const FIXTURE_IDS = [
	'evt-h0',
	'evt-p1',
	'evt-p2',
	'evt-p3',
	'evt-e1',
	'evt-e2',
	'evt-h1',
	'evt-e3',
	'evt-e4',
	'evt-e5',
	'evt-r1',
	'evt-r2',
	'evt-r3',
	'evt-r4',
];

describe('evidence-graph fixture', () => {
	it('still exports 14 EVENTS', () => {
		assert.equal(EVENTS.length, 14);
		assert.deepEqual(
			EVENTS.map((event) => event.eventId),
			FIXTURE_IDS,
		);
	});
});

describe('fromEvidenceGraphV1', () => {
	it('maps a minimal v1 graph with one prompt and one tool_call', () => {
		const graph = {
			schema_version: 'hyodo.evidence-graph/v1',
			status: 'READY',
			reason: null,
			root: null,
			nodes: [
				{
					id: 'evt-prompt',
					type: 'event',
					run_id: 'run-1',
					ts: '2026-09-06T00:00:00Z',
					kind: 'prompt',
					actor: 'human',
					actor_id: null,
					step_index: 0,
					decision: null,
					policy: { rule_id: null, reason: null, evaluated_by: null },
					tool: { name: null, method: null, paths: [], urls: [] },
				},
				{
					id: 'evt-call',
					type: 'event',
					run_id: 'run-1',
					ts: '2026-09-06T00:00:01Z',
					kind: 'tool_call',
					actor: 'agent',
					actor_id: 'planner',
					step_index: 1,
					decision: null,
					policy: { rule_id: null, reason: null, evaluated_by: null },
					tool: { name: 'read_file', method: null, paths: ['src/a.py'], urls: [] },
				},
			],
			edges: [
				{
					type: 'parent_event_id',
					source: 'evt-prompt',
					target: 'evt-call',
					label: 'result_of',
				},
			],
			unresolved_refs: [],
			missions: { 'run-1': 'evt-prompt' },
			summary: { events: 2, edges: 1 },
		};

		const events = fromEvidenceGraphV1(graph);
		assert.equal(events.length, 2);
		assert.equal(events[0].schemaKind, 'prompt');
		assert.equal(events[0].eventId, 'evt-prompt');
		assert.equal(events[0].row, 'human');
		assert.equal(events[1].schemaKind, 'tool_call');
		assert.equal(events[1].eventId, 'evt-call');
		assert.equal(events[1].parentEventId, 'evt-prompt');
		assert.deepEqual(events[1].parentEventIds, ['evt-prompt']);
		assert.equal(events[1].tool?.name, 'read_file');
		// This graph reports no `rows`, and `actor` alone says only "agent".
		// Which kind of agent it was is exactly what went unreported, so the
		// event lands in the explicit unobserved lane. The adapter used to
		// answer `planner` here because the actor id contained "plan", which
		// is a claim the producer never made.
		assert.equal(events[1].row, 'unobserved');
		assert.equal(
			events.some((event) => event.policy?.decision === 'ALLOW'),
			false,
		);
	});

	it('preserves every Graph v2 parent without choosing a first parent', () => {
		const graph = {
			schema_version: 'hyodo.evidence-graph/v1',
			status: 'READY',
			reason: null,
			nodes: [
				{ id: 'left', kind: 'tool_call', actor: 'agent', step_index: 1, run_id: 'run-1', ts: '1' },
				{ id: 'right', kind: 'tool_call', actor: 'agent', step_index: 2, run_id: 'run-1', ts: '2' },
				{
					id: 'join',
					kind: 'tool_result',
					actor: 'agent',
					step_index: 3,
					run_id: 'run-1',
					ts: '3',
					parent_event_ids: ['right', 'left'],
				},
			],
			edges: [
				{ type: 'parent_event_id', source: 'right', target: 'join' },
				{ type: 'parent_event_id', source: 'left', target: 'join' },
			],
			unresolved_refs: [],
		};

		const join = fromEvidenceGraphV1(graph).find((event) => event.eventId === 'join');
		assert.ok(join);
		assert.deepEqual(join.parentEventIds, ['left', 'right']);
		assert.equal(join.parentEventId, null);
	});

	it('does not invent ALLOW when status is UNOBSERVED', () => {
		const graph = {
			schema_version: 'hyodo.evidence-graph/v1',
			status: 'UNOBSERVED',
			reason: 'ledger_unreadable',
			nodes: [
				{
					id: 'evt-prompt',
					kind: 'prompt',
					actor: 'human',
					step_index: 0,
					run_id: 'run-1',
					ts: '2026-09-06T00:00:00Z',
				},
				{
					id: 'evt-claimed-allow',
					kind: 'decision',
					actor: 'hyodo',
					step_index: 1,
					run_id: 'run-1',
					ts: '2026-09-06T00:00:01Z',
					decision: 'ALLOW',
					policy: { rule_id: 'claimed', reason: 'untrusted', evaluated_by: null },
				},
			],
			edges: [],
		};

		const events = fromEvidenceGraphV1(graph);
		assert.ok(events.length >= 1);
		assert.equal(
			events.some((event) => event.policy?.decision === 'ALLOW'),
			false,
		);
		const claimed = events.find((event) => event.eventId === 'evt-claimed-allow');
		assert.equal(claimed?.policy?.decision, 'UNOBSERVED');
		assert.equal(inspectEvidenceGraphV1(graph).status, 'UNOBSERVED');
		assert.equal(inspectEvidenceGraphV1(graph).reason, 'ledger_unreadable');
	});

	it('returns empty and does not throw on unknown or malformed graphs', () => {
		assert.deepEqual(fromEvidenceGraphV1(null), []);
		assert.deepEqual(fromEvidenceGraphV1('nope'), []);
		assert.deepEqual(fromEvidenceGraphV1({ schema_version: 'other', nodes: [] }), []);
		assert.deepEqual(
			fromEvidenceGraphV1({ schema_version: 'hyodo.evidence-graph/v1' }),
			[],
		);
		assert.equal(inspectEvidenceGraphV1(null).ok, false);
	});
});

describe('from-v1 reads canonical facts instead of guessing', () => {
	const graphWithRows = (role) => ({
		schema_version: 'hyodo.evidence-graph/v1',
		status: 'UNOBSERVED',
		reason: 'edge_validation_failed',
		nodes: [
			{
				id: 'evt-1',
				kind: 'decision',
				actor: 'agent',
				actor_id: 'plan-and-review-worker',
				step_index: 0,
				run_id: 'run-1',
				ts: '1',
				decision: 'ALLOW',
				policy: { decision: 'ALLOW', rule_id: 'r1', reason: 'recorded' },
				tool: { name: 'write_and_test_scanner', paths: [], urls: [] },
			},
		],
		edges: [],
		rows: { order: ['a'], rows: { a: { role, events: ['evt-1'] } } },
	});

	it('takes the lane from the role the producer already computed', () => {
		assert.equal(fromEvidenceGraphV1(graphWithRows('orchestrator'))[0].row, 'planner');
		assert.equal(fromEvidenceGraphV1(graphWithRows('worker'))[0].row, 'executor');
		assert.equal(fromEvidenceGraphV1(graphWithRows('reviewer'))[0].row, 'reviewer');
	});

	it('does not read the actor id, even when it contains a role word', () => {
		// The actor id is "plan-and-review-worker". Three substrings that the
		// old heuristic would have matched, and the producer's answer wins.
		assert.equal(fromEvidenceGraphV1(graphWithRows('worker'))[0].row, 'executor');
	});

	it('lands in the unobserved lane when no role was reported', () => {
		const graph = graphWithRows('worker');
		delete graph.rows;
		assert.equal(fromEvidenceGraphV1(graph)[0].row, 'unobserved');
	});

	it('never shows a decision it was not handed a presentable value for', () => {
		// A raw graph carries the recorded decision but not the value a viewer
		// may show. Reporting ALLOW here is exactly the false green this
		// adapter must not produce.
		const events = fromEvidenceGraphV1(graphWithRows('worker'));
		assert.equal(events[0].policy?.decision, 'UNOBSERVED');
		assert.equal(events[0].displayKind, 'unobserved');
	});

	it('does not classify an event by its tool name', () => {
		const graph = graphWithRows('worker');
		graph.nodes[0].kind = 'tool_call';
		graph.nodes[0].decision = null;
		graph.nodes[0].policy = {};
		// The tool is called "write_and_test_scanner". The old heuristic would
		// have called this a scan, a test run, and a file write at once.
		const [event] = fromEvidenceGraphV1(graph);
		assert.equal(event.displayKind, 'decision');
		assert.equal(event.tool?.name, 'write_and_test_scanner');
	});
});

describe('fromVerificationView', () => {
	const view = (overrides = {}) => ({
		schema_version: 'hyodo.verification-view/v0',
		status: 'READY',
		reason: null,
		authority: 'UNOBSERVED',
		presentation: { allow_withheld: false, reason: null },
		lanes: [
			{ lane_id: 'h', role: 'human', events: ['m1'] },
			{ lane_id: 'a', role: 'orchestrator', events: ['d1'] },
		],
		event_order: ['m1', 'd1'],
		events: {
			m1: {
				who: { actor: 'human', actor_id: null },
				what: { kind: 'prompt', tool_name: null, decision: null, decision_presentable: null },
				when: { ts: '1', step_index: 0 },
				where: { paths: [], urls: [], method: null },
				why: { reason: null, run_id: 'run-1' },
				how: { rule_id: null, evaluated_by: null, output_digest: null },
				causal_parents: [],
			},
			d1: {
				who: { actor: 'hyodo', actor_id: null },
				what: {
					kind: 'decision',
					tool_name: null,
					decision: 'ALLOW',
					decision_presentable: 'ALLOW',
				},
				when: { ts: '2', step_index: 1 },
				where: { paths: [], urls: [], method: null },
				why: { reason: 'tests passed', run_id: 'run-1' },
				how: { rule_id: 'r1', evaluated_by: 'hyodo', output_digest: null },
				causal_parents: ['m1'],
			},
		},
		edges_causal: [{ source: 'm1', target: 'd1' }],
		edges_evidence: [],
		...overrides,
	});

	it('takes lanes from the roles the producer computed', () => {
		const events = fromVerificationView(view());
		assert.deepEqual(
			events.map((event) => event.row),
			['human', 'planner'],
		);
	});

	it('preserves withheld intent comparisons and safely renders their labels', () => {
		const payload = view();
		const review = {
			mode: 'PROJECTED', target: 'outcome', intent_ref: 'm1',
			checks: [{ id: '<img src=x onerror=alert(1)>', dimension: 'constraints', basis: 'INFERRED',
				state: 'UNOBSERVED', comparison: 'SATISFIED', expected: 0, actual: 0, delta: 0,
				operator: 'lte', unit: 'count', evidence_refs: ['m1'], missing: ['hypothetical_comparison'] }],
		};
		payload.events.d1.why.intent_review = review;
		const [, event] = fromVerificationView(payload);
		assert.deepEqual(event.intentReview, review);
		const html = renderIntentReview(event.intentReview);
		assert.ok(html.includes('UNOBSERVED'));
		assert.ok(html.includes('reported actual: 0'));
		assert.ok(html.includes('&lt;img'));
		assert.ok(!html.includes('<img'));
	});

	it('shows the presentable decision, not the recorded one', () => {
		const withheld = view({
			presentation: { allow_withheld: true, reason: 'graph_status:UNOBSERVED' },
			status: 'UNOBSERVED',
		});
		withheld.events.d1.what.decision_presentable = 'UNOBSERVED';
		const [, decision] = fromVerificationView(withheld);
		assert.equal(decision.policy?.decision, 'UNOBSERVED');
		assert.equal(decision.displayKind, 'unobserved');
	});

	it('keeps columns as classification and does not infer event observation', () => {
		const payload = view({
			status: 'UNOBSERVED',
			presentation: { allow_withheld: true, reason: 'graph_status:UNOBSERVED' },
			missing: { unresolved_refs: ['d1'], calls_without_result: [] },
		});
		payload.events.d1.when.ts = null;
		payload.events.d1.what.decision_presentable = 'UNOBSERVED';
		payload.events.d1.columns = ['jin', 'in'];
		const [, decision] = fromVerificationView(payload);
		assert.equal(decision.ts, '');
		assert.equal(decision.lensStates?.jin, 'UNOBSERVED');
		assert.equal(decision.lensStates?.seon, 'UNOBSERVED');
		assert.deepEqual(decision.lensClassifications, ['jin', 'in']);
		assert.equal(decision.continuityState, 'UNOBSERVED');
		assert.deepEqual(decision.missing, ['unresolved_refs']);
		assert.equal(decision.recordedDecision, 'ALLOW');
		assert.equal(decision.presentableDecision, 'UNOBSERVED');
		assert.equal(verificationProjectionContext(payload).canonical, true);
	});

	it('preserves producer event order instead of sorting or parsing timestamps', () => {
		const payload = view({
			event_order: ['d1', 'm1'],
		});
		payload.events.d1.when.ts = '2026-09-06T09:02:00-07:00';
		payload.events.m1.when.ts = '2026-09-06T09:01:00-07:00';
		const projection = timelineProjection(fromVerificationView(payload));
		assert.deepEqual(projection.labels, [
			'TS 2026-09-06T09:02:00-07:00',
			'TS 2026-09-06T09:01:00-07:00',
		]);
		assert.equal(projection.columnByEvent.get('d1'), 0);
		assert.equal(projection.columnByEvent.get('m1'), 1);
	});

	it('never draws an edge for a citation that resolved to nothing', () => {
		const withBrokenRef = view({
			edges_evidence: [
				{ source: 'nowhere', target: 'd1', target_kind: 'event', source_resolved: false },
				{ source: 'm1', target: 'd1', target_kind: 'event', source_resolved: true },
			],
		});
		const [, decision] = fromVerificationView(withBrokenRef);
		assert.deepEqual(decision.evidenceRefs, ['m1']);
	});

	it('treats a view with no presentation block as withholding', () => {
		const noBlock = view();
		delete noBlock.presentation;
		// Absence of the flag is not permission to light green.
		assert.equal(inspectVerificationView(noBlock).allowWithheld, true);
	});

	it('returns empty and does not throw on unknown or malformed input', () => {
		assert.deepEqual(fromVerificationView(null), []);
		assert.deepEqual(fromVerificationView({ schema_version: 'other' }), []);
		assert.deepEqual(fromVerificationView({ schema_version: 'hyodo.verification-view/v0' }), []);
		assert.equal(inspectVerificationView({}).ok, false);
	});
});
