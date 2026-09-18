from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "demo-dry-run.sh"


def test_demo_dry_run_declares_its_side_effect_contract() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'echo "run_kind: demo-verification-run"' in text
    assert 'echo "zero_write: false"' in text
    assert 'echo "local_side_effects: true"' in text
    assert 'echo "receipt_write: true"' in text
    assert 'echo "release_mutation: false"' in text
