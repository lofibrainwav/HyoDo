"""Write test ledgers through HyoDo's own anchored writer.

A ledger file written byte-for-byte by a test is exactly what a hostile clone
ships: HyoDo never wrote it, so its origin is UNVERIFIED and it cannot make a
report or continuity receipt READY. Fixtures that stand for a ledger HyoDo
recorded locally must therefore be produced by the production append path.
"""

from __future__ import annotations

from pathlib import Path

from hyodo.ledger_origin import anchored_append


def write_ledger(path: Path, text: str) -> None:
    """Replace the ledger at *path* with *text*, appended line by line by HyoDo."""
    root = path.parent.parent
    relative = path.relative_to(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    for line in text.splitlines(keepends=True):
        anchored_append(root, relative, line)
