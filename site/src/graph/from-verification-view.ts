// Pure adapter: hyodo.verification-view/v0 JSON -> the page's EvidenceEvent[].
//
// No DOM, no fetch, no storage. This adapter derives nothing. Lanes, roles,
// and the presentable decision all arrive already decided by
// `hyodo/verification_view.py`, which is the point: a viewer that re-decides
// what its producer already measured will eventually disagree with it.
//
// Presentation may compress truth. It must never reconstruct truth.

import type {
	Decision,
	DisplayKind,
	EvidenceEvent,
	LensKey,
	ObservationState,
	Row,
	SchemaEventKind,
	VerificationProjectionContext,
} from './evidence-graph';

export const VERIFICATION_VIEW_V0 = 'hyodo.verification-view/v0';

const SCHEMA_KINDS = new Set<string>([
	'prompt',
	'tool_call',
	'tool_result',
	'model_response',
	'error',
	'decision',
]);

const DECISIONS = new Set<string>(['ALLOW', 'ASK', 'DENY', 'UNOBSERVED']);

/**
 * The one place the canonical role vocabulary meets this page's lane
 * vocabulary. `orchestrator` becomes the planner lane because that lane means
 * "spawned other work", which is what `build_actor_rows` observes to call a
 * row an orchestrator. Mirrors `_DAW_LANE_BY_ROLE` in `hyodo/dashboard.py`.
 */
const LANE_BY_ROLE: Record<string, Row> = {
	human: 'human',
	orchestrator: 'planner',
	reviewer: 'reviewer',
	worker: 'executor',
};

