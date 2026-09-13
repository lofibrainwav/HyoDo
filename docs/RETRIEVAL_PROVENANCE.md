# Retrieval provenance

HyoDo 4.19.4 can carry a bounded, compatibility-scoped projection of a
KINGDOM/QMD retrieval on a
`hyodo.agent-event/v1` event. The carrier is `provenance.retrieval/v1`.

The projection preserves `source_sha`, `run_id`, `qmd_uri`, `evidence_ref`, a
SHA-256 `result_digest`, bounded `result_metadata`, and a deterministic
lowercase 64-character `receipt_id`. The receipt ID is the SHA-256 of canonical
JSON containing those five identity fields:

```text
{source_sha, run_id, qmd_uri, evidence_ref, result_digest}
```

Canonical JSON recursively sorts object keys, preserves retrieval array order,
and is encoded as UTF-8. `qmd_result` is accepted only long enough to compute
the digest; it is never written to the HyoDo event ledger.

`result_metadata` is closed and bounded: at most eight keys from the schema
allowlist, depth two, scalar values only, and strings no longer than 256
characters. Queries, prompts, document bodies, authority, approval, and
execution tokens are not carrier fields. A legacy raw `retrieval_receipt` is
rejected with `unsupported_field:retrieval_receipt`.

`qmd_uri` is a v1 KINGDOM/QMD-specific compatibility field. A future generic
retrieval contract may use provider-neutral `provider`, `retrieval_ref`, and
`resource_ref` fields without breaking v1.

The event's execution `provenance.source_sha`, when present, must equal the
retrieval subject. Retrieval `run_id` and an explicitly supplied event
`evidence_ref` must also match. Existing gate `evidence_refs` remain a separate
surface and are not used as retrieval provenance.

Missing or mismatched fields fail closed. Replaying the same normalized event
is idempotent through the normal event ledger; reusing an event ID with a
different projection is a conflict. The projection records provenance only and
does not grant authority, policy approval, or Neo4j seal status.
