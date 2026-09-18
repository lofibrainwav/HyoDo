from hyodo.compute_supply_observation import (
    SCHEMA_VERSION,
    build_observation_receipt,
    validate_observation_receipt,
)


def test_observation_receipt_has_three_layers_and_no_routing() -> None:
    receipt = build_observation_receipt(
        catalog={"provider": "observed", "models": ["observed"]},
        user_availability={"state": "OBSERVED"},
        live_access={"access": "FREE_OK"},
    )
    assert receipt["schema_version"] == SCHEMA_VERSION
    assert set(receipt) == {
        "schema_version", "observed_at", "fresh_until", "evidence_source",
        "catalog", "user_availability", "live_access",
    }
    assert validate_observation_receipt(receipt) == (True, [])


def test_credentials_and_content_are_not_recorded() -> None:
    receipt = build_observation_receipt(
        live_access={"api_key": "secret", "prompt": "private", "quota": "UNOBSERVED"}
    )
    assert receipt["live_access"] == {"api_key": "REDACTED", "quota": "UNOBSERVED"}


def test_missing_layer_is_unobserved_by_validation() -> None:
    ok, reasons = validate_observation_receipt({"schema_version": SCHEMA_VERSION})
    assert not ok
    assert "missing:catalog" in reasons
