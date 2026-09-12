// Pure adapter: hyodo.evidence-graph/v1 JSON -> the page's EvidenceEvent[].
//
// No DOM, no fetch, no storage. Unknown or malformed input must not throw
// and must not invent an ALLOW (unobserved is never green).

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

const DECISIONS = new Set<string>(['ALLOW', 'ASK', 'DENY', 'UNOBSERVED']);

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

function asDecision(value: unknown): Decision | null {
	return typeof value === 'string' && DECISIONS.has(value) ? (value as Decision) : null;
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

function mapDecision(raw: unknown, graphStatus: string | null): Decision | null {
	const decision = asDecision(raw);
	// Fail-closed: an UNOBSERVED graph must not light ALLOW (fake-green).
	if (graphStatus === 'UNOBSERVED' && decision === 'ALLOW') return 'UNOBSERVED';
	return decision;
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

function deriveRow(actor: string, actorId: string | null): Row {
	if (actor === 'human') return 'human';
	const id = (actorId ?? '').toLowerCase();
	if (id.includes('plan')) return 'planner';
	if (id.includes('review')) return 'reviewer';
	if (id.includes('exec') || id.includes('work')) return 'executor';
	if (actor === 'hyodo') return 'reviewer';
	return 'executor';
}

function deriveDisplayKind(
	schemaKind: SchemaEventKind,
	toolName: string | null,
	decision: Decision | null,
	row: Row,
	hasParent: boolean,
): DisplayKind {
	if (schemaKind === 'decision') {
		return decision === 'UNOBSERVED' ? 'unobserved' : 'decision';
	}
	const name = (toolName ?? '').toLowerCase();
	if (name.includes('scan') || name.includes('notify')) return 'scan';
	if (name.includes('test')) return 'run_tests';
	if (name.includes('write') || name.includes('edit')) return 'write_file';
	if (name.includes('read')) return 'read_file';
	if (schemaKind === 'prompt') {
		return row === 'human' && hasParent ? 'approve' : 'mission';
	}
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
		const row = deriveRow(actor, actorId);
		const tool = mapTool(raw.tool);
		const policyBlock = isRecord(raw.policy) ? raw.policy : null;
		const decision = mapDecision(
			raw.decision !== undefined && raw.decision !== null
				? raw.decision
				: policyBlock?.decision,
			info.status,
		);
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
			displayKind: deriveDisplayKind(
				schemaKind,
				tool?.name ?? null,
				decision,
				row,
				parentEventIds.length > 0,
			),
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
