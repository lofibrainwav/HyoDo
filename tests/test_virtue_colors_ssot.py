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
# Each virtue accent is a light-dark() pair: one hex cannot clear WCAG AA
# against both the light and the dark surface. See _VIRTUE_ACCENT_HEX.
_PAIR = r"light-dark\(\s*(?P<light>#[0-9a-fA-F]{6})\s*,\s*(?P<dark>#[0-9a-fA-F]{6})\s*\)"
DASHBOARD_ACCENT_RE = re.compile(r"\.(?P<name>\w+)\s*\{\{\s*--accent:" + _PAIR + r"\s*\}\}")
TOKEN_RE = re.compile(r"--color-virtue-(?P<slug>[a-z]+):\s*" + _PAIR + r"\s*;")
SURFACE_RE = re.compile(r"--surface:\s*(?P<hex>#[0-9a-fA-F]{3,6})\s*;")
DARK_BLOCK_RE = re.compile(r"prefers-color-scheme:\s*dark")

# WCAG 2.2 SC 1.4.3, normal text. The accent is used as text (the hanja label
# and the reference line), so the 3:1 large-text allowance does not apply.
AA_NORMAL_TEXT = 4.5


def _dashboard_key_to_hex() -> dict[str, tuple[str, str]]:
    text = DASHBOARD_PATH.read_text(encoding="utf-8")

    specs_match = re.search(r"PILLAR_SPECS.*?=\s*\((.*?)\n\)", text, re.DOTALL)
    assert specs_match, "PILLAR_SPECS tuple not found in hyodo/dashboard.py"
    key_to_color = {
        entry.group("key"): entry.group("color")
        for entry in PILLAR_SPEC_ENTRY_RE.finditer(specs_match.group(1))
    }
    assert key_to_color, "no PILLAR_SPECS entries parsed"

    color_to_hex = {
        m.group("name"): (m.group("light"), m.group("dark"))
        for m in DASHBOARD_ACCENT_RE.finditer(text)
    }
    assert color_to_hex, "no .accent-class { --accent:light-dark(...) } rules parsed"

    return {key: color_to_hex[color] for key, color in key_to_color.items()}


def _tokens_slug_to_hex() -> dict[str, tuple[str, str]]:
    text = TOKENS_PATH.read_text(encoding="utf-8")
    return {m.group("slug"): (m.group("light"), m.group("dark")) for m in TOKEN_RE.finditer(text)}


def _relative_luminance(hex_value: str) -> float:
    """WCAG relative luminance for a #rgb or #rrggbb value."""
    digits = hex_value.lstrip("#")
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    channels = []
    for offset in (0, 2, 4):
        channel = int(digits[offset : offset + 2], 16) / 255
        channels.append(
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground: str, background: str) -> float:
    first, second = _relative_luminance(foreground), _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _dashboard_surfaces() -> tuple[str, str]:
    """The light and dark `--surface` values the accents are read against."""
    text = DASHBOARD_PATH.read_text(encoding="utf-8")
    dark_at = DARK_BLOCK_RE.search(text)
    assert dark_at, "no prefers-color-scheme: dark block found in hyodo/dashboard.py"

    light = SURFACE_RE.search(text, 0, dark_at.start())
    assert light, "could not read the light --surface value from hyodo/dashboard.py"
    dark = SURFACE_RE.search(text, dark_at.end())
    assert dark, "could not read the dark --surface value from hyodo/dashboard.py"
    return light.group("hex"), dark.group("hex")


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
    css_hex = {
        m.group("name"): (m.group("light"), m.group("dark"))
        for m in DASHBOARD_ACCENT_RE.finditer(text)
    }
    assert css_hex, "no .accent-class { --accent:light-dark(...) } rules parsed"
    assert css_hex == _VIRTUE_ACCENT_HEX


def test_every_virtue_accent_clears_wcag_aa_on_its_own_surface():
    """A muted or re-derived palette must not buy looks with legibility.

    This is the guard the colours themselves cannot provide: it reads the two
    `--surface` values straight out of the stylesheet, so changing a surface
    re-runs the check on every accent instead of silently invalidating it.
    """
    from hyodo.dashboard import _VIRTUE_ACCENT_HEX

    light_surface, dark_surface = _dashboard_surfaces()
    failures = []
    for name, (light, dark) in _VIRTUE_ACCENT_HEX.items():
        for label, accent, surface in (
            ("light", light, light_surface),
            ("dark", dark, dark_surface),
        ):
            ratio = _contrast_ratio(accent, surface)
            if ratio < AA_NORMAL_TEXT:
                failures.append(f"{name} {label}: {accent} on {surface} is {ratio:.2f}:1")

    assert not failures, "accents below WCAG AA (4.5:1): " + "; ".join(failures)


def test_no_single_hex_could_serve_both_surfaces():
    """Documents why the accents are pairs rather than one value each.

    Clearing 4.5:1 against the light surface caps an accent's relative
    luminance; clearing it against the dark surface floors it. If those two
    windows ever overlap again -- because a surface moved -- the pair split is
    no longer forced and this test says so.
    """
    light_surface, dark_surface = _dashboard_surfaces()
    ceiling = (_relative_luminance(light_surface) + 0.05) / AA_NORMAL_TEXT - 0.05
    floor = AA_NORMAL_TEXT * (_relative_luminance(dark_surface) + 0.05) - 0.05

    assert ceiling < floor, (
        f"a single accent hex with relative luminance in [{floor:.4f}, {ceiling:.4f}] "
        "would now clear AA on both surfaces; the light-dark() pairs can be collapsed"
    )


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


# Local viewer second pass (brief finding 2): the SVG edge overlay's three
# line-kind colours (`hyodo.dashboard.EDGE_COLORS`) are guarded the same
# way as the ring colours above.
EDGE_TOKEN_RE = re.compile(r"--color-edge-(?P<slug>[a-z]+):\s*(?P<hex>#[0-9a-fA-F]{6})\s*;")


def _tokens_edge_slug_to_hex() -> dict[str, str]:
    text = TOKENS_PATH.read_text(encoding="utf-8")
    return {m.group("slug"): m.group("hex") for m in EDGE_TOKEN_RE.finditer(text)}


def test_edge_colors_match_tokens_css_ssot():
    if not TOKENS_PATH.exists():
        pytest.skip("site/ is absent (sdist install) — nothing to compare")

    from hyodo.dashboard import EDGE_COLORS

    tokens_hex = _tokens_edge_slug_to_hex()
    assert tokens_hex, "no --color-edge-* custom properties found in tokens.css"
    for kind, hex_value in EDGE_COLORS.items():
        assert kind in tokens_hex, f"tokens.css is missing --color-edge-{kind}"
        assert tokens_hex[kind] == hex_value, (
            f"hyodo.dashboard.EDGE_COLORS[{kind!r}] ({hex_value}) does not match "
            f"tokens.css's --color-edge-{kind} ({tokens_hex[kind]})"
        )
