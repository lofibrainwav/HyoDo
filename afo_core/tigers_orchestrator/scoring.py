"""
Trinity Score Aggregator for Tiger Generals (5호장군)

Weighted scoring algorithm and dynamic risk aggregation
based on AGENTS.md SSOT and 2026 distributed systems best practices.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


TIGER_WEIGHTS = {
    "truth_guard": 0.35,
    "goodness_gate": 0.35,
    "beauty_craft": 0.20,
    "serenity_deploy": 0.05,
    "eternity_log": 0.05,
}


class TrinityScoreAggregator:
    """Trinity Score aggregation with weighted scoring and dynamic risk calculation"""

    def __init__(self) -> None:
        self.scores: dict[str, float] = {}
        self.risk_factors: dict[str, Any] = {}
        self.weights = TIGER_WEIGHTS.copy()

    def add_score(self, general_name: str, score: float) -> None:
        """Add individual general's score"""
        self.scores[general_name] = score
        logger.debug(f"Added score for {general_name}: {score}")

    def calculate_trinity_score(self) -> float:
        """Calculate weighted Trinity Score"""
        trinity_score = 0.0

        for general_name, score in self.scores.items():
            weight = self.weights.get(general_name, 0.0)
            trinity_score += score * weight

        return round(trinity_score, 2)

    def calculate_risk_score(self, inputs: dict[str, Any]) -> float:
        """Calculate dynamic risk score"""
        risk_factors = []

        # Test failure rate (0-30)
        test_results = inputs.get("test_results", {})
        if test_results:
            total = test_results.get("total", 0)
            failed = test_results.get("failed", 0)
            if total > 0:
                failure_rate = failed / total
                risk_factors.append(failure_rate * 30)

        # Lint violations (0-20)
        lint_results = inputs.get("lint_results", {})
        if lint_results:
            violations = lint_results.get("violations", 0)
            risk_factors.append(min(violations * 2, 20))

        # Security vulnerabilities (0-30)
        security_results = inputs.get("security_results", {})
        if security_results:
            vulnerabilities = security_results.get("vulnerabilities", 0)
            risk_factors.append(min(vulnerabilities * 10, 30))

        # Code complexity (0-20)
        complexity = inputs.get("complexity_score", 0)
        if complexity > 50:
            risk_factors.append(min((complexity - 50) * 0.5, 20))

        # General failure history (0-50)
        failure_history = inputs.get("general_failures", [])
        if failure_history:
            now = datetime.now()
            recent_failures = len(
                [
                    f
                    for f in failure_history
                    if f.get("timestamp")
                    and datetime.fromisoformat(f["timestamp"]) > now - timedelta(hours=24)
                ]
            )
            risk_factors.append(min(recent_failures * 5, 50))

        # Cap at 100
        total_risk = float(min(sum(risk_factors), 100.0))
        return total_risk

    def get_decision(self) -> str:
        """Get decision based on Trinity Score and Risk Score"""
        trinity_score = self.calculate_trinity_score()
        risk_score = self.calculate_risk_score(self.scores)

        # Decision Matrix
        if trinity_score >= 90.0 and risk_score <= 10.0:
            return "AUTO_RUN"
        elif 70.0 <= trinity_score < 90.0 and risk_score <= 10.0:
            return "ASK_COMMANDER"
        else:
            return "BLOCK"

    def generate_evidence(self) -> dict[str, Any]:
        """Generate Trinity Evidence"""
        return {
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "trinity_score": self.calculate_trinity_score(),
            "risk_score": self.calculate_risk_score(self.scores),
            "decision": self.get_decision(),
            "scores_by_general": self.scores.copy(),
            "weights": self.weights.copy(),
            "metadata": {
                "scoring_algorithm": "weighted_average_v2",
                "risk_algorithm": "dynamic_aggregation_2026",
            },
        }

    def get_status(self) -> dict[str, Any]:
        """Get aggregator status"""
        return {
            "trinity_score": self.calculate_trinity_score(),
            "risk_score": self.calculate_risk_score(self.scores),
            "decision": self.get_decision(),
            "scores_by_general": self.scores.copy(),
            "weights": self.weights.copy(),
        }
