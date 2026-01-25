import json
import socket
import subprocess

import pytest

# SSOT Contract Test
# Enforces the 11-Organs Contract and Key Presence physically.

API_URL = "http://127.0.0.1:8010/api/health/comprehensive"


def _is_server_running(host: str = "127.0.0.1", port: int = 8010) -> bool:
    """Check if the API server is running."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((host, port))
            return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


@pytest.mark.external
@pytest.mark.skipif(not _is_server_running(), reason="API server not running on port 8010")
def test_ssot_contract_v2() -> None:
    """
    Verifies that the API response adheres exactly to the Option A SSOT Contract.
    """
    # 1. Fetch Data
    try:
        raw = subprocess.check_output(["curl", "-fsS", API_URL], timeout=5)
        data = json.loads(raw)
    except Exception as e:
        pytest.fail(f"API Unreachable or Invalid JSON: {e}")

    # 2. Key Presence (The Sealed List)
    expected_keys = [
        "organs_v2",
        "security",
        "contract_v2",
        "healthy_organs",
        "total_organs",
        "trinity_breakdown",
        "iccls_gap",
        "sentiment",
    ]
    for key in expected_keys:
        assert key in data, f"Missing SSOT Key: {key}"

    # 3. Organs Count (11)
    organs = data.get("organs_v2") or data.get("organs")
    assert isinstance(organs, dict), "Organs must be a dictionary (V2)"
    assert len(organs) == 11, f"Organs Count Contract Violation: Found {len(organs)}, Expected 11"

    # 4. Security Separation
    assert data.get("security") is not None, "Security Field Missing (Option A Violation)"

    # 5. Breakdown Keys
    breakdown = data.get("trinity_breakdown") or data.get("breakdown")
    assert breakdown, "Breakdown Missing"
    # Basic 5 Pillars
    assert "truth" in breakdown
    assert "goodness" in breakdown
    assert "beauty" in breakdown
    assert "filial_serenity" in breakdown
    assert "eternity" in breakdown

    # 6. Data Types
    assert isinstance(data["iccls_gap"], (float, int)), "ICCLS Gap must be numeric"
    assert isinstance(data["sentiment"], (float, int)), "Sentiment must be numeric"
