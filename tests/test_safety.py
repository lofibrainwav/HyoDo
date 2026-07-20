"""Unit tests for public HyoDo safety scan helpers."""

from unittest.mock import patch

from hyodo.safety import collect_scan_corpus, risk_score, run_safety_scan, scan_text


def test_scan_detects_github_token():
    text = "token = ghp_abcdefghijklmnopqrstuvwxyz012345"
    findings = scan_text(text)
    assert any(f.category == "secret" and f.label == "github_token" for f in findings)


def test_scan_detects_drop_database():
    findings = scan_text("please DROP DATABASE production;")
    assert any(f.category == "dangerous_command" and f.label == "drop_database" for f in findings)


def test_risk_score_high_when_secret_present():
    findings = scan_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")
    assert risk_score(findings) >= 40


def test_empty_corpus_is_info_not_false_green():
    findings = scan_text("")
    assert findings
    assert findings[0].category == "corpus"
    assert findings[0].severity == "info"


def test_run_safety_scan_on_inline_file(tmp_path):
    sample = tmp_path / "snippet.txt"
    sample.write_text("kubectl apply -f deploy.yaml\n", encoding="utf-8")
    result = run_safety_scan(path=str(sample), strict=True, cwd=tmp_path)
    assert result["risk_score"] >= 15
    assert result["level"] in {"caution", "high"}
    assert "file:" in result["source"]
    prod = [f for f in result["findings"] if f.category == "production_impact"]
    assert prod
    assert prod[0].path == str(sample)
    assert prod[0].line == 1


def test_scan_text_attaches_path_and_line():
    text = "line1\ntoken = ghp_abcdefghijklmnopqrstuvwxyz012345\n"
    findings = scan_text(text, path="/tmp/demo.py")
    secret = next(f for f in findings if f.label == "github_token")
    assert secret.path == "/tmp/demo.py"
    assert secret.line == 2


def test_run_safety_scan_missing_path_source(tmp_path):
    result = run_safety_scan(path=str(tmp_path / "missing.txt"), cwd=tmp_path)
    assert result["source"].startswith("missing:")


def test_collect_scan_corpus_read_error_not_silent(tmp_path):
    """OSError while reading must yield error:read: source, not empty-corpus success."""
    sample = tmp_path / "locked.txt"
    sample.write_text("hello\n", encoding="utf-8")
    with patch("hyodo.safety._read_text_file", side_effect=OSError("Permission denied")):
        corpus, source = collect_scan_corpus(path=str(sample), cwd=tmp_path)
    assert corpus == ""
    assert source.startswith("error:read:")
    assert str(sample) in source


def test_run_safety_scan_read_error_source(tmp_path):
    sample = tmp_path / "locked.txt"
    sample.write_text("hello\n", encoding="utf-8")
    with patch("hyodo.safety._read_text_file", side_effect=PermissionError("denied")):
        result = run_safety_scan(path=str(sample), strict=True, cwd=tmp_path)
    assert result["source"].startswith("error:read:")
