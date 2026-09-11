"""The claim-lock table is copied by hand into several documents.

`README.md` is the source. The same block appears in the research notes and on
the site, and nothing checked that the copies agreed -- so a status could be
corrected in one place and stay wrong in three others. That is the drift
`check_roadmap_sync` exists to stop, one table over.

The copies are discovered rather than listed: a new copy is covered the day it
is added, without anyone remembering to register it here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HEADER = "| Capability | Status | Evidence boundary |"


def tracked_markdown() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / name for name in listing.stdout.split("\0") if name]


def claim_table(text: str) -> list[str] | None:
    """The table block starting at HEADER, or None when the file has none."""
    lines = text.splitlines()
    try:
        start = lines.index(HEADER)
    except ValueError:
        return None
    block = [HEADER]
    for line in lines[start + 1 :]:
        if not line.startswith("|"):
            break
        block.append(line)
    return block


def test_every_copy_of_the_claim_table_matches_the_readme() -> None:
    source = claim_table((REPO_ROOT / "README.md").read_text(encoding="utf-8"))
    assert source is not None, "README.md no longer carries the claim-lock table"

    mismatched: list[str] = []
    for path in tracked_markdown():
        if path.name == "README.md" and path.parent == REPO_ROOT:
            continue
        copy = claim_table(path.read_text(encoding="utf-8"))
        if copy is not None and copy != source:
            rel = path.relative_to(REPO_ROOT)
            extra = set(copy) - set(source)
            missing = set(source) - set(copy)
            mismatched.append(f"{rel}: +{sorted(extra)} -{sorted(missing)}")

    assert not mismatched, "claim table copies disagree with README.md:\n" + "\n".join(mismatched)


def test_the_table_is_found_by_its_header_not_its_position() -> None:
    text = "intro\n\n" + HEADER + "\n| --- | --- | --- |\n| a | B | c. |\n\nafter\n"
    assert claim_table(text) == [HEADER, "| --- | --- | --- |", "| a | B | c. |"]
    assert claim_table("no table here\n") is None
