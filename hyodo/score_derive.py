"""Derive HyoDo Integrity Score pillar inputs from HyoDo's own observations.

``hyodo score`` takes the five pillar values as CLI floats supplied by the
caller. This module adds a deterministic, documented derivation of those
same five values from what ``hyodo check``, ``hyodo safe``, and the
test-integrity scan already observe about a checkout — with per-pillar
provenance so a reader can see exactly which rule produced which number.

Design constraints (see docs/SCORE_DERIVATION.md):

* The HyoDo Integrity Score formula itself (``calculate_hygook_v5_score``)
  is not changed. This module only proposes the five inputs to it.
* Every rule that contributes to a pillar has a stable ``rule_id`` that is
  a key in :data:`PILLAR_RULE_TABLE`. The table is the single source of
  truth for which pillar a rule feeds and how much it can contribute.
* A pillar with no observed rules is ``UNOBSERVED`` and its value is
  ``None`` — never a smuggled 0 or 100. A pillar with some but not all of
  its rules observed is ``PARTIAL`` and its value is rescaled over the
  rules that *were* observed. A pillar with every rule observed is
  ``OBSERVED``.
* This stays a review signal, not an approval — see ``hyodo score --help``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Coverage = Literal["OBSERVED", "PARTIAL", "UNOBSERVED"]
PILLAR_NAMES = ("benevolence", "truth", "goodness", "hyo", "beauty")


@dataclass(frozen=True)
class RuleSpec:
    """One row of :data:`PILLAR_RULE_TABLE`: what a rule feeds and how much."""

    pillar: str
    max_weight: float  # points out of 100 this rule can contribute when fully observed
    description: str


# Rule-id -> pillar weight table. This is the SSOT for the derivation; every
# rule_id a `PillarResult.provenance` entry can carry must be a key here.
# Mirrored in docs/SCORE_DERIVATION.md — keep both in sync when editing.
PILLAR_RULE_TABLE: dict[str, RuleSpec] = {
    # Truth <- test-integrity (observed/expected assertion ratio) + hyodo
    # check's own Truth gate (pyright).
    "test_integrity.observed_ratio": RuleSpec(
        "truth", 70.0, "Fraction of tests that assert something observable"
    ),
    "check.truth_gate": RuleSpec("truth", 30.0, "hyodo check Truth gate (pyright) status"),
    # Goodness <- hyodo safe findings (severity-weighted) + scan coverage.
    "safe.high_findings": RuleSpec("goodness", 50.0, "Penalty for high-severity safe findings"),
    "safe.medium_findings": RuleSpec("goodness", 30.0, "Penalty for medium-severity safe findings"),
    "safe.coverage": RuleSpec("goodness", 20.0, "Fraction of scannable files safe covered"),
    # Beauty <- hyodo check's Beauty gate (ruff lint + format).
    "check.beauty_gate": RuleSpec("beauty", 100.0, "hyodo check Beauty gate (ruff) status"),
    # Benevolence <- onboarding/DX signals hyodo check would emit. hyodo
    # check does not currently emit README/start-hint/help-text signals, so
    # this pillar reports UNOBSERVED until it does (see docs).
    "check.readme_present": RuleSpec("benevolence", 40.0, "README.md present at project root"),
    "check.start_hint_present": RuleSpec(
        "benevolence", 30.0, "Onboarding entry point (hyodo start) documented"
    ),
    "check.help_text_present": RuleSpec(
        "benevolence", 30.0, "CLI help text present for the primary commands"
    ),
    # Hyo <- project/context alignment signals: BYOG config, a connected
    # host, and an access ledger recording MCP activity.
    "hyo.config_present": RuleSpec("hyo", 34.0, ".hyodo/gates.toml (Bring-Your-Own-Gates) present"),
    "hyo.connect_wired": RuleSpec("hyo", 33.0, "At least one host wired via hyodo connect"),
    "hyo.ledger_present": RuleSpec("hyo", 33.0, ".hyodo/mcp-access.jsonl ledger present"),
}


def _validate_table() -> None:
    for rule_id, spec in PILLAR_RULE_TABLE.items():
        if spec.pillar not in PILLAR_NAMES:
            raise ValueError(
                f"PILLAR_RULE_TABLE[{rule_id!r}] targets unknown pillar {spec.pillar!r}"
            )


_validate_table()


@dataclass(frozen=True)
class ProvenanceRow:
    """One rule's contribution to a pillar's derived value."""

    rule_id: str
    source: str  # "check" | "safe" | "test_integrity" | "cli-flag"
    weight: float
    contribution: float
    override: bool = False

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dict for this provenance row."""
        payload: dict[str, object] = {
            "rule_id": self.rule_id,
            "source": self.source,
            "weight": self.weight,
            "contribution": self.contribution,
        }
        if self.override:
            payload["override"] = True
        return payload


