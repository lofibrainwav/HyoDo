"""CliRunner tests for HyoDo CLI commands.

Covers the commands that were previously untested in ``hyodo/cli/main.py``:
``score`` (across its review-signal bands, primary flags, and legacy aliases),
``start``, ``trinity``, ``version``, the ``--version`` callback, and the
no-subcommand help path.

Assertions are keyword-based (not exact full-text matches) so they stay
resilient to Rich rendering and minor copy changes.

For uniform pillar inputs the review signal reduces to ``value == v * 100``:
each pillar scales ``v -> 1 + 9v`` on the 1-10 scale, the geometric mean of
five equal values equals that value, so ``F = 6x`` and
``value = ((6x - 6) / 54) * 100 = 100 * v``. That lets us target bands exactly:
0.95 -> STRONG, 0.80 -> CAUTION, 0.30 -> BLOCK.
"""

from __future__ import annotations

from typer.testing import CliRunner

from hyodo import __version__
from hyodo.cli.main import app
from hyodo.dashboard import render_dashboard_html

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
# score - review signal bands
# --------------------------------------------------------------------------- #


def test_score_missing_pillars_exit_2():
    """No options / partial options must not invent 1.0 defaults (false STRONG)."""
    bare = runner.invoke(app, ["score"])
    assert bare.exit_code == 2
    assert "required" in bare.output.lower() or "Missing" in bare.output

    partial = runner.invoke(app, ["score", "-t", "0.9", "-g", "0.8"])
    assert partial.exit_code == 2
    assert "REVIEW_SIGNAL_STRONG" not in partial.output
    assert "TOTAL" not in partial.output


def test_score_high_long_flags_strong_band():
    """High inputs via primary long flags land in the STRONG band."""
    result = runner.invoke(app, _uniform_score_args(0.95, short=False))
    assert result.exit_code == 0
    assert "STRONG" in result.output


def test_score_mid_short_flags_caution_band():
    """Mid inputs via primary short flags land in the CAUTION band."""
    result = runner.invoke(app, _uniform_score_args(0.80, short=True))
    assert result.exit_code == 0
    assert "CAUTION" in result.output


def test_score_low_short_flags_block_band():
    """Low inputs via primary short flags land in the BLOCK band."""
    result = runner.invoke(app, _uniform_score_args(0.30, short=True))
    assert result.exit_code == 0
    assert "BLOCK" in result.output


def test_score_legacy_serenity_eternity_aliases_block_band():
    """Legacy aliases (-s serenity, -e eternity) may fill benevolence/hyo.

    Primary and legacy for the same pillar cannot be combined; this path uses
    legacy only for those two pillars.
    """
    result = runner.invoke(
        app,
        ["score", "-s", "0.30", "-e", "0.30", "-t", "0.30", "-g", "0.30", "-b", "0.30"],
    )
    assert result.exit_code == 0
    assert "BLOCK" in result.output


def test_score_conflict_hyo_and_eternity_exit_2():
    """Primary --hyo and legacy --eternity together must fail, not silently override."""
    result = runner.invoke(
        app,
        [
            "score",
            "-t",
            "0.9",
            "-g",
            "0.9",
            "-b",
            "0.9",
            "-i",
            "0.9",
            "--hyo",
            "0.2",
            "--eternity",
            "0.9",
        ],
    )
    assert result.exit_code == 2
    assert "Conflict" in result.output or "conflict" in result.output.lower()


def test_score_conflict_benevolence_and_serenity_exit_2():
    result = runner.invoke(
        app,
        [
            "score",
            "-t",
            "0.9",
            "-g",
            "0.9",
            "-b",
            "0.9",
            "-c",
            "0.9",
            "--benevolence",
            "0.2",
            "--serenity",
            "0.9",
        ],
    )
    assert result.exit_code == 2
    assert "Conflict" in result.output or "conflict" in result.output.lower()


def test_score_output_mentions_review_signal():
    """Output identifies itself as a review signal, not an auto-approval."""
    result = runner.invoke(app, _uniform_score_args(0.95, short=False))
    assert result.exit_code == 0
    assert "Review Signal" in result.output or "REVIEW_SIGNAL" in result.output
    assert "V6" in result.output or "philosophy" in result.output.lower()


def test_dashboard_html_uses_raw_evidence_and_never_invents_ux_score():
    evidence = {
        "target": "/tmp/HyoDo",
        "measured_at": "2026-07-20T00:00:00+00:00",
        "gates": {
            "typecheck": {"status": "PASS", "message": "0 errors"},
            "lint_format": {"status": "PASS", "message": "passed"},
            "tests": {"status": "PASS", "message": "==== 173 passed, 1 skipped in 0.61s ===="},
            "sbom": {"status": "PASS", "message": "generated"},
        },
        "safety": {"risk_score": 5, "findings": []},
    }
    html = render_dashboard_html(evidence)
    assert "Raw evidence only" in html
    assert "173 passed, 1 skipped in 0.61s" in html
    assert "==== 173 passed" not in html
    assert "GateStatus.PASS" not in html
    assert html.count("Not measured") == 3
    assert "composite score" in html
    assert "inventory artifact" in html


# --------------------------------------------------------------------------- #
# start / trinity - guide text
# --------------------------------------------------------------------------- #


def test_start_shows_onboarding_keywords():
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0
    assert "quick start" in result.output.lower()
    assert "score" in result.output.lower()
    # Onboarding must not teach the false-STRONG partial example.
    assert "-t 0.9 -g 0.8" not in result.output.replace("\n", " ")


def test_trinity_shows_checklist_keywords():
    result = runner.invoke(app, ["trinity", "add a new feature"])
    assert result.exit_code == 0
    assert "Trinity" in result.output
    assert "Checklist" in result.output


# --------------------------------------------------------------------------- #
# version
# --------------------------------------------------------------------------- #


def test_version_subcommand():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "HyoDo" in result.output
    assert __version__ in result.output


def test_version_flag_callback():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "HyoDo" in result.output
    assert __version__ in result.output


# --------------------------------------------------------------------------- #
# no-subcommand - help / guidance path
# --------------------------------------------------------------------------- #


def test_no_subcommand_shows_help():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    # Typer prints usage/help without crashing and lists available commands.
    assert "Usage" in result.output
    assert "score" in result.output
