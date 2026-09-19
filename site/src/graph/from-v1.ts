// Legacy adapter: hyodo.evidence-graph/v1 JSON -> the page's EvidenceEvent[].
//
// No DOM, no fetch, no storage. Unknown or malformed input must not throw
// and must not invent an ALLOW (unobserved is never green).
//
// A raw evidence graph is a record of what happened, not a decided view of
// it. This adapter therefore reads the lane roles the producer already
// attached as `rows` and reports every decision as UNOBSERVED, because the
// value a viewer may show is computed by `hyodo/verification_view.py` and
// shipped as `decision_presentable` in `hyodo.verification-view/v0`. Load
// that file (`GET /api/verification-view`) to see decisions.
//
// What this adapter must never do is decide for itself. It previously guessed
// a lane from substrings of `actor_id` and a chip class from substrings of a
// tool name, which is how a viewer starts disagreeing with its own producer
// about facts the producer had already measured.

import type {
	Decision,
	DisplayKind,
	EvidenceEvent,
	Row,
	SchemaEventKind,
} from './evidence-graph';

export const EVIDENCE_GRAPH_V1 = 'hyodo.evidence-graph/v1';

const SCHEMA_KINDS = new Set<string>([
	'prompt',
	'tool_call',
	'tool_result',
	'model_response',
	'error',
	'decision',
]);

