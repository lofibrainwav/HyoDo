"""Frozen Graph v2 join fixtures validate the independent SCC oracle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hyodo.tarjan_scc import tarjan_scc

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "graph-v2-join"


def _fixture_paths() -> list[Path]:
    return sorted(FIXTURE_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _fixture_paths(), ids=lambda path: path.stem)
def test_frozen_join_fixture(path: Path) -> None:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    edges = [(edge["child"], edge["parent"]) for edge in fixture["edges"]]
    result = tarjan_scc(fixture["nodes"], edges)

    expected = fixture["expected"]
    assert result.acyclic is expected["acyclic"]
    assert result.components == expected["components"]
    assert sorted({cycle["reason"] for cycle in result.cycles}) == sorted(expected["cycle_reasons"])
