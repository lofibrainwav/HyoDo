from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .contracts import ReflexionContract


@dataclass
class Step:
    kind: str
    content: str


def run_reflexion(
    input_text: str, contract: ReflexionContract, *, dry_run: bool = True
) -> dict[str, Any]:
    """
    Core reflection execution loop.
    Supports a sequential loop of critique and improvement.
    """
    t0 = time.time()
    steps: list[dict[str, str]] = []

    def elapsed() -> float:
        return time.time() - t0

    def stop_time_budget() -> bool:
        return elapsed() >= float(contract.time_budget_sec)

    iters = 0
    draft = f"DRAFT: {input_text}"
    steps.append({"kind": "draft", "content": draft})

    # Core logic loop (simulated in dry_run)
    while iters < contract.max_iters:
        if stop_time_budget():
            break

        iters += 1

        if dry_run:
            # Simulate critique and revision in dry-run mode
            critique = f"(Dry Run Critique {iters}): Ensure the solution is SSOT-compliant."
            improved = (
                f"(Dry Run Improved {iters}): Optimized for Trinity Pillars. Input: {input_text}"
            )
        else:
            # Future Engine integration (LangGraph/CrewAI) will go here
            raise RuntimeError(
                "non_dry_run_not_configured: provide an engine adapter before enabling production mode"
            )

        steps.append({"kind": "critique", "content": critique})
        steps.append({"kind": "final", "content": improved})

        # Logic to decide if we stop (in dry run we just do one iter for smoke test)
        break

    return {
        "contract": {"fingerprint": contract.fingerprint, "version": contract.version},
        "input": input_text,
        "dry_run": dry_run,
        "iters": iters,
        "elapsed_sec": round(elapsed(), 6),
        "steps": steps,
    }
