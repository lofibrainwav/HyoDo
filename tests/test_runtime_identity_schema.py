"""Cross-repo contract tests for the canonical runtime identity payload."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hyodo.identity import build_runtime_identity

SCHEMA = Path(__file__).parents[1] / "schemas" / "runtime-identity-v1.schema.json"
PIN = Path(__file__).parents[1] / "schemas" / "runtime-identity-v1.pin.json"
ROOT = Path(__file__).parents[1]


def test_generated_identity_matches_v1_schema(tmp_path: Path) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    identity = build_runtime_identity(tmp_path)

    errors = sorted(Draft202012Validator(schema).iter_errors(identity), key=str)

    assert errors == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"unexpected": True}),
        lambda payload: payload["provenance"].update({"validity": "GREEN"}),
        lambda payload: payload["ledger"].update({"events": -1}),
    ],
)
def test_runtime_identity_schema_rejects_protocol_drift(tmp_path: Path, mutator) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    payload = copy.deepcopy(build_runtime_identity(tmp_path))
    mutator(payload)

    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_schema_pin_matches_exact_schema_bytes() -> None:
    """Downstream consumers can verify the schema without importing HyoDo."""
    pin = json.loads(PIN.read_text(encoding="utf-8"))

    assert pin == {
        "algorithm": "sha256",
        "digest": hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
        "schema": "runtime-identity-v1.schema.json",
        "schema_id": "https://hyodo.app/schemas/runtime-identity-v1.schema.json",
        "schema_version": "hyodo.runtime-identity/v1",
    }


def test_schema_pin_references_existing_schema() -> None:
    pin = json.loads(PIN.read_text(encoding="utf-8"))

    assert (PIN.parent / pin["schema"]).resolve() == SCHEMA.resolve()


def test_built_artifacts_contain_exact_runtime_identity_contract_bytes(tmp_path: Path) -> None:
    """Wheel and sdist manifests must carry the checkout-independent contracts."""
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = sorted(dist.glob("hyodo-*.whl"))
    assert len(wheels) == 1
    sdists = sorted(dist.glob("hyodo-*.tar.gz"))
    assert len(sdists) == 1

    expected = {
        "schemas/runtime-identity-v1.schema.json": SCHEMA.read_bytes(),
        "schemas/runtime-identity-v1.pin.json": PIN.read_bytes(),
    }
    with zipfile.ZipFile(wheels[0]) as archive:
        assert set(expected).issubset(archive.namelist())
        for name, content in expected.items():
            assert archive.read(name) == content

    with tarfile.open(sdists[0], "r:gz") as archive:
        for name, content in expected.items():
            member = next(
                member for member in archive.getmembers() if member.name.endswith(f"/{name}")
            )
            extracted = archive.extractfile(member)
            assert extracted is not None
            assert extracted.read() == content
