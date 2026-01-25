from __future__ import annotations

from typing import TYPE_CHECKING

from AFO.learning_loader import get_learning_profile
from AFO.trinity_config import BASE_CONFIG, apply_learning_profile

from ..decision_result import DecisionResult

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""MERGE Node - Synthesize 3 strategists results with DecisionResult."""


async def merge_node(state: GraphState) -> GraphState:
    """Aggregate all strategist evaluations and make a final decision.

    SSOT Contract: Return DecisionResult, never bare boolean.

    Args:
        state: Current graph state
    Returns:
        Updated graph state with DecisionResult evaluation
    """

    # Get individual scores (5기둥 완전 평가)
    truth_score = state.outputs.get("TRUTH", {}).get("score", 0)
    goodness_score = state.outputs.get("GOODNESS", {}).get("score", 0)
    beauty_score = state.outputs.get("BEAUTY", {}).get("score", 0)
    serenity_score = state.outputs.get("SERENITY", {}).get("score", 0)
    eternity_score = state.outputs.get("ETERNITY", {}).get("score", 0)

    # Boot-Swap: Learning profile 적용
    profile = get_learning_profile()
    effective_config = apply_learning_profile(BASE_CONFIG, profile.data.get("overrides", {}))
    weights = effective_config["weights"]
    thresholds = effective_config["thresholds"]

    pillar_scores = {
        "truth": truth_score,
        "goodness": goodness_score,
        "beauty": beauty_score,
        "filial_serenity": serenity_score,
        "eternity": eternity_score,
    }

    # Calculate Trinity Score (Boot-Swap: effective weights 적용)
    trinity_score = (
        truth_score * weights["truth"]  # 眞 (Truth)
        + goodness_score * weights["goodness"]  # 善 (Goodness)
        + beauty_score * weights["beauty"]  # 美 (Beauty)
        + serenity_score * weights["serenity"]  # 孝 (Serenity)
        + eternity_score * weights["eternity"]  # 永 (Eternity)
    ) * 100

    # SSOT validation: All 5 pillars must be present for valid Trinity Score
    pillars_present = {"truth", "goodness", "beauty"}
    if not pillars_present.issubset(pillar_scores.keys()):
        trinity_score = 0  # Force 0 if pillars missing

    # Risk Score (currently using goodness_score as proxy, can be enhanced)
    risk_score = (1.0 - goodness_score) * 100  # Lower goodness = higher risk

    # Create DecisionResult based on evaluation (Boot-Swap: effective thresholds 적용)
    if (
        trinity_score >= thresholds["auto_run_trinity"]
        and risk_score <= thresholds["auto_run_risk"]
    ):
        decision = DecisionResult.auto_run(trinity_score, risk_score, pillar_scores)
    else:
        decision = DecisionResult.ask_commander(trinity_score, risk_score, pillar_scores)

    # Store DecisionResult in state
    if "MERGE" not in state.outputs:
        state.outputs["MERGE"] = {}

    state.outputs["MERGE"] = decision.to_dict()

    return state
