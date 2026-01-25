from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ReflexionContract:
    """
    眞善美孝 philosophy alignment scores
    - version: Contract version (SSOT)
    - max_iters: Maximum reflection loops
    - time_budget_sec: Execution timeout
    - dry_run_default: Safety first
    - risk_threshold: Threshold for human-in-the-loop
    """

    version: int
    max_iters: int
    time_budget_sec: int
    dry_run_default: bool
    risk_threshold: int
    stop_conditions: list[dict[str, Any]]
    judge: dict[str, Any]

    @property
    def fingerprint(self) -> str:
        """Unique ID for the contract state to ensure SSOT integrity"""
        s = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(s).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "max_iters": self.max_iters,
            "time_budget_sec": self.time_budget_sec,
            "dry_run_default": self.dry_run_default,
            "risk_threshold": self.risk_threshold,
            "stop_conditions": self.stop_conditions,
            "judge": self.judge,
        }


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def load_reflexion_contract(path: str | Path) -> ReflexionContract:
    """Loads and validates a reflexion contract from YAML"""
    p = Path(path)
    _require(p.exists(), f"contract_not_found: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), "contract_invalid: root must be mapping")

    version = int(data.get("version", 0))
    max_iters = int(data.get("max_iters", 0))
    time_budget_sec = int(data.get("time_budget_sec", 0))
    dry_run_default = bool(data.get("dry_run_default", True))
    risk_threshold = int(data.get("risk_threshold", -1))
    stop_conditions = data.get("stop_conditions", [])
    judge = data.get("judge", {})

    # Strict SSOT validation
    _require(version >= 1, "contract_invalid: version must be >= 1")
    _require(1 <= max_iters <= 20, "contract_invalid: max_iters must be 1..20")
    _require(1 <= time_budget_sec <= 300, "contract_invalid: time_budget_sec must be 1..300")
    _require(0 <= risk_threshold <= 100, "contract_invalid: risk_threshold must be 0..100")
    _require(
        isinstance(stop_conditions, list) and all(isinstance(x, dict) for x in stop_conditions),
        "contract_invalid: stop_conditions must be list[dict]",
    )
    _require(isinstance(judge, dict), "contract_invalid: judge must be mapping")

    rubric = judge.get("rubric", [])
    pass_score = judge.get("pass_score", None)
    _require(
        isinstance(rubric, list) and all(isinstance(x, str) for x in rubric),
        "contract_invalid: judge.rubric must be list[str]",
    )
    _require(
        isinstance(pass_score, (int, float)) and 0 <= float(pass_score) <= 1,
        "contract_invalid: judge.pass_score must be 0..1",
    )

    return ReflexionContract(
        version=version,
        max_iters=max_iters,
        time_budget_sec=time_budget_sec,
        dry_run_default=dry_run_default,
        risk_threshold=risk_threshold,
        stop_conditions=stop_conditions,
        judge=judge,
    )
