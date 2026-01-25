from unittest.mock import MagicMock, patch

import pytest
from services.external_interface import ExternalInterfaceService


class TestExternalInterfaceService:
    @patch("services.external_interface.dgm_engine")
    def test_get_public_chronicle_success(self, mock_dgm) -> None:
        # Setup mock history
        mock_entry = MagicMock()
        mock_entry.decree_status = "APPROVED"
        mock_entry.generation = 1
        mock_entry.modifications = ["Update A", "Update B"]
        mock_entry.trinity_score = 0.95
        mock_entry.timestamp = "2026-01-13T10:00:00"

        mock_dgm.chronicle.get_history.return_value = [mock_entry]

        service = ExternalInterfaceService()
        result = service.get_public_chronicle()

        assert len(result) == 1
        assert result[0]["iteration"] == 1
        assert result[0]["reliability_index"] == 0.95
        assert "Update A" in result[0]["summary"]

    @patch("services.external_interface.dgm_engine")
    def test_get_public_chronicle_sanitization(self, mock_dgm) -> None:
        # Setup mock history with approved and unapproved entries
        approved_entry = MagicMock()
        approved_entry.decree_status = "APPROVED"
        approved_entry.generation = 1
        approved_entry.modifications = ["A"]

        pending_entry = MagicMock()
        pending_entry.decree_status = "PENDING"
        pending_entry.generation = 2

        mock_dgm.chronicle.get_history.return_value = [approved_entry, pending_entry]

        service = ExternalInterfaceService()
        result = service.get_public_chronicle()

        assert len(result) == 1
        assert result[0]["iteration"] == 1

    @patch("services.external_interface.sentry")
    def test_get_public_status_operational(self, mock_sentry) -> None:
        mock_sentry.is_locked.return_value = False
        service = ExternalInterfaceService()
        result = service.get_public_status()
        assert result["status"] == "OPERATIONAL"

    @patch("services.external_interface.sentry")
    def test_get_public_status_maintenance(self, mock_sentry) -> None:
        mock_sentry.is_locked.return_value = True
        service = ExternalInterfaceService()
        result = service.get_public_status()
        assert result["status"] == "MAINTENANCE"
