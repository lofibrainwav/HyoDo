"""Directory cap omissions must remain explicit, including late listing errors."""

from unittest.mock import patch

from hyodo.safety import collect_scan_corpus, run_safety_scan


def test_capped_corpus_is_not_complete(tmp_path):
    for n in range(41):
        (tmp_path / f"{n:03}.txt").write_text("safe\n" if n < 40 else "git push --force\n")
    coverage = {}
    corpus, source = collect_scan_corpus(str(tmp_path), coverage=coverage)
    assert source.startswith("error:partial:"), source
    assert "git push" not in corpus
    assert coverage["scanned"] == 40
    assert coverage["omitted"] == 1
    result = run_safety_scan(str(tmp_path), max_files=40)
    assert result["coverage"] == "PARTIAL"
    full = run_safety_scan(str(tmp_path), max_files=41)
    assert full["coverage"] == "FULL"
    assert any(f.severity == "high" for f in full["findings"])


def test_unlistable_subtree_after_cap_is_observed(tmp_path):
    for n in range(40):
        (tmp_path / f"{n:03}.txt").write_text("safe\n")
    blocked = tmp_path / "z-blocked"
    blocked.mkdir()
    import os

    original = os.scandir

    def scandir(path):
        if str(path) == str(blocked):
            raise PermissionError("synthetic denied")
        return original(path)

    with patch("hyodo.safety.os.scandir", side_effect=scandir):
        corpus, source = collect_scan_corpus(str(tmp_path))
    assert source == f"error:read:{blocked}"
    assert corpus == ""


def test_empty_corpus_and_external_link_are_not_source_observations(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run_safety_scan(str(empty))["coverage"] == "UNOBSERVED"
    outside = tmp_path / "outside.txt"
    outside.write_text("do not read\n")
    (empty / "link.txt").symlink_to(outside)
    corpus, _source = collect_scan_corpus(str(empty))
    assert "do not read" not in corpus
    assert run_safety_scan(str(empty))["coverage"] != "FULL"


def test_oversize_text_is_unobserved_not_full(tmp_path):
    file = tmp_path / "large.txt"
    file.write_text("#" * 200_001 + "git push --force\n")
    for target in (file, tmp_path):
        result = run_safety_scan(str(target), max_files=0)
        assert result["coverage"] == "UNOBSERVED"
        assert result["source"].startswith("error:read:")
        corpus, source = collect_scan_corpus(str(target))
        assert corpus == ""
        assert source.startswith("error:read:")


def test_symlink_loop_after_cap_is_structured_unobserved(tmp_path):
    for n in range(40):
        (tmp_path / f"{n:03}.txt").write_text("safe\n")
    loop = tmp_path / "z-loop"
    loop.symlink_to(loop)
    corpus, source = collect_scan_corpus(str(tmp_path))
    assert corpus == ""
    assert source == f"error:read:{loop}"


def test_entry_metadata_failure_after_cap_is_structured_unobserved(tmp_path):
    import os

    for n in range(40):
        (tmp_path / f"{n:03}.txt").write_text("safe\n")
    broken = tmp_path / "z-broken"
    broken.write_text("safe\n")
    original = os.scandir

    class BrokenEntry:
        name = "z-broken"
        path = str(broken)

        def is_symlink(self):
            raise OSError("synthetic metadata failure")

    class Entries:
        def __enter__(self):
            self.entries = original(tmp_path)
            return iter([e for e in self.entries if e.name != "z-broken"] + [BrokenEntry()])

        def __exit__(self, *args):
            self.entries.close()

    with patch("hyodo.safety.os.scandir", return_value=Entries()):
        corpus, source = collect_scan_corpus(str(tmp_path))
    assert corpus == ""
    assert source == f"error:read:{broken}"
