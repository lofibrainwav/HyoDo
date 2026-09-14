from __future__ import annotations

from pathlib import Path

from scripts.check_hyodo_boundary import FORBIDDEN


def test_hyodo_package_has_no_legacy_runtime_references() -> None:
    root = Path(__file__).parents[1] / "hyodo"
    matches = [
        f"{path}:{line_number}"
        for path in sorted(root.rglob("*.py"))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if FORBIDDEN.search(line)
    ]
    assert matches == []