export interface EvidenceGraphV1Info {
	/** True when the payload is a v1 object with a nodes array. Not READY. */
	ok: boolean;
	status: string | null;
	reason: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asNonEmptyString(value: unknown): string | null {
	return typeof value === 'string' && value.trim() ? value : null;
}

function asSchemaKind(value: unknown): SchemaEventKind | null {
	return typeof value === 'string' && SCHEMA_KINDS.has(value)
		? (value as SchemaEventKind)
		: null;
}

function asStepIndex(value: unknown): number | null {
	return typeof value === 'number' && Number.isInteger(value) && value >= 0 ? value : null;
}

function uniqueStrings(value: unknown): string[] {
	if (!Array.isArray(value)) return [];
	return Array.from(
		new Set(value.filter((item): item is string => typeof item === 'string' && item.trim() !== '')),
	).sort();
}

/**
 * Read schema/status/reason without mapping nodes. Never throws.
 * `ok` means "this is a v1 graph we can attempt to render", not READY.
 */
export function inspectEvidenceGraphV1(graph: unknown): EvidenceGraphV1Info {
	if (!isRecord(graph)) {
		return { ok: false, status: null, reason: 'not_an_object' };
	}
	const status = typeof graph.status === 'string' ? graph.status : null;
	if (graph.schema_version !== EVIDENCE_GRAPH_V1) {
		return { ok: false, status, reason: 'unsupported_schema' };
	}
	if (!Array.isArray(graph.nodes)) {
		return { ok: false, status, reason: 'missing_nodes' };
	}
	const reason = typeof graph.reason === 'string' ? graph.reason : null;
	return { ok: true, status, reason };
}

function mapTool(raw: unknown): EvidenceEvent['tool'] {
	if (!isRecord(raw)) return null;
	const name = asNonEmptyString(raw.name);
	const paths = Array.isArray(raw.paths)
		? raw.paths.filter((item): item is string => typeof item === 'string' && item.trim() !== '')
		: [];
	const urls: string[] = [];
	if (Array.isArray(raw.urls)) {
		for (const entry of raw.urls) {
			if (typeof entry === 'string' && entry.trim()) {
				urls.push(entry);
			} else if (isRecord(entry)) {
				const domain = asNonEmptyString(entry.domain);
				if (domain) urls.push(domain);
			}
		}
	}
	if (!name && paths.length === 0 && urls.length === 0) return null;
	return { name: name ?? 'tool', paths, urls };
}

/**
 * The one place the canonical role vocabulary meets this page's lane
 * vocabulary. Mirrors `_DAW_LANE_BY_ROLE` in `hyodo/dashboard.py`.
 */
const LANE_BY_ROLE: Record<string, Row> = {
	human: 'human',
	orchestrator: 'planner',
	reviewer: 'reviewer',
	worker: 'executor',
};

/**
 * Lane from the `actor` schema field alone, used only when the producer
 * reported no role. `actor` is a closed vocabulary (`human`, `hyodo`,
 * `agent`), so reading it is reading a recorded fact, not guessing — this
 * mirrors the fallback in `_daw_track` in `hyodo/dashboard.py`.
 *
 * A bare `agent` stays unobserved on purpose. Which kind of agent it was is
 * precisely what went unreported, and calling it an executor would answer a
 * question nobody measured.
 */
function laneFromActor(actor: string): Row {
	if (actor === 'human') return 'human';
	if (actor === 'hyodo') return 'reviewer';
	return 'unobserved';
}

/**
 * Index `event_id -> Row` from the `rows` the producer already computed.
 * `build_report_graph` attaches it to every payload it serves. A payload
 * without it yields an empty index and every event lands in the explicit
 * unobserved lane, which is the honest answer when no role was reported.
 */
function rowIndex(graph: Record<string, unknown>): Map<string, Row> {
	const rowOf = new Map<string, Row>();
	const rows = isRecord(graph.rows) ? graph.rows : null;
	const table = rows && isRecord(rows.rows) ? rows.rows : null;
	if (!table) return rowOf;
	for (const entry of Object.values(table)) {
		if (!isRecord(entry)) continue;
		const role = asNonEmptyString(entry.role);
		const lane: Row = (role && LANE_BY_ROLE[role]) || 'unobserved';
		if (!Array.isArray(entry.events)) continue;
		for (const eventId of entry.events) {
			if (typeof eventId === 'string' && eventId.trim()) rowOf.set(eventId, lane);
		}
	}
	return rowOf;
}

function displayKindOf(schemaKind: SchemaEventKind, decision: Decision | null): DisplayKind {
	// Derived only from schema fields. The tool's name is deliberately not
	// read: a name is what something is called, not what it did, which is the
	// same reason `graph_view.carries_measured_evidence` refuses to count it.
	if (schemaKind === 'decision') return decision === 'UNOBSERVED' ? 'unobserved' : 'decision';
	if (schemaKind === 'prompt') return 'mission';
	if (schemaKind === 'error') return 'unobserved';
	return 'decision';
}

function linkMaps(graph: Record<string, unknown>): {
	parentsOf: Map<string, string[]>;
	evidenceOf: Map<string, string[]>;
} {
	const parentSets = new Map<string, Set<string>>();
	const evidenceOf = new Map<string, string[]>();
	const edges = Array.isArray(graph.edges) ? graph.edges : [];
	for (const edge of edges) {
		if (!isRecord(edge)) continue;
		const source = asNonEmptyString(edge.source);
		const target = asNonEmptyString(edge.target);
		if (!source || !target) continue;
		if (edge.type === 'parent_event_id') {
			const set = parentSets.get(target) ?? new Set<string>();
			set.add(source);
			parentSets.set(target, set);
		} else if (edge.type === 'evidence_ref') {
			const list = evidenceOf.get(target) ?? [];
			list.push(source);
			evidenceOf.set(target, list);
		}
	}
	const unresolved = Array.isArray(graph.unresolved_refs) ? graph.unresolved_refs : [];
	for (const issue of unresolved) {
		if (!isRecord(issue)) continue;
		if (issue.field !== 'parent_event_id' && issue.field !== 'parent_event_ids') continue;
		const eventId = asNonEmptyString(issue.event_id);
		const ref = asNonEmptyString(issue.ref);
		if (!eventId || !ref) continue;
		const set = parentSets.get(eventId) ?? new Set<string>();
		set.add(ref);
		parentSets.set(eventId, set);
	}
	const parentsOf = new Map<string, string[]>();
	for (const [target, parents] of parentSets) {
		parentsOf.set(target, Array.from(parents).sort());
	}
	for (const [target, refs] of evidenceOf) {
		evidenceOf.set(target, Array.from(new Set(refs)).sort());
	}
	return { parentsOf, evidenceOf };
}

function nodeParentIds(node: Record<string, unknown>, parentsOf: Map<string, string[]>): string[] {
	const fromEdges = parentsOf.get(String(node.id ?? ''));
	if (fromEdges && fromEdges.length) return fromEdges;
	const plural = uniqueStrings(node.parent_event_ids);
	if (plural.length) return plural;
	const singular = asNonEmptyString(node.parent_event_id);
	return singular ? [singular] : [];
}

function nodeEvidenceRefs(
	node: Record<string, unknown>,
	evidenceOf: Map<string, string[]>,
): string[] {
	const fromEdges = evidenceOf.get(String(node.id ?? ''));
	if (fromEdges && fromEdges.length) return fromEdges;
	return uniqueStrings(node.evidence_refs);
}

/**
 * Map a `hyodo.evidence-graph/v1` payload into page events.
 * Malformed input returns `[]` (never throws, never defaults to ALLOW).
 */
export function fromEvidenceGraphV1(graph: unknown): EvidenceEvent[] {
	const info = inspectEvidenceGraphV1(graph);
	if (!info.ok || !isRecord(graph) || !Array.isArray(graph.nodes)) return [];

	const { parentsOf, evidenceOf } = linkMaps(graph);
	const rowOf = rowIndex(graph);
	const seen = new Set<string>();
	const events: EvidenceEvent[] = [];

	for (const raw of graph.nodes) {
		if (!isRecord(raw)) continue;
		const eventId = asNonEmptyString(raw.id);
		const schemaKind = asSchemaKind(raw.kind);
		const stepIndex = asStepIndex(raw.step_index);
		if (!eventId || !schemaKind || stepIndex === null) continue;
		if (seen.has(eventId)) continue;
		seen.add(eventId);

		const actor = asNonEmptyString(raw.actor) ?? 'agent';
		const actorId = asNonEmptyString(raw.actor_id);
		const row = rowOf.get(eventId) ?? laneFromActor(actor);
		const tool = mapTool(raw.tool);
		const policyBlock = isRecord(raw.policy) ? raw.policy : null;
		// A raw graph carries the recorded decision but not the value a viewer
		// may show. That value is `decision_presentable` in
		// `hyodo.verification-view/v0`. Rather than re-derive it here and drift
		// from the producer, this adapter reports UNOBSERVED for every decision
		// and leaves the recorded value to the canonical view.
		const decision: Decision | null = schemaKind === 'decision' ? 'UNOBSERVED' : null;
		const ruleId = policyBlock ? asNonEmptyString(policyBlock.rule_id) : null;
		const reason = policyBlock ? asNonEmptyString(policyBlock.reason) : null;
		const parentEventIds = nodeParentIds(raw, parentsOf);
		const parentEventId = parentEventIds.length === 1 ? parentEventIds[0] : null;
		const evidenceRefs = nodeEvidenceRefs(raw, evidenceOf);
		const policy = decision === null ? null : { decision, ruleId, reason };

		events.push({
			eventId,
			runId: asNonEmptyString(raw.run_id) ?? '',
			ts: asNonEmptyString(raw.ts) ?? '',
			schemaKind,
			displayKind: displayKindOf(schemaKind, decision),
			actor: actorId ? `${actor}:${actorId}` : actor,
			row,
			stepIndex,
			tool,
			policy,
			parentEventId,
			parentEventIds,
			evidenceRefs,
			note: reason ?? '',
		});
	}

	return events;
}
