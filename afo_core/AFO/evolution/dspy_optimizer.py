import antigravity
import json
import os
from typing import Any

import dspy

# Constants
STRICT_MODE = os.getenv("AFO_STRICT_MODE", "0") == "1"

try:
    from dspy.teleprompt import MIPROv2
except ImportError:
    MIPROv2 = None


def _pick_field(obj: Any, keys: list[str]) -> Any | None:
    """Robust field extractor for DSPy Examples."""
    for k in keys:
        if hasattr(obj, k):
            v = getattr(obj, k)
            if v is not None:
                return v
        try:
            if isinstance(obj, dict) and k in obj and obj[k] is not None:
                return obj[k]
        except Exception:
            pass
    return None


def trinity_metric_fn(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """
    Trinity Score Metric Wrapper (Fail-Closed).
    Compares prediction with ground truth using a basic string match or logic.
    """
    truth_keys = ["ground_truth", "answer", "label", "y", "output"]
    pred_keys = ["answer", "output", "prediction", "text"]

    gt = _pick_field(example, truth_keys)
    pred = _pick_field(prediction, pred_keys) if prediction is not None else None

    if gt is None or pred is None:
        return 0.0

    # Simple semantic/string match for now
    # In a full implementation, this calls Trinity Score calculator
    if str(gt).strip().lower() in str(pred).strip().lower():
        return 1.0
    return 0.0


def compile_mipro(
    program: dspy.Program,
    trainset: list[dspy.Example],
    auto: str = "light",
    valset: list[dspy.Example] | None = None,
    save_path: str = "artifacts/dspy/optimized_program.json",
    strict: bool = STRICT_MODE,
) -> dspy.Program:
    """
    AFO Kingdom MIPROv2 Optimization with Safe-Save.
    """
    if antigravity.DRY_RUN:
        print(f"[DRY_RUN] compile_mipro with {len(trainset)} examples. Returning copy.")
        return program.deepcopy()

    if MIPROv2 is None:
        msg = "DSPy not installed or MIPROv2 not available."
        if strict:
            raise ImportError(msg)
        print(f"[MIPRO][FALLBACK] {msg}")
        return program.deepcopy()

    print(f"[MIPRO] Starting optimization: mode={auto}, trainsize={len(trainset)}")

    optimizer = MIPROv2(metric=trinity_metric_fn, auto=auto)
    optimized_program = optimizer.compile(program, trainset=trainset, valset=valset)

    # Safe-Save Logic
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            optimized_program.save(save_path)
            # 0-byte validation
            if os.path.getsize(save_path) == 0:
                raise ValueError("Saved file is 0 bytes.")
            print(f"[MIPRO][SUCCESS] Program saved to {save_path}")
        except Exception as e:
            print(f"[MIPRO][SAVE_FALLBACK] dspy.save failed ({e}), using JSON fallback.")
            # JSON Fallback serialization
            try:
                state = {
                    k: v for k, v in optimized_program.__dict__.items() if not k.startswith("_")
                }
                with open(save_path, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception as e2:
                print(f"[MIPRO][CRITICAL] Save failed: {e2}")

    return optimized_program
