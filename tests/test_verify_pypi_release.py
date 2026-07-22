"""Unit tests for scripts/release/verify-pypi-release.py.

Network is fully mocked. These pin the 4.0.1 failure mode: version JSON is
already live while the integrity API still 404s — provenance must be *retried*,
not fail on the first miss.
"""

from __future__ import annotations

import importlib.util
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release" / "verify-pypi-release.py"


def _load_verify() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_pypi_release", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def verify() -> ModuleType:
    return _load_verify()


def _meta(version: str = "4.0.1") -> dict[str, Any]:
    return {
        "info": {"version": version, "yanked": False},
        "urls": [
            {
                "filename": f"hyodo-{version}-py3-none-any.whl",
                "packagetype": "bdist_wheel",
                "size": 1,
                "digests": {"sha256": "abc"},
                "url": f"https://files.pythonhosted.org/packages/xx/hyodo-{version}-py3-none-any.whl",
                "yanked": False,
            },
            {
                "filename": f"hyodo-{version}.tar.gz",
                "packagetype": "sdist",
                "size": 2,
                "digests": {"sha256": "def"},
                "url": f"https://files.pythonhosted.org/packages/xx/hyodo-{version}.tar.gz",
                "yanked": False,
            },
        ],
    }


def test_require_files_ok(verify: ModuleType) -> None:
    urls = verify.require_files(_meta())
    assert len(urls) == 2


def test_require_files_rejects_missing_wheel(verify: ModuleType) -> None:
    meta = _meta()
    meta["urls"] = [u for u in meta["urls"] if u["packagetype"] == "sdist"]
    with pytest.raises(SystemExit, match="wheel"):
        verify.require_files(meta)


def test_provenance_from_version_json(verify: ModuleType) -> None:
    meta = _meta()
    meta["urls"][0]["provenance"] = {"attestation": True}
    assert verify.provenance_from_version_json(meta, meta["urls"][0]["filename"]) == {
        "attestation": True
    }
    assert verify.provenance_from_version_json(meta, meta["urls"][1]["filename"]) is None


def test_wait_for_provenance_retries_then_succeeds(
    verify: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Integrity 404 twice, then present — must not SystemExit."""
    calls: list[str] = []
    sleeps: list[float] = []

    def fake_version_payload(version: str) -> dict[str, Any]:
        return _meta(version)

    def fake_integrity(version: str, filename: str):
        calls.append(filename)
        # First full round (2 files) + first file of second round = 404, then OK.
        if len(calls) <= 3:
            return None, "http_404"
        return {"attestation_bundles": []}, None

    monkeypatch.setattr(verify, "version_payload", fake_version_payload)
    monkeypatch.setattr(verify, "fetch_integrity_provenance", fake_integrity)
    monkeypatch.setattr(verify.time, "sleep", lambda s: sleeps.append(s))

    names = [u["filename"] for u in _meta()["urls"]]
    verify.wait_for_provenance("4.0.1", names, retries=5, sleep_seconds=0.01)
    assert len(calls) >= 4
    assert sleeps  # retried at least once


def test_wait_for_provenance_exhausts_retries(
    verify: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verify, "version_payload", lambda v: _meta(v))
    monkeypatch.setattr(
        verify,
        "fetch_integrity_provenance",
        lambda v, f: (None, "http_404"),
    )
    monkeypatch.setattr(verify.time, "sleep", lambda s: None)

    names = [u["filename"] for u in _meta()["urls"]]
    with pytest.raises(SystemExit, match="still missing after 3 polls"):
        verify.wait_for_provenance("4.0.1", names, retries=3, sleep_seconds=0.0)


def test_fetch_integrity_provenance_404(
    verify: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(url: str, timeout: int = 30):
        raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]

    monkeypatch.setattr(verify, "fetch_json", boom)
    payload, kind = verify.fetch_integrity_provenance("4.0.1", "hyodo-4.0.1.tar.gz")
    assert payload is None
    assert kind == "http_404"


def test_wait_for_version_retries(verify: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"n": 0}

    def flaky(version: str) -> dict[str, Any]:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise urllib.error.URLError("temporary")
        return _meta(version)

    monkeypatch.setattr(verify, "version_payload", flaky)
    monkeypatch.setattr(verify.time, "sleep", lambda s: None)
    meta = verify.wait_for_version("4.0.1", retries=5, sleep_seconds=0.0)
    assert meta["info"]["version"] == "4.0.1"
    assert attempts["n"] == 3


def test_main_wires_provenance_retry(verify: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() must call wait_for_provenance, not the one-shot check_provenance."""
    called: dict[str, Any] = {}

    monkeypatch.setattr(verify, "wait_for_version", lambda *a, **k: _meta())
    monkeypatch.setattr(verify, "require_files", lambda m: m["urls"])

    def capture_wait(version, filenames, retries, sleep_seconds):
        called["version"] = version
        called["filenames"] = filenames
        called["retries"] = retries
        called["sleep"] = sleep_seconds

    monkeypatch.setattr(verify, "wait_for_provenance", capture_wait)
    # one-shot must NOT be the path used by main
    monkeypatch.setattr(
        verify,
        "check_provenance",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("one-shot used")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify-pypi-release.py",
            "--version",
            "4.0.1",
            "--require-provenance",
            "--retries",
            "7",
            "--sleep-seconds",
            "0.5",
            "--provenance-retries",
            "9",
        ],
    )
    assert verify.main() == 0
    assert called["version"] == "4.0.1"
    assert called["retries"] == 9
    assert any(n.endswith(".whl") for n in called["filenames"])
    assert any(n.endswith(".tar.gz") for n in called["filenames"])


def test_install_smoke_never_imports_from_the_callers_cwd(
    verify: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The smoke check must read the installed wheel, not whatever is next to us.

    ``python -c`` puts the current directory first on sys.path. Running the verifier
    from a HyoDo checkout therefore imported the local source tree and reported the
    working copy's version as if it were the published one — a release verifier
    measuring the code in hand instead of the code being shipped.
    """
    # A decoy package in the caller's cwd, exactly like running from a checkout.
    decoy = tmp_path / "cwd"
    (decoy / "hyodo").mkdir(parents=True)
    (decoy / "hyodo" / "__init__.py").write_text('__version__ = "0.0.0-decoy"\n', encoding="utf-8")
    monkeypatch.chdir(decoy)

    seen_cwds: list[Any] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> None:
        return None

    def fake_check_output(cmd: list[str], **kwargs: Any) -> str:
        cwd = kwargs.get("cwd")
        seen_cwds.append(cwd)
        if cmd[-1] == "--version":
            return "HyoDo v9.9.9 - test\n"
        # Stand in for the interpreter honouring sys.path: a cwd holding a `hyodo`
        # package wins over site-packages, which is exactly the bug.
        effective = Path(cwd) if cwd is not None else Path.cwd()
        return "0.0.0-decoy\n" if (effective / "hyodo").exists() else "9.9.9\n"

    monkeypatch.setattr(verify.subprocess, "run", fake_run)
    monkeypatch.setattr(verify.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(verify, "version_payload", lambda _v: {"urls": []})

    verify.install_smoke("9.9.9", retries=1, sleep_seconds=0)

    assert seen_cwds, "smoke ran no verification subprocesses"
    for cwd in seen_cwds:
        assert cwd is not None, "verification subprocess inherited the caller's cwd"
        assert not (Path(cwd) / "hyodo").exists(), "verification cwd can shadow the wheel"
