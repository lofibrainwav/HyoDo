"""Evidence-binding contracts for `hyodo eval`.

The dataset bytes that are parsed must be the same bytes whose SHA-256 is
recorded, JSON input/output must be strict (no duplicate keys, no non-finite
numbers), malformed dataset field types must stay `UNOBSERVED` instead of
crashing, and built-in comparators must not treat JSON booleans as numbers.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo import eval as eval_mod
from hyodo.cli.main import app
from hyodo.eval import EvalInputError, load_dataset, run_evaluation, score_case

runner = CliRunner()


def _runner_command(path: Path, body: str) -> str:
    path.write_text(body, encoding="utf-8")
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(path))}"


_ECHO_RUNNER = (
    "import json, sys\nreq = json.load(sys.stdin)\nprint(json.dumps({'output': req['input']}))\n"
)


# --- A: one dataset snapshot is parsed and hashed ---------------------------


def test_dataset_hash_binds_the_bytes_that_were_parsed(tmp_path: Path, monkeypatch) -> None:
    """If the file is replaced after the first read, the receipt must still
    describe the bytes that were evaluated, never the replacement."""
    dataset = tmp_path / "golden.jsonl"
    original = b'{"id": "a", "input": "x", "expected": "x", "scoring": "exact"}\n'
    replacement = b'{"id": "b", "input": "y", "expected": "zzz", "scoring": "exact"}\n'
    dataset.write_bytes(original)
    command = _runner_command(tmp_path / "echo.py", _ECHO_RUNNER)

    real_read_bytes = Path.read_bytes
    real_read_text = Path.read_text
    reads = {"n": 0}

    def read_bytes(self: Path) -> bytes:
        data = real_read_bytes(self)
        if self == dataset:
            reads["n"] += 1
            if reads["n"] == 1:
                Path.write_bytes(dataset, replacement)
        return data

    def read_text(self: Path, *args, **kwargs) -> str:
        data = real_read_text(self, *args, **kwargs)
        if self == dataset:
            reads["n"] += 1
            if reads["n"] == 1:
                Path.write_bytes(dataset, replacement)
        return data

    monkeypatch.setattr(eval_mod.Path, "read_bytes", read_bytes)
    monkeypatch.setattr(eval_mod.Path, "read_text", read_text)

    exit_code, summary = run_evaluation(dataset, command, tmp_path, 1.0, 30)

    result = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    assert [case["id"] for case in result["cases"]] == ["a"]
    assert result["dataset_sha256"] == hashlib.sha256(original).hexdigest()
    assert exit_code == 0
    assert reads["n"] == 1, "dataset must be read exactly once per run"


def test_load_dataset_keeps_its_public_signature(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(
        '{"id": "a", "input": 1, "expected": 1, "scoring": "exact"}\n', encoding="utf-8"
    )
    cases = load_dataset(dataset)
    assert [case.case_id for case in cases] == ["a"]


# --- B: strict dataset JSON and field types --------------------------------


@pytest.mark.parametrize(
    "line",
    [
        '{"id": "a", "id": "b", "input": 1, "expected": 1, "scoring": "exact"}',
        '{"id": "a", "input": NaN, "expected": 1, "scoring": "exact"}',
        '{"id": "a", "input": 1, "expected": Infinity, "scoring": "exact"}',
        '{"id": "a", "input": 1, "expected": -Infinity, "scoring": "exact"}',
        '{"id": "a", "input": 1, "expected": 1e400, "scoring": "exact"}',
        '{"id": "a", "input": {"k": 1, "k": 2}, "expected": 1, "scoring": "exact"}',
        '{"id": "a", "input": 1, "expected": 1, "scoring": ["exact"]}',
        '{"id": "a", "input": 1, "expected": 1, "scoring": {"x": 1}}',
        '{"id": "a", "input": 1, "expected": {"path": "$", "operator": ["gt"], "value": 1},'
        ' "scoring": "custom"}',
        '{"id": "a", "input": 1, "expected": {"path": "$", "operator": {"o": 1}, "value": 1},'
        ' "scoring": "custom"}',
    ],
)
def test_malformed_dataset_lines_are_rejected_not_crashed(tmp_path: Path, line: str) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(EvalInputError):
        load_dataset(dataset)


def test_invalid_utf8_dataset_is_unobserved_via_cli(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_bytes(b'{"id": "a", "input": "\xff", "expected": 1, "scoring": "exact"}\n')
    command = _runner_command(tmp_path / "echo.py", _ECHO_RUNNER)

    result = runner.invoke(
        app,
        ["eval", "--dataset", str(dataset), "--runner", command, "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 2, result.output
    assert json.loads(result.output)["status"] == "UNOBSERVED"
    assert not (tmp_path / ".hyodo" / "eval-runs.jsonl").exists()


# --- B: strict runner output ------------------------------------------------


@pytest.mark.parametrize(
    "stdout",
    [
        '{"output": 1, "output": 2}',
        '{"output": NaN}',
        '{"output": Infinity}',
        '{"output": 1e400}',
        '{"output": {"a": 1, "a": 2}}',
    ],
)
def test_ambiguous_runner_output_is_a_failed_run(tmp_path: Path, stdout: str) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(
        '{"id": "a", "input": 1, "expected": 2, "scoring": "exact"}\n', encoding="utf-8"
    )
    command = _runner_command(tmp_path / "bad.py", f"print({stdout!r})\n")

    exit_code, summary = run_evaluation(dataset, command, tmp_path, 1.0, 30)

    assert exit_code == 1
    assert summary["status"] == "FAIL"
    assert summary["runner_failure"]["code"] == "runner_output_not_json"


# --- B: comparators keep JSON booleans distinct from numbers ---------------


@pytest.mark.parametrize(
    ("scoring", "actual", "expected", "passed"),
    [
        ("exact", True, 1, False),
        ("exact", 1, True, False),
        ("exact", False, 0, False),
        ("exact", 0, False, False),
        ("exact", {"a": [True]}, {"a": [1]}, False),
        ("exact", [0], [False], False),
        ("exact", True, True, True),
        ("exact", {"a": [1, "x", None]}, {"a": [1, "x", None]}, True),
        # Numeric 1 == 1.0 is preserved; changing it is a separate compatibility decision.
        ("exact", 1, 1.0, True),
        ("contains", [1, 2], True, False),
        ("contains", [0], False, False),
        ("contains", [True], True, True),
        ("contains", [1, 2], 1, True),
        ("json_path", {"v": True}, {"path": "$.v", "value": 1}, False),
        ("json_path", {"v": 1}, {"path": "$.v", "value": True}, False),
        ("json_path", {"v": [False]}, {"path": "$.v", "value": [0]}, False),
        ("json_path", {"v": 3}, {"path": "$.v", "value": 3}, True),
        ("custom", {"v": True}, {"path": "$.v", "operator": "equals", "value": 1}, False),
        ("custom", {"v": True}, {"path": "$.v", "operator": "not_equals", "value": 1}, True),
        ("custom", {"v": 1}, {"path": "$.v", "operator": "not_equals", "value": 1.0}, False),
        ("custom", {"v": True}, {"path": "$.v", "operator": "gt", "value": 0}, False),
        ("custom", {"v": 1}, {"path": "$.v", "operator": "gte", "value": True}, False),
        ("custom", {"v": False}, {"path": "$.v", "operator": "lt", "value": 1}, False),
        ("custom", {"v": 0}, {"path": "$.v", "operator": "lte", "value": False}, False),
        ("custom", {"v": 2}, {"path": "$.v", "operator": "gt", "value": 1}, True),
        ("custom", {"v": [1]}, {"path": "$.v", "operator": "contains", "value": True}, False),
        ("custom", {"v": [True]}, {"path": "$.v", "operator": "contains", "value": True}, True),
        ("custom", {"v": "abc"}, {"path": "$.v", "operator": "contains", "value": "b"}, True),
    ],
)
def test_comparators_do_not_conflate_booleans_and_numbers(
    scoring: str, actual: object, expected: object, passed: bool
) -> None:
    assert score_case(scoring, actual, expected)[0] is passed


# --- review follow-ups: no crash paths, nested booleans --------------------


def test_deeply_nested_values_compare_without_recursion_error() -> None:
    deep = json.loads("[" * 5000 + "]" * 5000)
    other = json.loads("[" * 5000 + "1" + "]" * 5000)
    assert score_case("exact", deep, deep)[0] is True
    assert score_case("exact", deep, other)[0] is False
    nested_list = json.loads("[" * 5000 + "]" * 5000)
    assert score_case("custom", nested_list, {"path": "$", "operator": "gt", "value": []})[0] in (
        True,
        False,
    )


@pytest.mark.parametrize(
    ("value", "operator", "target"),
    [
        ([True], "gt", [0]),
        ([1], "gte", [True]),
        ([False], "lt", [1]),
        ({"a": [0]}, "lte", {"a": [False]}),
    ],
)
def test_nested_booleans_are_never_ordered(value: object, operator: str, target: object) -> None:
    expected = {"path": "$", "operator": operator, "value": target}
    assert score_case("custom", value, expected)[0] is False


def test_oversized_integer_in_dataset_is_rejected(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    big = "9" * 5000
    dataset.write_text(
        f'{{"id": "a", "input": {big}, "expected": 1, "scoring": "exact"}}\n', encoding="utf-8"
    )
    with pytest.raises(EvalInputError):
        load_dataset(dataset)


@pytest.mark.parametrize(
    "body",
    [
        "print('{\"output\": ' + '9' * 5000 + '}')\n",
        "import sys\nsys.stdout.buffer.write(b'\\xff\\xfe')\n",
    ],
)
def test_unparseable_runner_output_is_a_failed_run_not_a_crash(tmp_path: Path, body: str) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(
        '{"id": "a", "input": 1, "expected": 1, "scoring": "exact"}\n', encoding="utf-8"
    )
    command = _runner_command(tmp_path / "odd.py", body)

    exit_code, summary = run_evaluation(dataset, command, tmp_path, 1.0, 30)

    assert exit_code == 1
    assert summary["runner_failure"]["code"] == "runner_output_not_json"
