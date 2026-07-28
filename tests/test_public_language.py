"""This repository is public, so its tracked text is English.

`CLAUDE.md` has said "Public language: English only" for a long time, but nothing
checked it. Agents arriving from Korean-first repositories kept adding Korean
comments and docstrings, and a second doc even told them it was fine. A rule that
nothing verifies is not a rule — it is a comment about one.

The single deliberate exception is the six virtue labels, which ship as
hanja/Hangul/English together because the trilingual form *is* the label. Only
those six syllables are allowed, and only as labels — never as prose.

This file writes every Hangul character as an escape rather than a literal, so it
holds itself to the rule it enforces. That is not cosmetic: the first version
used literals, passed locally while it was still untracked, and failed in CI the
moment it was committed — the scanner had flagged itself. Escapes are the honest
fix. Excluding this file from its own scan would have been self-concealment.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

HANGUL = re.compile("[\uac00-\ud7a3]")  # the modern Hangul syllable block

# The trilingual virtue labels: Truth, Goodness, Beauty, Benevolence,
# Filial Piety, Eternity — each shipped as hanja/Hangul/English together.
ALLOWED_SYLLABLES = frozenset("\uc9c4\uc120\ubbf8\uc778\ud6a8\uc601")

SCANNED_SUFFIXES = (".py", ".md")


def _tracked_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "*.py", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / name for name in listing.stdout.split("\0") if name]


def _offending_lines(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Unreadable is not clean. Surface it rather than counting it as a pass.
        return [(0, f"<could not read {path}>")]
    offences = []
    for number, line in enumerate(text.splitlines(), start=1):
        found = set(HANGUL.findall(line))
        if found - ALLOWED_SYLLABLES:
            offences.append((number, line.strip()))
    return offences


def test_tracked_text_is_english_apart_from_the_virtue_labels():
    files = _tracked_files()
    assert files, "git ls-files returned nothing — the scan would pass vacuously"

    scanned = 0
    offences = []
    for path in files:
        if path.suffix not in SCANNED_SUFFIXES:
            continue
        scanned += 1
        for number, line in _offending_lines(path):
            offences.append(f"{path.relative_to(REPO_ROOT)}:{number}: {line[:100]}")

    assert scanned > 10, f"only {scanned} files scanned — the glob likely broke"
    assert not offences, (
        "This repository is public and its tracked text is English "
        "(CLAUDE.md, 'Public language: English only'). Korean is allowed only as "
        "the six trilingual virtue syllables, and only as labels.\n  " + "\n  ".join(offences)
    )


def test_this_file_is_itself_scanned():
    # The gate must not be exempt from the rule it enforces. If this file ever
    # drops out of the tracked set, the check above silently stops covering it.
    tracked = {path.name for path in _tracked_files()}
    assert Path(__file__).name in tracked


def test_the_scan_would_actually_catch_korean_prose(tmp_path):
    # Guard the guard: if the pattern ever stops matching, the test above would
    # pass on a repository full of Korean and nobody would know.
    prose = "# \uc774 \uc904\uc740 \ud55c\uae00 \uc0b0\ubb38\uc774\ub2e4\n"
    sample = tmp_path / "sample.py"
    sample.write_text(prose, encoding="utf-8")
    assert _offending_lines(sample), "the scanner no longer detects Korean prose"

    label = tmp_path / "label.py"
    label.write_text('PILLARS = ("jin", "\u771e", "\uc9c4", "Truth")\n', encoding="utf-8")
    assert not _offending_lines(label), "the virtue-label exception regressed"
