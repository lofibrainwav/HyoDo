"""Local, deterministic golden-dataset evaluation helpers."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVAL_RUNS_RELATIVE_DIR = Path(".hyodo") / "eval-runs"
EVAL_LEDGER_RELATIVE_PATH = Path(".hyodo") / "eval-runs.jsonl"
EVAL_SCHEMA_VERSION = "hyodo.eval-run/v1"
_JSON_PATH_TOKEN = re.compile(r"(?:\.([A-Za-z_][A-Za-z0-9_-]*))|(?:\[([0-9]+)\])")


class EvalInputError(ValueError):
    """A dataset cannot be observed or trusted."""


@dataclass(frozen=True)
class EvalCase:
    """One validated golden evaluation case."""

    case_id: str
    input_value: Any
    expected: Any
    scoring: str
    tags: list[str]


def load_dataset(path: Path) -> list[EvalCase]:
    """Load a deterministic JSONL dataset, rejecting malformed input."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EvalInputError("dataset file does not exist") from exc
    except OSError as exc:
        raise EvalInputError(f"dataset unreadable: {exc}") from exc
    if not text.strip():
        raise EvalInputError("dataset file is empty")

    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise EvalInputError(f"dataset line {line_number} is empty")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalInputError(f"dataset line {line_number} is not JSON") from exc
        if not isinstance(raw, dict):
            raise EvalInputError(f"dataset line {line_number} must be an object")
        case_id = raw.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvalInputError(f"dataset line {line_number} has invalid id")
        if case_id in seen_ids:
            raise EvalInputError(f"dataset line {line_number} repeats id {case_id!r}")
        if "input" not in raw or "expected" not in raw:
            raise EvalInputError(f"dataset line {line_number} needs input and expected")
        scoring = raw.get("scoring")
        if scoring not in {"exact", "contains", "json_path", "custom"}:
            raise EvalInputError(f"dataset line {line_number} has unsupported scoring")
        tags = raw.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise EvalInputError(f"dataset line {line_number} has invalid tags")
        _validate_expected(scoring, raw["expected"], line_number)
        cases.append(EvalCase(case_id, raw["input"], raw["expected"], scoring, tags))
        seen_ids.add(case_id)
    return cases


def _validate_expected(scoring: str, expected: Any, line_number: int) -> None:
    if scoring == "contains" and not isinstance(expected, (str, int, float, bool)):
        raise EvalInputError(
            f"dataset line {line_number} contains scoring needs a scalar expected value"
        )
    if scoring == "json_path" and (
        not isinstance(expected, dict)
        or not isinstance(expected.get("path"), str)
        or "value" not in expected
    ):
        raise EvalInputError(
            f"dataset line {line_number} json_path needs expected.path and expected.value"
        )
    if scoring == "custom" and (
        not isinstance(expected, dict)
        or not isinstance(expected.get("path"), str)
        or expected.get("operator")
        not in {"equals", "not_equals", "gt", "gte", "lt", "lte", "contains"}
        or "value" not in expected
    ):
        raise EvalInputError(f"dataset line {line_number} custom scoring has an invalid assertion")


def run_evaluation(
    dataset_path: Path,
    runner: str,
    root: Path,
    min_pass_rate: float,
    timeout_seconds: int,
) -> tuple[int, dict[str, Any]]:
    """Run a local dataset and write both a result artifact and ledger reference."""
    cases = load_dataset(dataset_path)
    command = shlex.split(runner)
    if not command:
        raise EvalInputError("runner command is empty")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:12]}"
    result: dict[str, Any] = {
        "schema_version": EVAL_SCHEMA_VERSION,
        "run_id": run_id,
        "measured_at": now,
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "runner": command,
        "min_pass_rate": min_pass_rate,
        "ledger_path": EVAL_LEDGER_RELATIVE_PATH.as_posix(),
        "cases": [],
    }

    for case in cases:
        actual, failure = _run_case(command, case, timeout_seconds)
        if failure is not None:
            result["status"] = "FAIL"
            result["runner_failure"] = {"case_id": case.case_id, **failure}
            result["pass_rate"] = None
            return _persist_result(root, result, exit_code=1)
        passed, detail = score_case(case.scoring, actual, case.expected)
        result["cases"].append(
            {
                "id": case.case_id,
                "tags": case.tags,
                "scoring": case.scoring,
                "expected": case.expected,
                "actual": actual,
                "passed": passed,
                "detail": detail,
            }
        )

    passed_count = sum(1 for case in result["cases"] if case["passed"])
    pass_rate = passed_count / len(cases)
    result["pass_rate"] = pass_rate
    result["status"] = "PASS" if pass_rate >= min_pass_rate else "FAIL"
    return _persist_result(root, result, exit_code=0 if result["status"] == "PASS" else 1)


