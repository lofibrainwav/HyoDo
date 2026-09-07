"""Tests for the anti-gaming AST visitor in hyodo.safe."""

from pathlib import Path

from hyodo.safe.anti_gaming import scan_test_file_ast


def test_detects_empty_test_body(tmp_path: Path) -> None:
    test_file = tmp_path / "test_empty.py"
    test_file.write_text(
        'def test_nothing():\n    """Just a docstring."""\n    pass\n', encoding="utf-8"
    )

    findings = scan_test_file_ast(test_file)
    assert any(f.rule_id == "HYO-SAFE-010" for f in findings)


def test_detects_tautological_assert_true(tmp_path: Path) -> None:
    test_file = tmp_path / "test_fake.py"
    test_file.write_text("def test_dummy():\n    assert True\n", encoding="utf-8")

    findings = scan_test_file_ast(test_file)
    assert any(f.rule_id == "HYO-SAFE-011" for f in findings)


def test_detects_literal_comparison(tmp_path: Path) -> None:
    test_file = tmp_path / "test_cmp.py"
    test_file.write_text("def test_dummy():\n    assert 1 == 1\n", encoding="utf-8")

    findings = scan_test_file_ast(test_file)
    assert any(f.rule_id == "HYO-SAFE-012" for f in findings)


def test_allows_valid_assertions(tmp_path: Path) -> None:
    test_file = tmp_path / "test_valid.py"
    test_file.write_text(
        "def test_real():\n    result = 1 + 1\n    assert result == 2\n", encoding="utf-8"
    )

    findings = scan_test_file_ast(test_file)
    assert len(findings) == 0
