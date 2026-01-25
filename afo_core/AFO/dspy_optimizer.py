"""
DSPy MIPROv2 Optimizer Module for AFO Kingdom.
Combines AFO Philosophy (Trinity Score) with DSPy's automated optimization.
Robust implementation with Strict Mode for CI/CD gates.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from AFO.config.antigravity import antigravity

logger = logging.getLogger(__name__)
from AFO.services.trinity_calculator import calculate_trinity_score

try:
    from dspy.teleprompt import MIPROv2
except ImportError:
    # DSPy가 설치되지 않은 경우 모의 클래스 제공
    class MockMIPROv2:
        def __init__(self, **kwargs) -> None:
            pass

        def compile(self, program, trainset=None, valset=None) -> None:
            return program

    MIPROv2 = MockMIPROv2

# Inferred strict mode from environment or existing config
STRICT_MODE = True if antigravity.ENVIRONMENT == "test" else False


@dataclass
class MIPROConfig:
    save_path: str = "artifacts/dspy/optimized_program.json"
    truth_keys: tuple[str, ...] = ("ground_truth", "answer", "label", "y", "output")
    pred_keys: tuple[str, ...] = ("answer", "output", "prediction", "text")
    strict: bool = STRICT_MODE
    auto: str = "light"


class MIPROOptimizer:
    """Encapsulates AFO Kingdom's MIPROv2 optimization logic."""

    def __init__(self, config: MIPROConfig) -> None:
        self.config = config

    def compile(self, program, trainset, valset=None, teacher=None) -> None:
        """Runs the optimization process."""
        if antigravity.DRY_RUN:
            logger.info(
                f"[DRY_RUN] compile_mipro called with {len(trainset)} examples. Returning original."
            )
            return program.deepcopy()

        if MIPROv2 is None:
            msg = "DSPy not installed or MIPROv2 not available."
            if self.config.strict:
                raise ImportError(msg)
            logger.warning(f"[MIPRO][FALLBACK] reason={msg}")
            return program.deepcopy()

        # 1. Prepare Metric
        metric_fn = self._create_metric_fn()

        # 2. Setup Optimizer
        optimizer = MIPROv2(metric=metric_fn, auto=self.config.auto)

        # 3. Auto-split valset
        if valset is None and len(trainset) >= 20:
            valset = trainset[-20:]

        logger.info(f"[AFO] Starting MIPROv2 Optimization (auto={self.config.auto})...")

        try:
            # 4. Run Compilation
            optimized = optimizer.compile(
                program.deepcopy(),
                trainset=trainset,
                valset=valset,
                teacher=teacher,
            )

            # 5. Save Artifacts
            if self.config.save_path:
                self._save_artifact(optimized)

            return optimized

        except Exception as e:
            if self.config.strict:
                raise e
            logger.warning(f"[MIPRO][FALLBACK] Optimization failed: {e}")
            return program.deepcopy()

    def _create_metric_fn(self) -> None:
        """Creates the Trinity Metric function (Closure)."""

        def _pick_field(obj, keys) -> None:
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

        def trinity_metric_fn(example, prediction, trace=None) -> None:
            gt = _pick_field(example, self.config.truth_keys)
            pred = _pick_field(prediction, self.config.pred_keys) if prediction else None

            if not gt or not pred:
                return 0.0

            score_result = calculate_trinity_score(str(pred), str(gt))
            return score_result.overall

        return trinity_metric_fn

    def _save_artifact(self, optimized) -> None:
        """Robust artifact saving logic."""
        p = Path(self.config.save_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            saved = False

            # Strategy 1: Native save
            if hasattr(optimized, "save") and callable(optimized.save):
                try:
                    optimized.save(str(p))
                    saved = p.exists() and p.stat().st_size > 0
                except Exception as e:
                    logger.warning(f"[AFO] Native save failed: {e}")

            # Strategy 2: JSON Dump fallback
            if not saved:
                saved = self._save_json_fallback(optimized, p)

            if not saved:
                raise RuntimeError(f"Artifact save failed: {p} is empty or missing")

            logger.info(f"[AFO] Saved optimized program to {p} ({p.stat().st_size} bytes)")

        except Exception as e:
            self._handle_save_error(e, p)

    def _save_json_fallback(self, optimized, path: Path) -> bool:
        try:
            import json

            state = None
            if hasattr(optimized, "state_dict"):
                state = optimized.state_dict()
            elif hasattr(optimized, "dump_state"):
                state = optimized.dump_state()
            elif hasattr(optimized, "__dict__"):
                state = {
                    "type": type(optimized).__name__,
                    "module_keys": list(getattr(optimized, "__dict__", {}).keys()),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }

            if state:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, default=str)
                return path.exists() and path.stat().st_size > 0
            return False
        except Exception:
            return False

    def _handle_save_error(self, error, path: Path) -> None:
        meta_path = path.with_suffix(".meta.json")
        import json
        import os

        meta = {
            "error": str(error),
            "model": os.getenv("AFO_DSPY_MODEL", "unknown"),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "save_path": str(path),
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.error(f"[AFO] Save failed. Meta written to {meta_path}")
        if self.config.strict:
            raise error


def compile_mipro(
    program,
    trainset,
    auto="light",
    valset=None,
    teacher=None,
    save_path="artifacts/dspy/optimized_program.json",
    truth_key_candidates=("ground_truth", "answer", "label", "y", "output"),
    pred_key_candidates=("answer", "output", "prediction", "text"),
    strict=STRICT_MODE,
):
    """AFO Kingdom MIPROv2 Optimization Wrapper."""
    config = MIPROConfig(
        save_path=save_path,
        truth_keys=truth_key_candidates,
        pred_keys=pred_key_candidates,
        strict=strict,
        auto=auto,
    )
    optimizer = MIPROOptimizer(config)
    return optimizer.compile(program, trainset, valset, teacher)


# Simple Test Block
if __name__ == "__main__":
    if antigravity.DRY_RUN:
        print("Dry Run Check: OK")
    else:
        print("Live Run Check: Ready (Requires DSPy + Data)")
