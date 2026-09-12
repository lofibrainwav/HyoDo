from __future__ import annotations

from hyodo.ifa import IFA_SCHEMA, attest_information_flow


def flow(
    flow_id: str,
    source: str,
    target: str,
    *,
    sensitivity: str = "confidential",
    transformation: str = "copy",
    sink: str = "local_process",
    declassification: dict[str, str] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "schema": IFA_SCHEMA,
        "flow_id": flow_id,
        "run_id": "r1",
        "source_event_id": source,
        "target_event_id": target,
        "sensitivity": sensitivity,
        "transformation": transformation,
        "sink_class": sink,
    }
    if declassification is not None:
        row["declassification"] = declassification
    return row


def test_linear_sensitive_flow_is_observed_without_authority() -> None:
    receipt = attest_information_flow(
        [flow("f1", "A", "B")],
        event_ids={"A", "B"},
    )
    assert receipt["status"] == "OBSERVED"
    assert receipt["authority_decision"] is None
    assert receipt["flows"][0]["effective_sensitivity"] == "confidential"


def test_redact_does_not_declassify_without_explicit_provenance() -> None:
    receipt = attest_information_flow(
        [flow("f1", "A", "B", transformation="redact")],
        event_ids={"A", "B"},
    )
    observed = receipt["flows"][0]
    assert observed["declassification_observed"] is False
    assert observed["effective_sensitivity"] == "confidential"


def test_explicit_declassification_requires_evaluator_and_evidence() -> None:
    receipt = attest_information_flow(
        [
            flow(
                "f1",
                "A",
                "B",
                transformation="redact",
                declassification={
                    "evaluated_by": "privacy-evaluator/v1",
                    "evidence_ref": "gate:privacy@abcdef1",
                    "output_label": "public",
                },
            )
        ],
        event_ids={"A", "B"},
    )
    observed = receipt["flows"][0]
    assert observed["declassification_observed"] is True
    assert observed["effective_sensitivity"] == "public"


def test_claimed_declassification_without_provenance_is_unobserved() -> None:
    receipt = attest_information_flow(
        [
            flow(
                "f1",
                "A",
                "B",
                transformation="redact",
                declassification={"output_label": "public"},
            )
        ],
        event_ids={"A", "B"},
    )
    observed = receipt["flows"][0]
    assert observed["declassification_unobserved"] is True
    assert observed["effective_sensitivity"] == "confidential"


def test_missing_lineage_endpoint_keeps_receipt_unobserved() -> None:
    receipt = attest_information_flow(
        [flow("f1", "A", "MISSING")],
        event_ids={"A"},
    )
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["unresolved"] == [{"flow_id": "f1", "event_id": "MISSING"}]


def test_sensitive_external_sink_is_risk_evidence_not_deny() -> None:
    receipt = attest_information_flow(
        [flow("f1", "A", "B", sink="external_network")],
        event_ids={"A", "B"},
    )
    assert receipt["risks"] == [{"flow_id": "f1", "reason": "sensitive_external_sink_observed"}]
    assert receipt["authority_decision"] is None


def test_unknown_external_sink_sensitivity_stays_unknown() -> None:
    receipt = attest_information_flow(
        [flow("f1", "A", "B", sensitivity="unknown", sink="external_network")],
        event_ids={"A", "B"},
    )
    assert receipt["risks"] == [{"flow_id": "f1", "reason": "external_sink_sensitivity_unobserved"}]
    assert receipt["authority_decision"] is None


def test_diamond_flows_remain_separate_observations() -> None:
    receipt = attest_information_flow(
        [
            flow("f2", "A", "J", transformation="summarize"),
            flow("f1", "B", "J", sensitivity="internal", transformation="aggregate"),
        ],
        event_ids={"A", "B", "J"},
    )
    assert [item["flow_id"] for item in receipt["flows"]] == ["f1", "f2"]
    assert receipt["status"] == "OBSERVED"


def test_invalid_observation_is_not_silently_dropped() -> None:
    bad = flow("f1", "A", "B")
    bad["transformation"] = "magic"
    receipt = attest_information_flow([bad], event_ids={"A", "B"})
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["invalid"] == [{"flow_id": "f1", "reasons": ["invalid_transformation"]}]
