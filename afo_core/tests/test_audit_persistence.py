# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import os
import socket
import sys
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AFO.domain.audit.trail import AuditTrail
from AFO.utils.history import Historian


def is_postgres_available() -> None:
    """Check if PostgreSQL is reachable on port 15432."""
    try:
        sock = socket.create_connection(("127.0.0.1", 15432), timeout=1)
        sock.close()
        return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


@pytest.mark.integration
@pytest.mark.skipif(not is_postgres_available(), reason="PostgreSQL not running on port 15432")
@pytest.mark.asyncio
async def test_historian_persistence():
    """Verify that Historian.record persists to AuditTrail."""
    query = "Test Audit Query"
    trinity_score = 95.5
    status = "AUTO_RUN"
    metadata = {"test": "metadata", "risk_score": 0.05}

    # Record the decision
    record = await Historian.record(query, trinity_score, status, metadata)

    assert record["query"] == query
    assert record["trinity_score"] == trinity_score
    assert record["status"] == status

    # Verify persistence in AuditTrail
    audit = AuditTrail()
    recent = await audit.get_recent(limit=5)

    # Check if our record is in the recent list
    # The score is normalized in AuditTrail (95.5 -> 0.955)
    found = False
    for r in recent:
        if r.action == status and abs(r.trinity_score - (trinity_score / 100.0)) < 0.01:
            found = True
            break

    assert found, "Record not found in AuditTrail PostgreSQL persistence"
    print("\n✅ Historian Persistence Verified!")


if __name__ == "__main__":
    asyncio.run(test_historian_persistence())
