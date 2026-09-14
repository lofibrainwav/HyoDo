# HyoDo multimodal evaluation contract

This is a shadow evaluation contract only. HyoDo may validate an evaluation
receipt and report evidence quality; it does not run encoders, choose models,
promote models, or grant execution authority.

## Evaluation envelope

Each JSONL evaluation case carries these fields:

```json
{
  "eval_id": "eval-2026-09-13-001",
  "scenario": "wrong-event-match",
  "modality": "cross-modal",
  "input_fixture": "fixtures/events/event-a-text-to-image.json",
  "expected_behavior": "reject a result bound to event-b",
  "forbidden_behavior": "accept a result with a mismatched event_id",
  "required_evidence": ["event_id", "asset_digest", "model_id", "model_version"],
  "oracle": "exact_event_binding",
  "critical_invariants": ["no_deleted_asset_leakage", "fresh_provenance"],
  "result": "REJECT",
  "confidence": null
}
```

`confidence` is optional metadata and is never an authority signal. A missing
or non-verifiable field produces `UNOBSERVED` or `PARTIAL`; it cannot become a
pass through a score.

## Required scenario coverage

The shadow suite should include text retrieval, vision retrieval, audio
retrieval, music retrieval, and cross-modal retrieval, plus:

- event binding and wrong-event match;
- provenance completeness and stale embedding;
- deleted asset leakage and temporal mismatch;
- entity mismatch and model/version mismatch.

## Result and metrics

Allowed case results are `PASS`, `FAIL`, `PARTIAL`, and `UNOBSERVED`. Suggested
aggregate metrics are Recall@K, MRR, nDCG, false-positive rate,
cross-modal consistency, provenance completeness, freshness, readback, and
latency. Metrics are review signals only; they do not authorize execution or
model promotion.

Every aggregate receipt must bind to the fixture digest, evaluator version,
source SHA, measured-at timestamp, and a readback status. A receipt without
those bindings remains `UNOBSERVED`.

## Ownership boundary

Memory, Eye, Ear, retrieval, embedding, event storage, and model lifecycle
remain external producer/owner concerns. HyoDo consumes bounded metadata and
evidence references, validates the contract, and reports evaluation status.
It must not become a memory writer, change an `AUTO_RUN` threshold, or treat an
evaluation receipt as KINGDOM authority.
