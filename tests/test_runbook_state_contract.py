"""Offline runbook examples; passing these tests grants no host authority."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "runbook"
SCHEMA = json.loads((FIXTURES / "state.schema.json").read_text())
EXAMPLES = json.loads((FIXTURES / "state-cases.json").read_text())
CASES = EXAMPLES["cases"]
VALIDATOR = Draft202012Validator(SCHEMA)
RUNBOOK = ROOT / "outputs" / "hyodo-unified-doctrine-orchestration-runbook.md"


def test_schema_is_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_adversarial_state_examples(case: dict) -> None:
    expected = EXAMPLES["base"] | case["overrides"]
    record = copy.deepcopy(expected)
    errors = list(VALIDATOR.iter_errors(record))
    assert (not errors) is case["valid"], [error.message for error in errors]
    # Validation must not normalize a missing observation or generate authority.
    assert record == expected


@pytest.mark.parametrize("field", SCHEMA["required"])
def test_omitted_axes_and_references_are_not_defaulted(field: str) -> None:
    record = dict(EXAMPLES["base"])
    del record[field]
    assert not VALIDATOR.is_valid(record)


def test_dictionary_and_schema_agree() -> None:
    document = RUNBOOK.read_text()
    for field, definition in SCHEMA["properties"].items():
        if "enum" not in definition:
            continue
        row = next(line for line in document.splitlines() if f"`{field}`" in line)
        values = row.split("|")[2].strip().split(", ")
        assert values == [value for value in definition["enum"] if value is not None]


def test_local_runbook_links_resolve() -> None:
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", RUNBOOK.read_text())
    assert links, "The runbook must reference existing evidence primitives."
    for link in links:
        assert not link.startswith(("https:", "http:")), "Inventory uses local source evidence."
        assert (RUNBOOK.parent / link).is_file(), link


@pytest.mark.parametrize("index", range(len(SCHEMA["allOf"])))
def test_each_guard_has_a_negative_control(index: int) -> None:
    """A removed constraint must let at least one attack through."""
    weakened = copy.deepcopy(SCHEMA)
    del weakened["allOf"][index]
    mutant = Draft202012Validator(weakened)
    attacks = [EXAMPLES["base"] | case["overrides"] for case in CASES if not case["valid"]]
    assert any(mutant.is_valid(attack) for attack in attacks), f"Unprotected guard: {index}"


@pytest.mark.parametrize(
    "untrusted_ref", ["fixture:expired", "fixture:revoked", "fixture:wrong-owner"]
)
def test_schema_acceptance_is_not_delegation_verification(untrusted_ref: str) -> None:
    """Expose the trust boundary: shape checks cannot authenticate a host grant."""
    record = EXAMPLES["base"] | {
        "resolution_state": "RESOLVED",
        "lane_state": "READY",
        "disposition": "WITHIN_AUTHORITY",
        "authority_ref": untrusted_ref,
    }
    assert VALIDATOR.is_valid(record)
