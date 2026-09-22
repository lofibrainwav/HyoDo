"""This repository is public, so its tracked text is English.

`CLAUDE.md` has said "Public language: English only" for a long time, but nothing
checked it. Agents arriving from Korean-first repositories kept adding Korean
comments and docstrings, and a second doc even told them it was fine. A rule that
nothing verifies is not a rule — it is a comment about one.

The single deliberate exception is the six virtue labels, which ship as
hanja/Hangul/English together because the trilingual form *is* the label. Only
those six syllables are allowed, and only as labels — never as prose. "As a
label" is enforced, not assumed: a virtue syllable passes only when its own
canonical hanja and one of its English names sit within a few characters of it.
An earlier version allowed the six syllables anywhere, so a sentence could use
them as bare Korean words and still pass; the policy said one thing and the
gate checked a weaker one.

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

# The trilingual virtue labels. Each Hangul syllable is allowed only next to its
# own canonical hanja and one of the English names the public surfaces use for
# it (hyodo/virtues.py, docs/VIRTUE_CONTRACT.md, the dashboard short labels).
VIRTUE_LABELS: dict[str, tuple[str, tuple[str, ...]]] = {
    "\uc9c4": ("\u771e", ("Truth",)),
    "\uc120": ("\u5584", ("Goodness", "Good")),
    "\ubbf8": ("\u7f8e", ("Beauty",)),
    "\uc778": ("\u4ec1", ("Benevolence", "Humanity")),
    "\ud6a8": ("\u5b5d", ("Hyo", "Filial Piety", "filialPiety")),
    "\uc601": ("\u6c38", ("Eternity", "Yeong", "Longevity")),
}
ALLOWED_SYLLABLES = frozenset(VIRTUE_LABELS)

# How far (in characters, either side) the hanja and English may sit from the
# syllable. Wide enough for a table cell or a multi-line tuple such as
# ("truth", "Truth", "<syllable>", "<hanja>"); narrow enough that a sentence
# cannot borrow a label from elsewhere in the paragraph.
LABEL_WINDOW = 40

SCANNED_SUFFIXES = (".py", ".md")

ACTIVE_ATTRIBUTION_FILES = (
    Path("pyproject.toml"),
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".github/actions/hyodo/action.yml"),
)


def _tracked_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "*.py", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / name for name in listing.stdout.split("\0") if name]


def _is_label(text: str, index: int) -> bool:
    hanja, names = VIRTUE_LABELS[text[index]]
    window = text[max(0, index - LABEL_WINDOW) : index + LABEL_WINDOW + 1]
    if hanja not in window:
        return False
    return any(
        re.search(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", window, re.I) for name in names
    )


def _offending_lines(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Unreadable is not clean. Surface it rather than counting it as a pass.
        return [(0, f"<could not read {path}>")]
    lines = text.splitlines(keepends=True)
    offences = []
    offset = 0
    for number, line in enumerate(lines, start=1):
        for match in HANGUL.finditer(line):
            char = match.group()
            if char in ALLOWED_SYLLABLES and _is_label(text, offset + match.start()):
                continue
            offences.append((number, line.strip()))
            break
        offset += len(line)
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
        "the six virtue syllables, and only beside their own hanja and English name.\n  "
        + "\n  ".join(offences)
    )


def test_this_file_is_itself_scanned():
    # The gate must not be exempt from the rule it enforces. If this file ever
    # drops out of the tracked set, the check above silently stops covering it.
    tracked = {path.name for path in _tracked_files()}
    assert Path(__file__).name in tracked


def test_legacy_attribution_stays_out_of_active_surfaces():
    for relative_path in ACTIVE_ATTRIBUTION_FILES:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "AFO Kingdom" not in text, relative_path


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


def _flags(tmp_path: Path, text: str) -> bool:
    sample = tmp_path / "sample.md"
    sample.write_text(text, encoding="utf-8")
    return bool(_offending_lines(sample))


def test_a_virtue_syllable_used_as_a_word_is_prose(tmp_path):
    # The loophole this gate closes: the six syllables used as bare Korean
    # nouns inside an English sentence used to pass.
    hyo, yeong = "\ud6a8", "\uc601"
    assert _flags(tmp_path, f"describe {hyo} as alignment, and {yeong} as record\n")
    # English name alone, hanja alone, or another virtue's hanja is not a label.
    assert _flags(tmp_path, "- \uc9c4 \u2014 `truth`\n")
    assert _flags(tmp_path, "\uc9c4(\u771e) \u2014 measured claims\n")
    assert _flags(tmp_path, "Truth \u5584 \uc9c4\n")
    # A label elsewhere in the paragraph cannot be borrowed by a later sentence.
    far = "Truth / \u771e / \uc9c4.\n" + "x" * (LABEL_WINDOW + 5) + " then \uc9c4 again\n"
    assert _flags(tmp_path, far)


def test_real_virtue_labels_still_pass(tmp_path):
    # Table cell, inline label, and the multi-line tuple shape of hyodo/virtues.py.
    assert not _flags(tmp_path, "| Hyo | \ud6a8 / \u5b5d | Consent |\n")
    assert not _flags(tmp_path, "FAIL pytest (\u5584 \uc120 Good): no module\n")
    tuple_shape = '(\n    "truth",\n    "Truth",\n    "\uc9c4",\n    "\u771e",\n)\n'
    assert not _flags(tmp_path, tuple_shape)
