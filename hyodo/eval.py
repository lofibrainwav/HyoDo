"""Local, deterministic golden-dataset evaluation helpers."""

from __future__ import annotations

import hashlib
import json
import math
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


def _describe_value(value: Any) -> str:
    """Return a short, bounded description of a rejected dataset value."""
    shown = repr(value)
    if len(shown) > 60:
        shown = shown[:57] + "..."
    return f"{shown} ({type(value).__name__})"


class _StrictJSONError(ValueError):
    """JSON that parses under Python defaults but is ambiguous as evidence."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _StrictJSONError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise _StrictJSONError(f"non-finite number {name}")


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise _StrictJSONError(f"number {text} is not finite")
    return value


def _strict_json_loads(text: str) -> Any:
    """Parse RFC 8259 JSON without Python's lenient extensions.

    Duplicate object keys (last-one-wins), ``NaN``/``Infinity`` literals, and
    numbers that overflow to infinity all make one document mean more than
    one thing, so they are rejected instead of silently resolved. Input the
    interpreter cannot materialize (integers beyond Python's digit limit,
    nesting beyond the recursion limit) is reported the same way instead of
    escaping as an unexpected exception.
    """
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except (json.JSONDecodeError, _StrictJSONError):
        raise
    except RecursionError as exc:
        raise _StrictJSONError("nesting exceeds the parser's recursion limit") from exc
    except ValueError as exc:
        raise _StrictJSONError(str(exc)[:200]) from exc


def load_dataset(path: Path) -> list[EvalCase]:
    """Load a deterministic JSONL dataset, rejecting malformed input."""
    cases, _ = load_dataset_snapshot(path)
    return cases


def load_dataset_snapshot(path: Path) -> tuple[list[EvalCase], str]:
    """Read the dataset once; return its cases and the SHA-256 of those exact bytes.

    Parsing and hashing share one in-memory snapshot, so a file replaced
    between two reads can never produce a receipt whose hash describes bytes
    other than the ones evaluated.
    """
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise EvalInputError("dataset file does not exist") from exc
    except OSError as exc:
        raise EvalInputError(f"dataset unreadable: {exc}") from exc
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvalInputError(f"dataset is not valid UTF-8 at byte {exc.start}") from exc
    return _parse_dataset_text(text), hashlib.sha256(data).hexdigest()


def _parse_dataset_text(text: str) -> list[EvalCase]:
    if not text.strip():
        raise EvalInputError("dataset file is empty")

    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise EvalInputError(f"dataset line {line_number} is empty")
        try:
            raw = _strict_json_loads(line)
        except json.JSONDecodeError as exc:
            raise EvalInputError(f"dataset line {line_number} is not JSON") from exc
        except _StrictJSONError as exc:
            raise EvalInputError(f"dataset line {line_number} is ambiguous JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise EvalInputError(f"dataset line {line_number} must be an object")
        case_id = raw.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvalInputError(
                f"dataset line {line_number} has invalid id: got {_describe_value(case_id)}; "
                'expected a non-empty string, for example {"id": "case-1", ...}'
            )
        if case_id in seen_ids:
            raise EvalInputError(f"dataset line {line_number} repeats id {case_id!r}")
        if "input" not in raw or "expected" not in raw:
            raise EvalInputError(f"dataset line {line_number} needs input and expected")
        scoring = raw.get("scoring")
        if not isinstance(scoring, str) or scoring not in {
            "exact",
            "contains",
            "json_path",
            "custom",
        }:
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
        or not isinstance(expected.get("operator"), str)
        or expected["operator"]
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
    cases, dataset_sha256 = load_dataset_snapshot(dataset_path)
    command = shlex.split(runner)
    if not command:
        raise EvalInputError("runner command is empty")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:12]}"
    result: dict[str, Any] = {
        "schema_version": EVAL_SCHEMA_VERSION,
        "run_id": run_id,
        "measured_at": now,
        "dataset_sha256": dataset_sha256,
        "runner": command,
        "min_pass_rate": min_pass_rate,
        "ledger_path": EVAL_LEDGER_RELATIVE_PATH.as_posix(),
        "provenance": _collect_provenance(root),
        "cases": [],
    }

    for case in cases:
        actual, failure = _run_case(command, case, root, timeout_seconds)
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
    command: list[str], case: EvalCase, root: Path, timeout_seconds: int
) -> tuple[Any, dict[str, Any] | None]:
    request = json.dumps({"id": case.case_id, "input": case.input_value}, sort_keys=True)
    try:
        completed = subprocess.run(
            command,
            input=request.encode("utf-8"),
            capture_output=True,
            timeout=timeout_seconds,
            cwd=str(root),
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
        detail = completed.stderr or completed.stdout or b"runner failed"
        return None, {
            "code": "runner_exit",
            "returncode": completed.returncode,
            "message": detail.decode("utf-8", errors="replace").strip()[:500],
        }
    try:
        stdout = completed.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None, {
            "code": "runner_output_not_json",
            "message": "runner stdout is not valid UTF-8",
        }
    try:
        parsed = _strict_json_loads(stdout)
    except json.JSONDecodeError:
        return None, {"code": "runner_output_not_json", "message": "runner stdout must be JSON"}
    except _StrictJSONError as exc:
        return None, {
            "code": "runner_output_not_json",
            "message": f"runner stdout is ambiguous JSON: {exc}",
        }
    if isinstance(parsed, dict) and "output" in parsed:
        return parsed["output"], None
    return parsed, None


def _json_equal(left: Any, right: Any) -> bool:
    """JSON value equality that keeps booleans distinct from numbers.

    Python treats ``True == 1`` and ``False == 0``; JSON does not. Numbers
    still compare numerically (``1 == 1.0``), which preserves the existing
    numeric contract. Containers compare element-wise with the same rule,
    iteratively, so deeply nested values cannot exhaust the call stack.
    """
    pending: list[tuple[Any, Any]] = [(left, right)]
    while pending:
        a, b = pending.pop()
        if isinstance(a, bool) or isinstance(b, bool):
            if not (isinstance(a, bool) and isinstance(b, bool) and a is b):
                return False
            continue
        if isinstance(a, dict) or isinstance(b, dict):
            if not (isinstance(a, dict) and isinstance(b, dict)) or a.keys() != b.keys():
                return False
            pending.extend((a[key], b[key]) for key in a)
            continue
        if isinstance(a, list) or isinstance(b, list):
            if not (isinstance(a, list) and isinstance(b, list)) or len(a) != len(b):
                return False
            pending.extend(zip(a, b, strict=True))
            continue
        if a != b:
            return False
    return True


def _contains_bool(value: Any) -> bool:
    """Return True if *value* is, or anywhere contains, a JSON boolean."""
    pending: list[Any] = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, bool):
            return True
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return False


def _json_member(item: Any, values: list[Any]) -> bool:
    return any(_json_equal(item, value) for value in values)


def score_case(scoring: str, actual: Any, expected: Any) -> tuple[bool, str]:
    """Score one output with only deterministic, built-in comparators."""
    if scoring == "exact":
        return _json_equal(actual, expected), "exact equality"
    if scoring == "contains":
        if isinstance(actual, str):
            return str(expected) in actual, "string containment"
        if isinstance(actual, list):
            return _json_member(expected, actual), "list membership"
        return False, "contains requires a string or list output"
    if scoring == "json_path":
        assert isinstance(expected, dict)
        found, value = _json_path(actual, expected["path"])
        return found and _json_equal(value, expected["value"]), "JSON path equality"
    assert scoring == "custom"
    assert isinstance(expected, dict)
    found, value = _json_path(actual, expected["path"])
    if not found:
        return False, "custom assertion path missing"
    target = expected["value"]
    operator = expected["operator"]
    ordering = operator in {"gt", "gte", "lt", "lte"}
    if ordering and (_contains_bool(value) or _contains_bool(target)):
        return False, f"custom {operator} assertion (booleans are not ordered)"
    try:
        if operator == "equals":
            passed = _json_equal(value, target)
        elif operator == "not_equals":
            passed = not _json_equal(value, target)
        elif operator == "gt":
            passed = value > target
        elif operator == "gte":
            passed = value >= target
        elif operator == "lt":
            passed = value < target
        elif operator == "lte":
            passed = value <= target
        elif isinstance(value, list):
            passed = _json_member(target, value)
        else:
            passed = target in value
    except (TypeError, RecursionError):
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


def _collect_provenance(root: Path) -> dict[str, Any]:
    """Capture the code state a run executed against, so a result can be tied
    back to a specific commit rather than trusted on its author's word.

    Git fields are ``None`` — never a silently-empty string or a false
    "clean" — when ``root`` is not a readable git repository; ``git_reason``
    then explains what was unobserved instead of pretending it is absent.
    """
    provenance: dict[str, Any] = {
        "run_cwd": str(root),
        "git_head_sha": None,
        "git_dirty": None,
        "git_reason": None,
    }
    from hyodo.provenance import clean_git_env

    git_env = clean_git_env()
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(root),
            check=False,
            env=git_env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        provenance["git_reason"] = f"git unavailable: {exc}"
        return provenance
    if head.returncode != 0 or not head.stdout.strip():
        provenance["git_reason"] = (head.stderr or "not a git repository").strip()[:200]
        return provenance
    provenance["git_head_sha"] = head.stdout.strip()

    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(root),
            check=False,
            env=git_env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        provenance["git_reason"] = f"git status unavailable: {exc}"
        return provenance
    if status.returncode != 0:
        provenance["git_reason"] = (status.stderr or "git status failed").strip()[:200]
        return provenance
    provenance["git_dirty"] = bool(status.stdout.strip())
    return provenance


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