def _run_case(
    command: list[str], case: EvalCase, timeout_seconds: int
) -> tuple[Any, dict[str, Any] | None]:
    request = json.dumps({"id": case.case_id, "input": case.input_value}, sort_keys=True)
    try:
        completed = subprocess.run(
            command,
            input=request,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, {
            "code": "runner_timeout",
            "message": f"runner timed out after {timeout_seconds}s",
        }
    except OSError as exc:
        return None, {"code": "runner_unavailable", "message": str(exc)}
    if completed.returncode != 0:
        return None, {
            "code": "runner_exit",
            "returncode": completed.returncode,
            "message": (completed.stderr or completed.stdout or "runner failed").strip()[:500],
        }
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, {"code": "runner_output_not_json", "message": "runner stdout must be JSON"}
    if isinstance(parsed, dict) and "output" in parsed:
        return parsed["output"], None
    return parsed, None


def score_case(scoring: str, actual: Any, expected: Any) -> tuple[bool, str]:
    """Score one output with only deterministic, built-in comparators."""
    if scoring == "exact":
        return actual == expected, "exact equality"
    if scoring == "contains":
        if isinstance(actual, str):
            return str(expected) in actual, "string containment"
        if isinstance(actual, list):
            return expected in actual, "list membership"
        return False, "contains requires a string or list output"
    if scoring == "json_path":
        assert isinstance(expected, dict)
        found, value = _json_path(actual, expected["path"])
        return found and value == expected["value"], "JSON path equality"
    assert scoring == "custom"
    assert isinstance(expected, dict)
    found, value = _json_path(actual, expected["path"])
    if not found:
        return False, "custom assertion path missing"
    target = expected["value"]
    operator = expected["operator"]
    try:
        if operator == "equals":
            passed = value == target
        elif operator == "not_equals":
            passed = value != target
        elif operator == "gt":
            passed = value > target
        elif operator == "gte":
            passed = value >= target
        elif operator == "lt":
            passed = value < target
        elif operator == "lte":
            passed = value <= target
        else:
            passed = target in value
    except TypeError:
        passed = False
    return passed, f"custom {operator} assertion"


def _json_path(value: Any, path: str) -> tuple[bool, Any]:
    """Resolve a limited, deterministic JSONPath subset: ``$``, ``$.key``, ``$[0]``."""
    if not path.startswith("$"):
        return False, None
    current = value
    position = 1
    while position < len(path):
        match = _JSON_PATH_TOKEN.match(path, position)
        if match is None:
            return False, None
        key, index_text = match.groups()
        if key is not None:
            if not isinstance(current, dict) or key not in current:
                return False, None
            current = current[key]
        else:
            if not isinstance(current, list):
                return False, None
            index = int(index_text)
            if index >= len(current):
                return False, None
            current = current[index]
        position = match.end()
    return True, current


def _persist_result(
    root: Path, result: dict[str, Any], exit_code: int
) -> tuple[int, dict[str, Any]]:
    """Persist a result plus compact append-only ledger receipt, or report unobserved storage."""
    relative_result = EVAL_RUNS_RELATIVE_DIR / f"{result['run_id']}.json"
    result["result_path"] = relative_result.as_posix()
    try:
        result_path = root / relative_result
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        ledger_path = root / EVAL_LEDGER_RELATIVE_PATH
        with ledger_path.open("a", encoding="utf-8") as ledger:
            ledger.write(
                json.dumps(
                    {
                        "schema_version": EVAL_SCHEMA_VERSION,
                        "run_id": result["run_id"],
                        "measured_at": result["measured_at"],
                        "status": result["status"],
                        "pass_rate": result["pass_rate"],
                        "result_path": relative_result.as_posix(),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    except OSError as exc:
        return 2, {"status": "UNOBSERVED", "reason": f"cannot persist eval result: {exc}"}
    return exit_code, {
        "run_id": result["run_id"],
        "status": result["status"],
        "pass_rate": result["pass_rate"],
        "result_path": relative_result.as_posix(),
        "runner_failure": result.get("runner_failure"),
    }
