"""CliRunner tests for HyoDo ``score --partial`` functionality.

Tests the --partial flag that allows missing pillars to default to 0.5 (neutral),
and verifies that SIGNAL_CONFIDENCE_WEAK is emitted only when pillars are filled.

For uniform pillar inputs the review signal reduces to ``value == v * 100``:
each pillar scales ``v -> 1 + 9v`` on the 1-10 scale, the geometric mean of
five equal values equals that value, so ``F = 6x`` and
``value = ((6x - 6) / 54) * 100 = 100 * v``. That lets us target bands exactly:
0.95 -> STRONG, 0.80 -> CAUTION, 0.30 -> BLOCK.

Assertions are keyword-based (not exact full-text matches) so they stay
resilient to Rich rendering and minor copy changes.
"""

from __future__ import annotations

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _uniform_score_args(value: float, *, short: bool = True) -> list[str]:
    """Build ``score`` args setting all five primary pillars to *value*."""
    if short:
        flags = ["-i", "-t", "-g", "-c", "-b"]
    else:
        flags = [
            "--benevolence",
            "--truth",
            "--goodness",
            "--hyo",
            "--beauty",
        ]
    args = ["score"]
    for flag in flags:
        args += [flag, str(value)]
    return args


# --------------------------------------------------------------------------- #
# score --partial - missing pillars default to 0.5
# --------------------------------------------------------------------------- #


def test_score_partial_two_pillars_exit_0():
    """Partial with two pillars must exit 0, show Partial mode, Missing, WEAK."""
    result = runner.invoke(app, ["score", "-t", "0.9", "-g", "0.9", "--partial"])
    assert result.exit_code == 0
    assert "Partial mode" in result.output or "partial" in result.output.lower()
    assert "SIGNAL_CONFIDENCE_WEAK" in result.output
    assert "Missing:" in result.output


def test_score_partial_band_label_preserved():
    """Partial mode preserves REVIEW_SIGNAL_* label (STRONG/CAUTION/BLOCK)."""
    result = runner.invoke(app, ["score", "-t", "0.9", "-g", "0.9", "--partial"])
    assert result.exit_code == 0
    # Normalize newlines for robust assertions across Rich rendering
    output_normalized = result.output.replace("\n", "")
    # Must have one of STRONG/CAUTION/BLOCK
    has_band = any(
        band in output_normalized
        for band in ["REVIEW_SIGNAL_STRONG", "REVIEW_SIGNAL_CAUTION", "REVIEW_SIGNAL_BLOCK"]
    )
    assert has_band, "Expected REVIEW_SIGNAL_* band label"
    # But must NOT have REVIEW_SIGNAL_WEAK (weak is confidence, not band)
    assert "REVIEW_SIGNAL_WEAK" not in output_normalized


def test_score_partial_all_pillars_0_8_caution_no_weak():
    """Full pillars (0.8) with partial: CAUTION, no SIGNAL_CONFIDENCE_WEAK."""
    result = runner.invoke(app, [*_uniform_score_args(0.8), "--partial"])
    assert result.exit_code == 0
    output_normalized = result.output.replace("\n", "")
    assert "CAUTION" in output_normalized
    assert "SIGNAL_CONFIDENCE_WEAK" not in output_normalized


def test_score_partial_all_pillars_0_3_block_no_weak():
    """Full pillars (0.3) with partial: BLOCK, no SIGNAL_CONFIDENCE_WEAK."""
    result = runner.invoke(app, [*_uniform_score_args(0.3), "--partial"])
    assert result.exit_code == 0
    output_normalized = result.output.replace("\n", "")
    assert "BLOCK" in output_normalized
    assert "SIGNAL_CONFIDENCE_WEAK" not in output_normalized


# --------------------------------------------------------------------------- #
# score (no partial) - missing pillars must error
# --------------------------------------------------------------------------- #


def test_score_missing_pillars_no_partial_exit_2():
    """Missing pillars without --partial: exit 2, --partial hint, no TOTAL."""
    result = runner.invoke(app, ["score", "-t", "0.9", "-g", "0.8"])
    assert result.exit_code == 2
    assert "--partial" in result.output
    assert "TOTAL" not in result.output


# --------------------------------------------------------------------------- #
# score --partial with zero pillars - all default to 0.5
# --------------------------------------------------------------------------- #


def test_score_partial_no_pillars_defaults_to_0_5():
    """Partial with no pillars: all default to 0.5, score ~50, BLOCK + WEAK."""
    result = runner.invoke(app, ["score", "--partial"])
    assert result.exit_code == 0
    output_normalized = result.output.replace("\n", "")
    assert "BLOCK" in output_normalized
    assert "SIGNAL_CONFIDENCE_WEAK" in output_normalized


# --------------------------------------------------------------------------- #
# score --partial - legacy conflict detection still applies
# --------------------------------------------------------------------------- #


def test_score_partial_legacy_conflict_hyo_eternity_exit_2():
    """Partial with both --hyo and --eternity (conflict) must exit 2."""
    result = runner.invoke(
        app,
        [
            "score",
            "--partial",
            "-c",
            "0.9",
            "--eternity",
            "0.8",
            "-t",
            "0.9",
            "-g",
            "0.9",
            "-b",
            "0.9",
            "-i",
            "0.9",
        ],
    )
    assert result.exit_code == 2
    assert "onflict" in result.output.lower()
