"""Evidence stays in HyoDo; scores, weights, and aggregates stay with the host.

`hyodo/score_derive.py` is the one place HyoDo still weighs evidence into a
number, kept only for the legacy `hyodo score --from-check` path. It is frozen:
a new importer is a new consumer of a judgment layer HyoDo does not own.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).parents[1] / "hyodo"

# The only modules allowed to import the legacy score derivation.
LEGACY_SCORE_IMPORTERS = {"cli/main.py"}


def _imports_score_derive(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "hyodo.score_derive":
                return True
            names = {alias.name for alias in node.names}
            if node.module == "hyodo" and "score_derive" in names:
                return True
        elif isinstance(node, ast.Import) and any(
            alias.name == "hyodo.score_derive" for alias in node.names
        ):
            return True
    return False


def test_score_derive_has_no_new_consumers() -> None:
    importers = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*.py")
        if path.name != "score_derive.py" and _imports_score_derive(path)
    }
    assert importers == LEGACY_SCORE_IMPORTERS
