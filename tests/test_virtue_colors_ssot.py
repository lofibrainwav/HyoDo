"""The six virtue colours have one source of truth, checked from both ends.

`hyodo/dashboard.py` has always owned the canonical hex values (its
`PILLAR_SPECS` order and inline CSS block). The core engine monitor design
(`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`)
adds a second consumer: `site/src/styles/tokens.css`. This test parses both
files and asserts the hex values match, by name and in the same fixed
column order, so the two never drift apart silently.

Each virtue carries two hexes, not one. The accents are rendered as text
(`h2 span`, `.reference`, `.grid-colhead h2 span`), and no single colour
clears WCAG AA against both a near-white card and a near-black one. The
contrast tests below parse the card surfaces out of the same file rather
than hard-coding them, so changing a surface colour re-runs the check and
fails CI if a virtue stops clearing 4.5:1.
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
TOKEN_RE = re.compile(
    r"--color-virtue-(?P<slug>[a-z]+):\s*light-dark\(\s*"
    r"(?P<light>#[0-9a-fA-F]{6})\s*,\s*(?P<dark>#[0-9a-fA-F]{6})\s*\)\s*;"
)
# The card the accent text sits on, read from the same stylesheet rather than
# restated here: a surface change must re-run the contrast check, not bypass it.
SURFACE_RE = re.compile(r"--surface:\s*(?P<hex>#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\s*;")
DARK_MEDIA = "prefers-color-scheme: dark"
AA_TEXT = 4.5


def _rgb(value: str) -> tuple[float, float, float]:
    raw = value.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return tuple(int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _relative_luminance(value: str) -> float:
    def channel(component: float) -> float:
        if component <= 0.03928:
            return component / 12.92
        return ((component + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(c) for c in _rgb(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.x contrast ratio. Public so the negative fixture can reuse it."""
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _dashboard_surfaces() -> tuple[list[str], list[str]]:
    """Every card surface the accents are drawn on, split light/dark.

    Both rendered pages (the dashboard and the evidence-graph viewer) declare
    their own `:root` plus a dark media query, so this returns a list per
    theme, not a single colour.
    """
    light: list[str] = []
    dark: list[str] = []
    for line in DASHBOARD_PATH.read_text(encoding="utf-8").splitlines():
        for match in SURFACE_RE.finditer(line):
            (dark if DARK_MEDIA in line else light).append(match.group("hex"))
    return light, dark


def _dashboard_key_to_hex() -> dict[str, str]:
    text = DASHBOARD_PATH.read_text(encoding="utf-8")

    specs_match = re.search(r"PILLAR_SPECS.*?=\s*\((.*?)\n\)", text, re.DOTALL)
    assert specs_match, "PILLAR_SPECS tuple not found in hyodo/dashboard.py"
    key_to_color = {
        entry.group("key"): entry.group("color")
        for entry in PILLAR_SPEC_ENTRY_RE.finditer(specs_match.group(1))
    }
    assert key_to_color, "no PILLAR_SPECS entries parsed"

    color_to_hex = _dashboard_color_to_pair(text)
    return {key: color_to_hex[color] for key, color in key_to_color.items()}


def _dashboard_color_to_pair(text: str) -> dict[str, tuple[str, str]]:
    """colour name -> (light hex, dark hex), asserting every CSS block agrees.

    Light and dark rules are told apart by the same signal the browser uses:
    whether the declaration sits inside a `prefers-color-scheme: dark` media
    query. The card surfaces are switched by that same query, so accent and
    surface always flip together. Driving one of them from `light-dark()`
    instead was measured in the browser rendering a dark accent on the light
    card at 2.89:1 — two mechanisms, two signals, one false green.

    The rules are emitted once per rendered page, so a name appearing with two
    different pairs means one page was edited and the other was not.
    """
    light: dict[str, str] = {}
    dark: dict[str, str] = {}
    for line in text.splitlines():
        target = dark if DARK_MEDIA in line else light
        for match in DASHBOARD_ACCENT_RE.finditer(line):
            name, value = match.group("name"), match.group("hex")
            if name in target:
                assert target[name] == value, (
                    f".{name} is declared as {target[name]} in one CSS block and {value} "
                    "in another; every rendered page must use the same accent"
                )
            target[name] = value

    assert light, "no light-theme .accent-class { --accent:#hex } rules parsed"
    assert dark, (
        "no dark-theme accent rules parsed; every virtue needs an override inside "
        "the prefers-color-scheme: dark media query, or the dark card is unchecked"
    )
    assert set(light) == set(dark), (
        f"light and dark accent rules cover different virtues: {sorted(set(light) ^ set(dark))}"
    )
    return {name: (light[name], dark[name]) for name in light}


