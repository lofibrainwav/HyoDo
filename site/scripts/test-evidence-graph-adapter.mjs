// Node unit tests for the public evidence-graph adapter.
// Run: node --test site/scripts/test-evidence-graph-adapter.mjs
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { EVENTS } from '../src/graph/evidence-graph.ts';
import { fromEvidenceGraphV1, inspectEvidenceGraphV1 } from '../src/graph/from-v1.ts';

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
		assert.equal(events[1].row, 'planner');
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
