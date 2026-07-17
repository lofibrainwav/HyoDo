"""Unit tests for public HyoDo safety scan helpers."""

from hyodo.safety import risk_score, run_safety_scan, scan_text


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


def test_run_safety_scan_missing_path_source(tmp_path):
    result = run_safety_scan(path=str(tmp_path / "missing.txt"), cwd=tmp_path)
    assert result["source"].startswith("missing:")