@dataclass(frozen=True)
class PillarResult:
    """A derived pillar value (0-100), its coverage, and full provenance."""

    pillar: str
    value: float | None  # 0-100, or None when UNOBSERVED
    coverage: Coverage
    provenance: tuple[ProvenanceRow, ...] = field(default_factory=tuple)
    override: bool = False

    def top_provenance(self, n: int = 3) -> tuple[ProvenanceRow, ...]:
        """Return the *n* provenance rows with the largest absolute contribution."""
        return tuple(sorted(self.provenance, key=lambda r: abs(r.contribution), reverse=True)[:n])

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dict for this pillar result."""
        return {
            "pillar": self.pillar,
            "value": self.value,
            "coverage": self.coverage,
            "override": self.override,
            "provenance": [row.as_dict() for row in self.provenance],
        }

    def unit_value(self) -> float | None:
        """Value scaled to 0-1 for feeding into calculate_hygook_v5_score, or None."""
        return None if self.value is None else self.value / 100.0


@dataclass(frozen=True)
class DerivedPillars:
    """The five derived pillar results, keyed by pillar name."""

    benevolence: PillarResult
    truth: PillarResult
    goodness: PillarResult
    hyo: PillarResult
    beauty: PillarResult

    def by_name(self) -> dict[str, PillarResult]:
        """Return the five pillar results keyed by pillar name."""
        return {
            "benevolence": self.benevolence,
            "truth": self.truth,
            "goodness": self.goodness,
            "hyo": self.hyo,
            "beauty": self.beauty,
        }

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dict of all five pillar results."""
        return {name: result.as_dict() for name, result in self.by_name().items()}


def _rule(rule_id: str) -> RuleSpec:
    return PILLAR_RULE_TABLE[rule_id]


def _make_pillar(
    pillar: str, observed_rows: list[ProvenanceRow], rule_ids: tuple[str, ...]
) -> PillarResult:
    """Roll a set of (possibly partial) observed rows up into a PillarResult.

    *rule_ids* is the full set of rules that exist for this pillar (used to
    decide OBSERVED vs PARTIAL vs UNOBSERVED); *observed_rows* holds only the
    rows that were actually computed.
    """
    if not observed_rows:
        return PillarResult(pillar=pillar, value=None, coverage="UNOBSERVED", provenance=())

    observed_ids = {row.rule_id for row in observed_rows}
    coverage: Coverage = "OBSERVED" if observed_ids >= set(rule_ids) else "PARTIAL"
    max_observed_weight = sum(row.weight for row in observed_rows)
    if max_observed_weight <= 0:
        value = 0.0
    else:
        value = max(
            0.0,
            min(
                100.0, sum(row.contribution for row in observed_rows) / max_observed_weight * 100.0
            ),
        )
    return PillarResult(
        pillar=pillar, value=value, coverage=coverage, provenance=tuple(observed_rows)
    )


def _derive_truth(test_integrity: dict | None, check: dict | None) -> PillarResult:
    rule_ids = ("test_integrity.observed_ratio", "check.truth_gate")
    rows: list[ProvenanceRow] = []

    if test_integrity is not None:
        total = test_integrity.get("total_tests")
        vacuous = test_integrity.get("vacuous_tests")
        if isinstance(total, int) and isinstance(vacuous, int) and total > 0:
            spec = _rule("test_integrity.observed_ratio")
            ratio = max(0.0, min(1.0, (total - vacuous) / total))
            rows.append(
                ProvenanceRow(
                    "test_integrity.observed_ratio",
                    "test_integrity",
                    spec.max_weight,
                    spec.max_weight * ratio,
                )
            )
        # total_tests == 0 (no tests found) is left unobserved rather than
        # scored as a free pass or a penalty — there is nothing to measure.

    if check is not None:
        gate = check.get("truth_gate")
        if gate in {"PASS", "FAIL"}:
            spec = _rule("check.truth_gate")
            factor = 1.0 if gate == "PASS" else 0.0
            rows.append(
                ProvenanceRow(
                    "check.truth_gate", "check", spec.max_weight, spec.max_weight * factor
                )
            )

    return _make_pillar("truth", rows, rule_ids)


