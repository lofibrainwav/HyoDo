"""Adversarial contract tests for bounded retrieval provenance."""

from __future__ import annotations

import json
from pathlib import Path

from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    AGENT_EVENTS_RELATIVE_PATH,
    EVENT_ID_CONFLICT,
    EVENT_ID_DUPLICATE,
    append_agent_event,
    check_event_id,
    read_agent_events,
    validate_event,
)
from hyodo.retrieval_provenance import (
    RETRIEVAL_PROVENANCE_SCHEMA_VERSION,
    canonical_json,
    normalize_qmd_uri,
    normalize_retrieval_projection,
    projection_receipt_id,
    result_digest,
)

SOURCE_SHA = "a" * 40
RUN_ID = "run-1"
EVENT_ID = "event-1"
EVIDENCE_REF = "retrieval-evidence-1"
QMD_URI = "qmd://knowledge/guide.md"


def _projection(**overrides: object) -> dict[str, object]:
    result: object = {"title": "hello", "score": 0.9}
    digest = result_digest(result)
    base: dict[str, object] = {
        "schema_version": RETRIEVAL_PROVENANCE_SCHEMA_VERSION,
        "source_sha": SOURCE_SHA,
        "run_id": RUN_ID,
        "qmd_uri": QMD_URI,
        "evidence_ref": EVIDENCE_REF,
        "result_digest": digest,
        "result_metadata": {"result_count": 1, "collection": "knowledge"},
        "receipt_id": projection_receipt_id(
            source_sha=SOURCE_SHA,
            run_id=RUN_ID,
            qmd_uri=QMD_URI,
            evidence_ref=EVIDENCE_REF,
            result_digest=digest,
        ),
    }
    base.update(overrides)
    return base


def _event(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": EVENT_ID,
        "run_id": RUN_ID,
        "ts": "2026-09-12T12:00:00+00:00",
        "kind": "tool_result",
        "step_index": 0,
        "actor": "agent",
        "evidence_ref": EVIDENCE_REF,
        "evidence_refs": ["gate:retrieval@abcdef1"],
        "provenance": {"source_sha": SOURCE_SHA, "retrieval": _projection()},
    }
    base.update(overrides)
    return base


def test_valid_projection_is_preserved_without_raw_result() -> None:
    raw_result = [{"body": "private document"}]
    digest = result_digest(raw_result)
    raw = _projection(
        qmd_result=raw_result,
        result_digest=digest,
        receipt_id=projection_receipt_id(
            source_sha=SOURCE_SHA,
            run_id=RUN_ID,
            qmd_uri=QMD_URI,
            evidence_ref=EVIDENCE_REF,
            result_digest=digest,
        ),
    )
    ok, reasons, normalized = normalize_retrieval_projection(raw)

    assert ok
    assert reasons == []
    assert normalized is not None
    assert normalized["result_digest"] == result_digest([{"body": "private document"}])
    assert "qmd_result" not in normalized
    assert "private document" not in json.dumps(normalized)


def test_raw_result_without_supplied_digest_uses_computed_digest() -> None:
    raw_result = {"answer": "computed"}
    raw = _projection(qmd_result=raw_result)
    raw.pop("result_digest")
    raw.pop("receipt_id")
    digest = result_digest(raw_result)
    raw["receipt_id"] = projection_receipt_id(
        source_sha=SOURCE_SHA,
        run_id=RUN_ID,
        qmd_uri=QMD_URI,
        evidence_ref=EVIDENCE_REF,
        result_digest=digest,
    )
    ok, reasons, normalized = normalize_retrieval_projection(raw)
    assert ok, reasons
    assert normalized is not None
    assert normalized["result_digest"] == digest


def test_event_normalization_keeps_gate_refs_separate() -> None:
    ok, reasons, normalized = validate_event(_event())

    assert ok, reasons
    assert normalized is not None
    assert normalized["evidence_refs"] == ["gate:retrieval@abcdef1"]
    assert normalized["provenance"]["retrieval"]["evidence_ref"] == EVIDENCE_REF


