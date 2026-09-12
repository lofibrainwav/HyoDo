import './evidence-graph';

declare module './evidence-graph' {
	interface EvidenceEvent {
		/** Graph-v2 causal parents. Omitted by legacy fixtures; adapters preserve it when observed. */
		parentEventIds?: string[];
	}
}

export {};
