"""The six virtue colours have one source of truth, checked from both ends.

`hyodo/dashboard.py` has always owned the canonical hex values (its
`PILLAR_SPECS` order and inline CSS block). The core engine monitor design
(`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`)
adds a second consumer: `site/src/styles/tokens.css`. This test parses both
files and asserts the hex values match, by name and in the same fixed
column order, so the two never drift apart silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = REPO_ROOT / "hyodo" / "dashboard.py"
TOKENS_PATH = REPO_ROOT / "site" / "src" / "styles" / "tokens.css"

# PILLAR_SPECS key -> the CSS custom property slug used in tokens.css.
# Fixed order: Truth, Goodness, Beauty, Benevolence, Hyo, Eternity.
KEY_TO_SLUG: tuple[tuple[str, str], ...] = (
    ("jin", "truth"),
    ("seon", "goodness"),
    ("mi", "beauty"),
    ("in", "benevolence"),
    ("hyo", "hyo"),
    ("yeong", "eternity"),
)

PILLAR_SPEC_ENTRY_RE = re.compile(
    r'\(\s*"(?P<key>\w+)"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"(?P<color>\w+)"\s*\)'
)
DASHBOARD_ACCENT_RE = re.compile(
    r"\.(?P<name>\w+)\s*\{\{\s*--accent:(?P<hex>#[0-9a-fA-F]{6})\s*\}\}"
)
TOKEN_RE = re.compile(r"--color-virtue-(?P<slug>[a-z]+):\s*(?P<hex>#[0-9a-fA-F]{6})\s*;")


def _dashboard_key_to_hex() -> dict[str, str]:
    text = DASHBOARD_PATH.read_text(encoding="utf-8")

    specs_match = re.search(r"PILLAR_SPECS.*?=\s*\((.*?)\n\)", text, re.DOTALL)
    assert specs_match, "PILLAR_SPECS tuple not found in hyodo/dashboard.py"
    key_to_color = {
        entry.group("key"): entry.group("color")
        for entry in PILLAR_SPEC_ENTRY_RE.finditer(specs_match.group(1))
    }
    assert key_to_color, "no PILLAR_SPECS entries parsed"

    color_to_hex = {m.group("name"): m.group("hex") for m in DASHBOARD_ACCENT_RE.finditer(text)}
    assert color_to_hex, "no .accent-class { --accent:#hex } rules parsed from dashboard.py"

    return {key: color_to_hex[color] for key, color in key_to_color.items()}


def _tokens_slug_to_hex() -> dict[str, str]:
    text = TOKENS_PATH.read_text(encoding="utf-8")
    return {m.group("slug"): m.group("hex") for m in TOKEN_RE.finditer(text)}


def test_virtue_hex_values_match_dashboard_ssot():
    if not TOKENS_PATH.exists():
        pytest.skip("site/ is absent (sdist install) — nothing to compare")

    dashboard_hex = _dashboard_key_to_hex()
    tokens_hex = _tokens_slug_to_hex()

    assert tokens_hex, "no --color-virtue-* custom properties found in tokens.css"

    for key, slug in KEY_TO_SLUG:
        assert key in dashboard_hex, f"PILLAR_SPECS is missing key {key!r}"
        assert slug in tokens_hex, f"tokens.css is missing --color-virtue-{slug}"
        assert tokens_hex[slug] == dashboard_hex[key], (
            f"--color-virtue-{slug} ({tokens_hex[slug]}) does not match "
            f"hyodo/dashboard.py's {key} colour ({dashboard_hex[key]})"
        )


def test_virtue_accent_hex_dict_matches_the_dashboard_css_block():
    """`hyodo.dashboard._VIRTUE_ACCENT_HEX` is a hand-kept second copy of the
    literal `.name {{ --accent:#hex }}` CSS block this file's other tests
    already parse from `hyodo/dashboard.py`'s source text (the render_graph_html
    graph viewer looks values up by name from that dict rather than
    re-parsing CSS). Nothing catches the two drifting apart without this
    assertion — see the judge report's colour-SSOT-gap finding.
    """
    from hyodo.dashboard import _VIRTUE_ACCENT_HEX

    text = DASHBOARD_PATH.read_text(encoding="utf-8")
    css_hex = {m.group("name"): m.group("hex") for m in DASHBOARD_ACCENT_RE.finditer(text)}
    assert css_hex, "no .accent-class { --accent:#hex } rules parsed from dashboard.py"
    assert css_hex == _VIRTUE_ACCENT_HEX


def test_virtue_tokens_appear_in_fixed_column_order():
    if not TOKENS_PATH.exists():
        pytest.skip("site/ is absent (sdist install) — nothing to compare")

    text = TOKENS_PATH.read_text(encoding="utf-8")
    positions = [text.index(f"--color-virtue-{slug}:") for _, slug in KEY_TO_SLUG]
    assert positions == sorted(positions), (
        "tokens.css virtue tokens must appear in the fixed order Truth, "
        "Goodness, Beauty, Benevolence, Hyo, Eternity"
    )


# Package 2-C, Ruling 5: the four actor-ring layer colours
# (`hyodo.dashboard.RING_COLORS`) are guarded the same way as the six
# virtue colours above — `site/src/styles/tokens.css`'s `--color-ring-*`
# custom properties are the SSOT this test parses both ends against.
RING_TOKEN_RE = re.compile(r"--color-ring-(?P<slug>[a-z]+):\s*(?P<hex>#[0-9a-fA-F]{6})\s*;")


def _tokens_ring_slug_to_hex() -> dict[str, str]:
    text = TOKENS_PATH.read_text(encoding="utf-8")
    return {m.group("slug"): m.group("hex") for m in RING_TOKEN_RE.finditer(text)}


def test_ring_colors_match_tokens_css_ssot():
    if not TOKENS_PATH.exists():
        pytest.skip("site/ is absent (sdist install) — nothing to compare")

    from hyodo.dashboard import RING_COLORS

    tokens_hex = _tokens_ring_slug_to_hex()
    assert tokens_hex, "no --color-ring-* custom properties found in tokens.css"
    for layer, hex_value in RING_COLORS.items():
        assert layer in tokens_hex, f"tokens.css is missing --color-ring-{layer}"
        assert tokens_hex[layer] == hex_value, (
            f"hyodo.dashboard.RING_COLORS[{layer!r}] ({hex_value}) does not match "
            f"tokens.css's --color-ring-{layer} ({tokens_hex[layer]})"
        )