def test_legacy_raw_carrier_fails_closed() -> None:
    ok, reasons, normalized = validate_event(
        {**_event(), "retrieval_receipt": {"qmd_result": "raw"}}
    )

    assert not ok
    assert reasons == ["unsupported_field:retrieval_receipt"]
    assert normalized is None


def test_correlation_and_digest_mismatches_fail_closed() -> None:
    for field, value, expected in (
        ("run_id", "other-run", "mismatch:provenance.retrieval.run_id"),
        ("source_sha", "b" * 40, "mismatch:provenance.retrieval.source_sha"),
        ("evidence_ref", "other-evidence", "mismatch:provenance.retrieval.evidence_ref"),
        ("result_digest", "0" * 64, "digest_mismatch:provenance.retrieval.result_digest"),
    ):
        raw = _projection(qmd_result={"answer": 1}, **{field: value})
        ok, reasons, _ = normalize_retrieval_projection(
            raw,
            event_run_id=RUN_ID,
            event_source_sha=SOURCE_SHA,
            event_evidence_ref=EVIDENCE_REF,
        )
        assert not ok
        assert expected in reasons


def test_missing_receipt_id_and_metadata_bounds_fail_closed() -> None:
    missing = _projection()
    missing.pop("receipt_id")
    ok, reasons, _ = normalize_retrieval_projection(missing)
    assert not ok
    assert "missing_field:provenance.retrieval.receipt_id" in reasons

    too_many = _projection(result_metadata={f"key-{i}": i for i in range(9)})
    ok, reasons, _ = normalize_retrieval_projection(too_many)
    assert not ok
    assert "metadata_bound:key_count" in reasons
    assert any(reason.startswith("unsupported_metadata_key:") for reason in reasons)

    nested = _projection(result_metadata={"collection": {"name": "private"}})
    ok, reasons, _ = normalize_retrieval_projection(nested)
    assert not ok
    assert "metadata_bound:nested:collection" in reasons


def test_qmd_uri_normalization_rejects_query_and_fragment_leakage() -> None:
    assert normalize_qmd_uri("qmd:////knowledge/guide.md") == "qmd://knowledge/guide.md"
    assert normalize_qmd_uri("qmd://knowledge/guide.md?token=private") is None
    assert normalize_qmd_uri("qmd://knowledge/guide.md#private") is None

    for value in (
        "qmd://knowledge/guide.md?token=private",
        "qmd://knowledge/guide.md#private",
    ):
        ok, reasons, _ = normalize_retrieval_projection(_projection(qmd_uri=value))
        assert not ok
        assert "invalid_field:provenance.retrieval.qmd_uri" in reasons


def test_metadata_secret_shaped_values_fail_closed() -> None:
    ok, reasons, _ = normalize_retrieval_projection(
        _projection(result_metadata={"collection": "knowledge?token=private"})
    )
    assert not ok
    assert "unsupported_metadata_value:collection" in reasons


def test_normalize_ledger_readback_identity_and_idempotency(tmp_path: Path) -> None:
    ok, reasons, normalized = validate_event(_event())
    assert ok, reasons
    assert normalized is not None
    assert append_agent_event(tmp_path, normalized)
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert events == [normalized]

    assert check_event_id(tmp_path, normalized) == EVENT_ID_DUPLICATE
    conflict = {
        **normalized,
        "provenance": {"source_sha": SOURCE_SHA, "retrieval": _projection(receipt_id="f" * 64)},
    }
    assert check_event_id(tmp_path, conflict) == EVENT_ID_CONFLICT

    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    assert "private document" not in ledger.read_text(encoding="utf-8")


def test_canonical_json_is_recursive_and_utf8_deterministic() -> None:
    assert (
        canonical_json({"b": {"z": 1, "a": "café"}, "a": [2, 1]})
        == '{"a":[2,1],"b":{"a":"café","z":1}}'
    )