def _derive_goodness(safe: dict | None) -> PillarResult:
    rule_ids = ("safe.high_findings", "safe.medium_findings", "safe.coverage")
    rows: list[ProvenanceRow] = []
    if safe is None:
        return _make_pillar("goodness", rows, rule_ids)

    high = safe.get("high")
    if isinstance(high, int):
        spec = _rule("safe.high_findings")
        factor = max(0.0, 1.0 - min(1.0, high * 0.5))
        rows.append(
            ProvenanceRow("safe.high_findings", "safe", spec.max_weight, spec.max_weight * factor)
        )

    medium = safe.get("medium")
    if isinstance(medium, int):
        spec = _rule("safe.medium_findings")
        factor = max(0.0, 1.0 - min(1.0, medium * 0.25))
        rows.append(
            ProvenanceRow("safe.medium_findings", "safe", spec.max_weight, spec.max_weight * factor)
        )

    scanned = safe.get("scanned_files")
    total = safe.get("total_scannable")
    if isinstance(scanned, int) and isinstance(total, int) and total > 0:
        spec = _rule("safe.coverage")
        ratio = max(0.0, min(1.0, scanned / total))
        rows.append(
            ProvenanceRow("safe.coverage", "safe", spec.max_weight, spec.max_weight * ratio)
        )
    # Missing/None coverage (UNOBSERVED file coverage) intentionally leaves
    # this rule out rather than guessing a ratio — a coverage gap must not
    # silently read as full coverage.

    return _make_pillar("goodness", rows, rule_ids)


def _derive_beauty(check: dict | None) -> PillarResult:
    rule_ids = ("check.beauty_gate",)
    rows: list[ProvenanceRow] = []
    if check is not None:
        gate = check.get("beauty_gate")
        if gate in {"PASS", "FAIL"}:
            spec = _rule("check.beauty_gate")
            factor = 1.0 if gate == "PASS" else 0.0
            rows.append(
                ProvenanceRow(
                    "check.beauty_gate", "check", spec.max_weight, spec.max_weight * factor
                )
            )
    return _make_pillar("beauty", rows, rule_ids)


def _derive_benevolence(check: dict | None) -> PillarResult:
    rule_ids = ("check.readme_present", "check.start_hint_present", "check.help_text_present")
    rows: list[ProvenanceRow] = []
    if check is not None:
        for rule_id, key in (
            ("check.readme_present", "readme_present"),
            ("check.start_hint_present", "start_hint_present"),
            ("check.help_text_present", "help_text_present"),
        ):
            signal = check.get(key)
            if isinstance(signal, bool):
                spec = _rule(rule_id)
                factor = 1.0 if signal else 0.0
                rows.append(
                    ProvenanceRow(rule_id, "check", spec.max_weight, spec.max_weight * factor)
                )
    # hyodo check does not currently emit readme_present / start_hint_present /
    # help_text_present signals; callers that do not pass them get an honest
    # UNOBSERVED Benevolence rather than an invented number. See
    # docs/SCORE_DERIVATION.md "Known gaps".
    return _make_pillar("benevolence", rows, rule_ids)


