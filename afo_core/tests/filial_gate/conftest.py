import pytest


@pytest.fixture(autouse=True)
def _afo_silent_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFO_DRY_RUN_DEFAULT", "true")
    monkeypatch.setenv("EXTERNAL_EXPOSURE_ENABLED", "false")
    monkeypatch.setenv("EXTERNAL_API_ENABLED", "false")
    monkeypatch.setenv("PUBLIC_ENDPOINTS_ENABLED", "false")
    monkeypatch.setenv("SILENT_CIVILIZATION_MODE", "true")