export interface VerificationViewInfo {
	/** True when this is a v0 view object with an events map. Not READY. */
	ok: boolean;
	status: string | null;
	reason: string | null;
	allowWithheld: boolean;
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asNonEmptyString(value: unknown): string | null {
	return typeof value === 'string' && value.trim() ? value : null;
}

function asStepIndex(value: unknown): number | null {
	return typeof value === 'number' && Number.isInteger(value) && value >= 0 ? value : null;
}

function stringList(value: unknown): string[] {
	if (!Array.isArray(value)) return [];
	return value.filter((item): item is string => typeof item === 'string' && item.trim() !== '');
}

function decisionValue(value: unknown): Decision | null {
	return typeof value === 'string' && DECISIONS.has(value) ? (value as Decision) : null;
}

function missingByEvent(view: Record<string, unknown>): Map<string, string[]> {
	const result = new Map<string, string[]>();
	const missing = isRecord(view.missing) ? view.missing : {};
	for (const [bucket, entries] of Object.entries(missing)) {
		if (!Array.isArray(entries)) continue;
		for (const entry of entries) {
			const eventId = typeof entry === 'string' ? entry : isRecord(entry) ? entry.event_id : null;
			if (typeof eventId !== 'string') continue;
			result.set(eventId, [...(result.get(eventId) ?? []), bucket]);
		}
	}
	return result;
}

export function verificationProjectionContext(view: unknown): VerificationProjectionContext {
	const info = inspectVerificationView(view);
	const record = isRecord(view) ? view : {};
	const rawMissing = isRecord(record.missing) ? record.missing : {};
	const missing = Object.fromEntries(
		Object.entries(rawMissing).map(([key, value]) => [key, Array.isArray(value) ? value : []]),
	);
	return {
		status: info.status,
		allowWithheld: info.allowWithheld,
		missing,
		canonical: info.ok,
	};
}

/** Read schema/status without mapping events. Never throws. */
export function inspectVerificationView(view: unknown): VerificationViewInfo {
	const empty = { ok: false, status: null, reason: 'not_an_object', allowWithheld: true };
	if (!isRecord(view)) return empty;
	const status = typeof view.status === 'string' ? view.status : null;
	if (view.schema_version !== VERIFICATION_VIEW_V0) {
		return { ok: false, status, reason: 'unsupported_schema', allowWithheld: true };
	}
	if (!isRecord(view.events)) {
		return { ok: false, status, reason: 'missing_events', allowWithheld: true };
	}
	const presentation = isRecord(view.presentation) ? view.presentation : null;
	// A view that does not say whether an ALLOW was withheld is treated as if
	// one was. Absence of the flag is not permission to light green.
	const allowWithheld = presentation?.allow_withheld !== false;
	const reason = typeof view.reason === 'string' ? view.reason : null;
	return { ok: true, status, reason, allowWithheld };
}

/** Map `lane_id -> Row` and `event_id -> lane_id` from the view's own lanes. */
function laneIndex(view: Record<string, unknown>): Map<string, Row> {
	const rowOf = new Map<string, Row>();
	const lanes = Array.isArray(view.lanes) ? view.lanes : [];
	for (const lane of lanes) {
		if (!isRecord(lane)) continue;
		const role = asNonEmptyString(lane.role);
		// An unmapped or absent role becomes the explicit unobserved lane. It
		// is never guessed from an actor id, a tool name, or anything else the
		// producer declined to claim.
		const row: Row = (role && LANE_BY_ROLE[role]) || 'unobserved';
		for (const eventId of stringList(lane.events)) rowOf.set(eventId, row);
	}
	return rowOf;
}

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

function presentableDecision(what: Record<string, unknown>): Decision | null {
	// The producer already applied the fail-closed rule and shipped the answer
	// as `decision_presentable`. This reads it; it does not re-derive it.
	const raw = what.decision_presentable;
	if (typeof raw !== 'string' || !DECISIONS.has(raw)) return null;
	return raw as Decision;
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

/**
 * Map a `hyodo.verification-view/v0` payload into page events.
 * Malformed input returns `[]` (never throws, never invents an ALLOW).
 */
export function fromVerificationView(view: unknown): EvidenceEvent[] {
	const info = inspectVerificationView(view);
	if (!info.ok || !isRecord(view) || !isRecord(view.events)) return [];

	const rowOf = laneIndex(view);
	const missing = missingByEvent(view);
	const order = stringList(view.event_order);
	const ids = order.length ? order : Object.keys(view.events).sort();

	const evidenceOf = new Map<string, string[]>();
	const edges = Array.isArray(view.edges_evidence) ? view.edges_evidence : [];
	for (const edge of edges) {
		if (!isRecord(edge)) continue;
		const source = asNonEmptyString(edge.source);
		const target = asNonEmptyString(edge.target);
		// An unresolved citation never becomes an edge. The producer reports it
		// under `missing.unresolved_refs` and this adapter keeps it that way.
		if (!source || !target || edge.source_resolved === false) continue;
		evidenceOf.set(target, [...(evidenceOf.get(target) ?? []), source]);
	}

	const events: EvidenceEvent[] = [];
	for (const eventId of ids) {
		const entry = view.events[eventId];
		if (!isRecord(entry)) continue;
		const who = isRecord(entry.who) ? entry.who : {};
		const what = isRecord(entry.what) ? entry.what : {};
		const when = isRecord(entry.when) ? entry.when : {};
		const where = isRecord(entry.where) ? entry.where : {};
		const why = isRecord(entry.why) ? entry.why : {};
		const how = isRecord(entry.how) ? entry.how : {};

		const kind = asNonEmptyString(what.kind);
		const stepIndex = asStepIndex(when.step_index);
		if (!kind || !SCHEMA_KINDS.has(kind) || stepIndex === null) continue;
		const schemaKind = kind as SchemaEventKind;

		const decision = presentableDecision(what);
		const recordedDecision = decisionValue(what.decision);
		const columns = stringList(entry.columns);
		const lensStates = Object.fromEntries(
			(['jin', 'seon', 'mi', 'in', 'hyo'] as LensKey[]).map((key) => [
				key,
				(columns.includes(key) ? 'OBSERVED' : 'UNOBSERVED') as ObservationState,
			]),
		) as Partial<Record<LensKey, ObservationState>>;
		const toolName = asNonEmptyString(what.tool_name);
		const paths = stringList(where.paths);
		const urls = stringList(where.urls);
		const actor = asNonEmptyString(who.actor) ?? 'agent';
		const actorId = asNonEmptyString(who.actor_id);
		const parents = stringList(entry.causal_parents);

		events.push({
			eventId,
			runId: asNonEmptyString(why.run_id) ?? '',
			ts: asNonEmptyString(when.ts) ?? '',
			schemaKind,
			displayKind: displayKindOf(schemaKind, decision),
			actor: actorId ? `${actor}:${actorId}` : actor,
			row: rowOf.get(eventId) ?? laneFromActor(actor),
			stepIndex,
			tool:
				toolName || paths.length || urls.length
					? { name: toolName ?? 'tool', paths, urls }
					: null,
			policy:
				decision === null
					? null
					: {
							decision,
							ruleId: asNonEmptyString(how.rule_id),
							reason: asNonEmptyString(why.reason),
						},
			parentEventId: parents.length === 1 ? parents[0] : null,
			parentEventIds: parents,
			evidenceRefs: Array.from(new Set(evidenceOf.get(eventId) ?? [])).sort(),
			note: asNonEmptyString(why.reason) ?? '',
			intentReview: isRecord(why.intent_review) ? why.intent_review : null,
			lensStates,
			continuityState: 'UNOBSERVED',
			recordedDecision,
			presentableDecision: decision,
			missing: missing.get(eventId) ?? [],
		});
	}

	return events;
}