def _derive_hyo(root: Path) -> PillarResult:
    from hyodo.access_ledger import ACCESS_LEDGER_PATH
    from hyodo.connect import detect as detect_connect_targets
    from hyodo.gates import GATES_CONFIG_RELATIVE_PATH

    rule_ids = ("hyo.config_present", "hyo.connect_wired", "hyo.ledger_present")
    rows: list[ProvenanceRow] = []

    config_present = (root / GATES_CONFIG_RELATIVE_PATH).is_file()
    spec = _rule("hyo.config_present")
    rows.append(
        ProvenanceRow(
            "hyo.config_present",
            "root",
            spec.max_weight,
            spec.max_weight * (1.0 if config_present else 0.0),
        )
    )

    connected = any(detect_connect_targets(root).values())
    spec = _rule("hyo.connect_wired")
    rows.append(
        ProvenanceRow(
            "hyo.connect_wired",
            "root",
            spec.max_weight,
            spec.max_weight * (1.0 if connected else 0.0),
        )
    )

    ledger_present = (root / ACCESS_LEDGER_PATH).is_file()
    spec = _rule("hyo.ledger_present")
    rows.append(
        ProvenanceRow(
            "hyo.ledger_present",
            "root",
            spec.max_weight,
            spec.max_weight * (1.0 if ledger_present else 0.0),
        )
    )

    return _make_pillar("hyo", rows, rule_ids)


def derive_pillars(
    root: Path,
    *,
    check: dict | None = None,
    safe: dict | None = None,
    test_integrity: dict | None = None,
) -> DerivedPillars:
    """Derive the five HyoDo Integrity Score pillar inputs from observations.

    Args:
        root: Project root. Used only for Hyo's filesystem-presence signals
            (``.hyodo/gates.toml``, ``.hyodo/mcp-access.jsonl``) and
            ``hyodo connect`` detection — never for a fresh scan; callers
            pass already-computed observations for the other pillars.
        check: Optional dict describing a `hyodo check` run. Recognized
            keys: ``truth_gate`` / ``beauty_gate`` (``"PASS"`` / ``"FAIL"``),
            ``readme_present`` / ``start_hint_present`` / ``help_text_present``
            (bool onboarding signals; omit or leave absent when unmeasured).
        safe: Optional dict describing a `hyodo safe` run. Recognized keys:
            ``high`` / ``medium`` (int finding counts), ``scanned_files`` /
            ``total_scannable`` (int file coverage).
        test_integrity: Optional dict describing a test-integrity scan.
            Recognized keys: ``total_tests`` / ``vacuous_tests`` (int).

    Returns:
        A :class:`DerivedPillars` with one :class:`PillarResult` per pillar,
        each carrying its own coverage and provenance. Missing evidence
        never becomes a 0 or 100 — it becomes ``UNOBSERVED``.
    """
    return DerivedPillars(
        benevolence=_derive_benevolence(check),
        truth=_derive_truth(test_integrity, check),
        goodness=_derive_goodness(safe),
        hyo=_derive_hyo(root),
        beauty=_derive_beauty(check),
    )


def apply_override(result: PillarResult, value: float) -> PillarResult:
    """Return a copy of *result* overridden by an explicit CLI value.

    Recorded as a single provenance row with ``override=True`` so JSON/table
    output shows the override took precedence over any derived evidence.
    """
    row = ProvenanceRow(
        rule_id=f"override.{result.pillar}",
        source="cli-flag",
        weight=100.0,
        contribution=value * 100.0,
        override=True,
    )
    return PillarResult(
        pillar=result.pillar,
        value=value * 100.0,
        coverage="OBSERVED",
        provenance=(row,),
        override=True,
    )


def geometric_mean_observed(values_0_100: list[float]) -> float:
    """Geometric mean of 0-100 pillar values, scaled to the 1-10 range first.

    Mirrors ``hyodo.calculate_geometric_mean``'s 1-10 scaling so a partial
    Eternity computed here is on the same footing as the full one, but
    accepts any number of values (1-5) instead of requiring exactly five —
    used only when at least one pillar is UNOBSERVED and the full formula
    cannot be called.
    """
    if not values_0_100:
        return 0.0
    product = 1.0
    for v in values_0_100:
        bounded = max(0.0, min(100.0, v))
        scaled = 1 + (bounded / 100.0) * 9
        if scaled <= 0:
            return 0.0
        product *= scaled
    return product ** (1 / len(values_0_100))


__all__ = [
    "PILLAR_NAMES",
    "PILLAR_RULE_TABLE",
    "Coverage",
    "DerivedPillars",
    "PillarResult",
    "ProvenanceRow",
    "RuleSpec",
    "apply_override",
    "derive_pillars",
    "geometric_mean_observed",
]
