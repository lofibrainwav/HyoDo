"""Independent P0 cross-check suite for hyodo eval.

Ported from a separately written repair candidate (40 cases across the eval,
inspect and cross-lane files) so two independent implementations are held to
the same observable contract. Runs against the real modules; nothing is stubbed
unless a test says so.
"""

import hashlib
import json
import shlex
import sys
from pathlib import Path

import pytest

from hyodo import eval as ev


def test_eval_binds_parsed_bytes_to_digest(tmp_path, monkeypatch):
    dataset = tmp_path / "golden.jsonl"
    old = b'{"id":"case","input":1,"expected":1,"scoring":"exact"}\n'
    new = old.replace(b'"expected":1', b'"expected":2')
    dataset.write_bytes(old)
    runner = tmp_path / "runner.py"
    runner.write_text(
        'import json,sys\nprint(json.dumps({"output":json.load(sys.stdin)["input"]}))\n'
    )
    original_text, original_bytes = Path.read_text, Path.read_bytes
    changed = False

    def mutate(path):
        nonlocal changed
        if path == dataset and not changed:
            changed = True
            path.write_bytes(new)

    def read_text(path, *a, **kw):
        out = original_text(path, *a, **kw)
        mutate(path)
        return out

    def read_bytes(path):
        out = original_bytes(path)
        mutate(path)
        return out

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(runner))}"
    code, summary = ev.run_evaluation(dataset, cmd, tmp_path, 1.0, 10)
    assert changed
    assert code == 0
    report = json.loads((tmp_path / summary["result_path"]).read_text())
    assert report["cases"][0]["expected"] == 1
    assert report["dataset_sha256"] == hashlib.sha256(old).hexdigest()


@pytest.mark.parametrize(
    ("actual", "expected"), [(True, 1), (False, 0), ({"x": True}, {"x": 1}), ([0], [False])]
)
def test_exact_json_bool_not_number(actual, expected):
    assert ev.score_case("exact", actual, expected)[0] is False


@pytest.mark.parametrize(
    ("scoring", "actual", "expected"),
    [
        ("contains", [True], 1),
        ("json_path", {"x": True}, {"path": "$.x", "value": 1}),
        ("custom", {"x": True}, {"path": "$.x", "operator": "equals", "value": 1}),
    ],
)
def test_related_bool_number_comparators(scoring, actual, expected):
    assert ev.score_case(scoring, actual, expected)[0] is False


@pytest.mark.parametrize(
    "bad",
    [
        '{"id":"a","input":1,"expected":0,"expected":1,"scoring":"exact"}',
        '{"id":"a","input":1,"expected":NaN,"scoring":"exact"}',
        '{"id":"a","input":1,"expected":1e9999,"scoring":"exact"}',
    ],
)
def test_eval_rejects_ambiguous_or_nonfinite_json(tmp_path, bad):
    p = tmp_path / "golden.jsonl"
    p.write_text(bad + "\n")
    with pytest.raises(ev.EvalInputError):
        ev.load_dataset(p)


@pytest.fixture(autouse=True)
def scratch_provenance(monkeypatch):
    # Other package modules absent; never claim a production or clean Git provenance.
    monkeypatch.setattr(
        ev,
        "_collect_provenance",
        lambda root: {
            "git_head_sha": None,
            "git_dirty": None,
            "git_reason": "isolated exact-file harness",
        },
    )


@pytest.mark.parametrize(
    ("actual", "expected", "passed"),
    [
        (1, 1.0, True),
        (True, True, True),
        ({"a": [1, False]}, {"a": [1.0, False]}, True),
        ("1", 1, False),
        (None, None, True),
        ([1], [1, 2], False),
    ],
)
def test_compat_controls(actual, expected, passed):
    assert ev.score_case("exact", actual, expected)[0] is passed


@pytest.mark.parametrize(
    "payload",
    [
        '{"id":"case","input":0,"expected":0,"scoring":[]}',
        '{"id":"case","input":0,"expected":{"path":"$","operator":[],"value":1},"scoring":"custom"}',
    ],
)
def test_malformed_selector_is_input_error(tmp_path, payload):
    p = tmp_path / "golden.jsonl"
    p.write_text(payload + "\n")
    with pytest.raises(ev.EvalInputError):
        ev.load_dataset(p)


def test_invalid_utf8_is_input_error(tmp_path):
    p = tmp_path / "golden.jsonl"
    p.write_bytes(b"\xff")
    with pytest.raises(ev.EvalInputError):
        ev.load_dataset(p)


@pytest.mark.parametrize(
    "output", ['{"output":1,"output":0}', '{"output":NaN}', '{"output":1e9999}']
)
def test_invalid_runner_json_fails(tmp_path, output):
    p = tmp_path / "golden.jsonl"
    p.write_text('{"id":"case","input":0,"expected":0,"scoring":"exact"}\n')
    script = tmp_path / "runner.py"
    script.write_text("print(" + repr(output) + ")\n")
    code, summary = ev.run_evaluation(p, shlex.join([sys.executable, str(script)]), tmp_path, 1, 10)
    assert code == 1
    assert summary["runner_failure"]["code"] == "runner_output_not_json"


@pytest.mark.parametrize("operator", ["gt", "gte", "lt", "lte"])
def test_bool_not_ordered_as_number(operator):
    # Pick a target that makes Python comparison true for True (integer 1).
    target = 0 if operator in ("gt", "gte") else 2
    assert (
        ev.score_case(
            "custom", {"x": True}, {"path": "$.x", "operator": operator, "value": target}
        )[0]
        is False
    )


def test_custom_array_membership_bool_is_distinct():
    assert (
        ev.score_case("custom", {"x": [True]}, {"path": "$.x", "operator": "contains", "value": 1})[
            0
        ]
        is False
    )


def test_nested_not_equals_bool_number():
    assert (
        ev.score_case(
            "custom", {"x": [True]}, {"path": "$.x", "operator": "not_equals", "value": [1]}
        )[0]
        is True
    )
