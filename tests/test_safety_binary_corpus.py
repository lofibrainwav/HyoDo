"""Binary and cache artifacts must not enter the safety scan corpus.

Reported 2026-07-22: `hyodo safe` on the HyoDo checkout returned
risk_score 15 / "caution" from two findings, both false. The first pointed at
`.coverage` — a SQLite database written by coverage.py. Because that filename
has no suffix it slipped past the extension blocklist, `_read_text_file`
decoded it with errors="replace", and the literal `CREATE TABLE` strings
inside the SQLite page data matched the schema_change pattern.

Only 5 of the 40 scanned files were real sources; 35 were `.hypothesis`
cache entries. Noise like that inflates risk_score and trains people to
ignore the scanner — which is how a real leak gets missed.

Note on what is deliberately NOT done: the scanner must NOT start honouring
.gitignore. `.gitignore` lists real `.env` files, and skipping ignored paths
would remove exactly the files most likely to hold live credentials. The
corpus is narrowed by *content* (binary sniffing) and by *build-cache
directory names*, never by "git does not track it".
"""

from pathlib import Path

from hyodo.safety import collect_scan_corpus, run_safety_scan

SQLITE_HEADER = b"SQLite format 3\x00"
# Real coverage.py databases carry their schema DDL as literal text.
SQLITE_BODY = SQLITE_HEADER + b"\x00\x01" + b"CREATE TABLE tracer (id integer)" + b"\x00" * 64


def test_extensionless_binary_is_not_scanned(tmp_path):
    """.coverage is SQLite: no suffix, but NUL bytes make it binary."""
    (tmp_path / ".coverage").write_bytes(SQLITE_BODY)
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    corpus, source = collect_scan_corpus(str(tmp_path))
    assert "CREATE TABLE" not in corpus
    assert "hello" in corpus, "real source must still be scanned"
    assert "(1 files)" in source, f"expected only app.py to be scanned, got {source}"


def test_binary_does_not_produce_findings(tmp_path):
    """The end-to-end verdict must not be raised by a binary artifact."""
    (tmp_path / ".coverage").write_bytes(SQLITE_BODY)
    (tmp_path / "readme.md").write_text("# docs\n", encoding="utf-8")

    result = run_safety_scan(path=str(tmp_path), cwd=tmp_path)
    labels = [f.label for f in result["findings"]]
    assert "schema_change" not in labels, f"binary decoded as source: {labels}"


def test_build_cache_directories_are_skipped(tmp_path):
    """Cache entries crowd real sources out of the file cap."""
    for name in (".hypothesis", ".pytest_cache", "__pycache__", "node_modules"):
        cache = tmp_path / name / "sub"
        cache.mkdir(parents=True)
        (cache / "entry.txt").write_text("ALTER TABLE users ADD COLUMN x\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hi')\n", encoding="utf-8")

    corpus, source = collect_scan_corpus(str(tmp_path))
    assert "ALTER TABLE" not in corpus
    assert "(1 files)" in source, f"cache leaked into corpus: {source}"


def test_gitignored_secrets_are_still_scanned(tmp_path):
    """Guard against 'fix' by .gitignore — untracked files hide real secrets.

    A .env is the single most likely place for a live credential and is
    almost always gitignored. Narrowing the corpus by git status would blind
    the scanner exactly where it matters most.
    """
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text(f"AWS_ACCESS_KEY_ID=AKIA{'Q' * 16}\n", encoding="utf-8")

    result = run_safety_scan(path=str(tmp_path), cwd=tmp_path)
    labels = [f.label for f in result["findings"]]
    assert any("secret" in label or "aws" in label.lower() for label in labels), (
        f"gitignored secret was not detected: {labels}"
    )


def test_text_sources_are_unaffected(tmp_path):
    """No regression: ordinary text files keep being scanned."""
    (tmp_path / "schema.sql").write_text("ALTER TABLE users ADD COLUMN email text;\n", "utf-8")

    corpus, _ = collect_scan_corpus(str(tmp_path))
    assert "ALTER TABLE" in corpus, "real schema change must still be visible"


def test_real_hyodo_checkout_has_clean_corpus():
    """The reported case: scanning HyoDo itself must not flag .coverage."""
    root = Path(__file__).resolve().parents[1]
    result = run_safety_scan(path=str(root), cwd=root)
    offenders = [f for f in result["findings"] if f.path and ".coverage" in f.path]
    assert not offenders, f".coverage still produces findings: {offenders}"