def _tokens_slug_to_hex() -> dict[str, str]:
    text = TOKENS_PATH.read_text(encoding="utf-8")
    return {m.group("slug"): (m.group("light"), m.group("dark")) for m in TOKEN_RE.finditer(text)}


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
    literal `.name {{ --accent:L; --accent:light-dark(L,D) }}` CSS block this file's other tests
    already parse from `hyodo/dashboard.py`'s source text (the render_graph_html
    graph viewer looks values up by name from that dict rather than
    re-parsing CSS). Nothing catches the two drifting apart without this
    assertion — see the judge report's colour-SSOT-gap finding.
    """
    from hyodo.dashboard import _VIRTUE_ACCENT_HEX

    text = DASHBOARD_PATH.read_text(encoding="utf-8")
    css_hex = _dashboard_color_to_pair(text)
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


def test_every_virtue_accent_clears_aa_on_every_text_surface():
    """The product gate: 6 virtues x every card surface, as text, >= 4.5:1.

    The accents are not decoration. `h2 span`, `.reference` and
    `.grid-colhead h2 span` all render them as text, so each one has to clear
    WCAG AA against the card it is printed on. The surfaces come from
    `_dashboard_surfaces()`, which parses them out of `hyodo/dashboard.py`:
    changing a card colour therefore re-runs this computation instead of
    quietly invalidating a number written down here.
    """
    light_surfaces, dark_surfaces = _dashboard_surfaces()
    assert len(light_surfaces) >= 2, (
        f"expected a light --surface for both rendered pages; parser found {light_surfaces}"
    )
    assert len(dark_surfaces) >= 2, (
        f"expected a dark --surface for both rendered pages; parser found {dark_surfaces}"
    )
    assert len(light_surfaces) == len(dark_surfaces), (
        "every light surface needs a dark counterpart, otherwise one theme is "
        f"unchecked: light={light_surfaces} dark={dark_surfaces}"
    )

    accents = _dashboard_color_to_pair(DASHBOARD_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for name, (light_hex, dark_hex) in sorted(accents.items()):
        for surface in light_surfaces:
            ratio = contrast_ratio(light_hex, surface)
            if ratio < AA_TEXT:
                failures.append(f"{name} light {light_hex} on {surface}: {ratio:.2f}")
        for surface in dark_surfaces:
            ratio = contrast_ratio(dark_hex, surface)
            if ratio < AA_TEXT:
                failures.append(f"{name} dark {dark_hex} on {surface}: {ratio:.2f}")

    assert not failures, "virtue accents below WCAG AA (4.5:1) as text:\n  " + "\n  ".join(failures)


def test_a_single_hex_cannot_serve_both_surfaces():
    """The pair is load-bearing, so nobody can "simplify" it back to one value.

    For each virtue this asserts the light value actually fails on the dark
    card (and vice versa). If a future palette ever had one hex that cleared
    both, this test would fail and force a deliberate decision rather than a
    silent collapse back to a single colour.
    """
    light_surfaces, dark_surfaces = _dashboard_surfaces()
    accents = _dashboard_color_to_pair(DASHBOARD_PATH.read_text(encoding="utf-8"))

    for name, (light_hex, dark_hex) in sorted(accents.items()):
        if light_hex == dark_hex:
            pytest.fail(f"{name} uses one hex for both themes; see this test's docstring")
        worst_light_on_dark = min(contrast_ratio(light_hex, s) for s in dark_surfaces)
        worst_dark_on_light = min(contrast_ratio(dark_hex, s) for s in light_surfaces)
        assert worst_light_on_dark < AA_TEXT or worst_dark_on_light < AA_TEXT, (
            f"{name}: both {light_hex} and {dark_hex} clear AA on both themes, so the "
            "light-dark() split is no longer load-bearing — collapse it deliberately "
            "or document why the pair stays"
        )


def test_the_contrast_check_fails_when_a_surface_regresses():
    """Negative fixture: prove the oracle has teeth.

    A contrast test that can only pass is not a gate. This feeds the real
    accents a deliberately bad surface — a mid grey no accent can clear — and
    asserts the same computation reports failures. If someone neuters
    `contrast_ratio`, this fails before the real check goes quietly green.
    """
    accents = _dashboard_color_to_pair(DASHBOARD_PATH.read_text(encoding="utf-8"))
    regressed_surface = "#767676"

    failures = [
        name
        for name, (light_hex, dark_hex) in accents.items()
        if contrast_ratio(light_hex, regressed_surface) < AA_TEXT
        or contrast_ratio(dark_hex, regressed_surface) < AA_TEXT
    ]
    assert len(failures) == len(accents), (
        "every virtue should fail against a mid-grey surface; the contrast "
        f"computation only flagged {sorted(failures)}"
    )


def test_contrast_ratio_matches_known_wcag_values():
    """Anchor the maths itself, so the gate cannot drift with the palette."""
    assert round(contrast_ratio("#000000", "#ffffff"), 2) == 21.0
    assert round(contrast_ratio("#ffffff", "#ffffff"), 2) == 1.0
    # three-digit hex must expand, since one card surface is written as #fff
    assert contrast_ratio("#000", "#fff") == contrast_ratio("#000000", "#ffffff")


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
