from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""SOCRATES Node - The Philosopher (Maieutics)."""


logger = logging.getLogger(__name__)


async def socrates_node(state: GraphState) -> GraphState:
    """Perform Socratic Questioning to challenge assumptions.

    Scholar: Socrates (Anthropic Sonnet via Adapter or Internal Logic)
    Role: Philosopher. Asks 'Why?' and challenges the premise of the command/plan.
    """
    command = state.input.get("command", "")
    plan = state.plan

    # 0. Check if we should even run (e.g. only on complex tasks)
    # Heuristic: If plan has > 3 steps or if explicitly requested
    should_run = len(plan) > 3 or "socrates" in command.lower()

    if not should_run:
        state.outputs["SOCRATES"] = {
            "status": "skipped",
            "reason": "Task complexity low or not requested.",
        }
        return state

    # 1. Socratic Prompt
    prompt = f"""
    You are Socrates.
    The user wants to execute the following command in the AFO Kingdom:
    "{command}"

    The proposed plan is:
    {json.dumps(plan, indent=2)}

    Your goal is NOT to solve the problem, but to finding logical flaws, unchecked assumptions, or vague definitions.
    Use the Maieutic Method:
    1. Definition: What do they mean by X?
    2. Elenchus: Is X consistent with Y?
    3. Consequence: What happens if we are wrong?

    Return a list of 3 probing questions in JSON format:
    {{
      "probes": [
        "Question 1...",
        "Question 2...",
        "Question 3..."
      ],
      "risk_assessment": "low" | "medium" | "high" | "critical",
      "verdict": "proceed" | "pause_for_thought"
    }}
    """

    socratic_data = {
        "probes": ["Why do you want to do this?", "Is this the only way?", "What if it fails?"],
        "risk_assessment": "low",
        "verdict": "proceed",
    }

    try:
        # Route to a capable model (e.g. Sonnet or GPT-4o)
        response = await llm_router.execute_with_routing(
            prompt,
            context={
                "provider": "anthropic",  # Or openai, depending on available keys
                "model": "claude-3-5-sonnet-20241022",
                "quality_tier": "premium",
            },
        )

        if response and response.get("success"):
            text = response.get("response", "{}")
            text = text.strip().replace("```json", "").replace("```", "").strip()
            try:
                socratic_data = json.loads(text)
            except Exception as e:
                logger.warning(f"Failed to parse Socrates JSON: {e}")
                # Fallback to text if JSON fails
                socratic_data["raw_text"] = text

    except Exception as e:
        state.errors.append(f"Socrates (Maieutics) failed: {e}")

    # 2. Record Output
    state.outputs["SOCRATES"] = {
        "probes": socratic_data.get("probes", []),
        "risk_assessment": socratic_data.get("risk_assessment", "low"),
        "verdict": socratic_data.get("verdict", "proceed"),
        "metadata": {
            "scholar": "Socrates",
            "mode": "Maieutics",
        },
    }

    return state
