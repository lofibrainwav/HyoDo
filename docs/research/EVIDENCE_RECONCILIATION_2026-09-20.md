# Evidence reconciliation receipt — 2026-09-20

This receipt replays the local 9,621-event ledger through the canonical
`build_report_graph -> build_verification_view` path. It is a read-only
reconciliation of recorded evidence, not a repair of historical events and not
an authorization decision.

## Frozen input

- Ledger events: **9,621**
- Ledger SHA-256: `05b4dc6b6fddb1fda9b45ec221e4e1b21a0aeb957c8f00e37743acf9bca120c7`
- Causal edges: **4,753**
- Evidence edges: **1**
- Unresolved references: **0**
- Cross-run references: **0**

The ledger is not modified or backfilled by reconciliation. Raw prompt or tool
bodies are not introduced.

## Terminal disposition

One tool call receives one derived terminal disposition. `RETURNED` means only
that a recorded terminal result event exists; it does not mean semantic success.

- Tool calls: **4,965**
- `RETURNED`: **4,649**
- `UNOBSERVED`: **316**
- `ERROR`, `CANCELLED`, `TIMEOUT`, `ABORTED`: **0 observed**
- duplicate / contradictory terminal receipts: **0**
- undispositioned calls: **0**

The 316 legacy calls remain `UNOBSERVED`. No result, error, cancellation,
timeout, or abort state is inferred after the fact. Producer inspection found
all 316 under Codex, whose measured hook payload does not expose a structured
terminal-mode field; that terminal lane therefore remains
`RECONCILIATION_REQUIRED` at the producer boundary rather than being mislabeled
as a repository-side failure.

## Recording disposition

The old `unmeasured_events = 5,161` bucket mixed lifecycle-minimal call
records with missing result measurement. The stricter recording disposition is:

- `MEASURED`: **4,415**
- `INTENTIONALLY_MINIMAL`: **4,964**
- `STRUCTURAL_CONTEXT`: **6**
- `MEASUREMENT_UNOBSERVED`: **236**
- unexplained required recording gaps: **0**

`INTENTIONALLY_MINIMAL` does not mean measured. It means the event is a
pre-outcome call record and reconciliation refuses to manufacture measurement
fields. The 236 result events with no measured output remain explicitly
`MEASUREMENT_UNOBSERVED`.

## Lens mapping disposition

The legacy viewer still exposes its compatibility columns. Reconciliation is
stricter: a tool name or metadata tag alone is not lens evidence.

- `MAPPED`: **8**
- `INSUFFICIENT_MEASUREMENT`: **5,200**
- `SEMANTICS_UNOBSERVED`: **4,413**
- `NOT_APPLICABLE`: **0**
- `MAPPING_GAP`: **0**

The difference between the legacy 5,161 unmeasured count and the stricter
5,200 insufficient-measurement count is deliberate: 39 compatibility-column
tool-call assignments were driven by a tool label without measured lens
semantics. Reconciliation does not accept those labels as evidence.

The legacy 4,382 unclassified result events carry an output digest but no
explicit lens-semantic field. Reconciliation also finds 31 result events that
legacy compatibility columns placed from a tool label despite the same semantic
absence. The combined 4,413 therefore stay `SEMANTICS_UNOBSERVED`, not evidence
that the lens engine is broken and not candidates for heuristic classification.

## Intent provenance

Fifteen runs are recorded in the ledger:

- `RECORDED_INTENT`: **3**
- `ADMISSION_UNOBSERVED`: **12**
- `EXPLICIT_NO_INTENT`: **0**
- undispositioned runs: **0**
- unauthorized executions: **NOT_PROVEN**

A run without a recorded human-intent/admission receipt is not relabeled as an
unauthorized execution. That conclusion would require separate authority or
host-admission evidence.

## Boundary

This reconciliation adds no score, confidence, virtue aggregate, execution
permission, or retroactive event. HyoDo reports what the evidence supports and
keeps missing evidence visible.
