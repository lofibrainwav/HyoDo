"""Static guard tests for the evidence-first orchestration hook."""

from scripts.check_orchestration_contract import main


def test_orchestration_contract_is_current() -> None:
    assert main() == 0
