"""Tests for VaultManager Phase 23 - Operation Hardening.

Tests seal/unseal functionality, encryption, and audit logging.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestVaultManagerBasic:
    """Basic VaultManager functionality tests."""

    def test_vault_init(self) -> None:
        """Test VaultManager initialization."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        assert vm.mode == "env"
        assert not vm.is_sealed()
        assert vm.secrets == {}

    def test_set_and_get_secret(self) -> None:
        """Test setting and getting secrets."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        assert vm.set_secret("TEST_KEY", "test_value")
        assert vm.get_secret("TEST_KEY") == "test_value"

    def test_rotate_secret(self) -> None:
        """Test secret rotation."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.set_secret("ROTATE_KEY", "old_value")
        assert vm.rotate_secret("ROTATE_KEY", "new_value")
        assert vm.get_secret("ROTATE_KEY") == "new_value"

    def test_delete_secret(self) -> None:
        """Test secret deletion."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.set_secret("DELETE_KEY", "value")
        assert vm.delete_secret("DELETE_KEY")
        assert vm.get_secret("DELETE_KEY") is None

    def test_get_status(self) -> None:
        """Test status retrieval."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        status = vm.get_status()
        assert status["mode"] == "env"
        assert status["sealed"] is False
        assert "secrets_count" in status


class TestVaultManagerSealUnseal:
    """Seal/Unseal functionality tests."""

    def test_seal_vault_empty(self) -> None:
        """Test sealing vault with no secrets."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        assert vm.seal_vault(persist=False)
        assert vm.is_sealed()
        assert vm.mode == "sealed"

    def test_seal_vault_with_secrets(self) -> None:
        """Test sealing vault with secrets."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.set_secret("SECRET1", "value1")
        vm.set_secret("SECRET2", "value2")

        assert vm.seal_vault(persist=False)
        assert vm.is_sealed()
        # Secrets should be cleared from memory
        assert len(vm.secrets) == 0

    def test_get_secret_when_sealed(self) -> None:
        """Test that getting secrets fails when sealed."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.set_secret("KEY", "value")
        vm.seal_vault(persist=False)

        # Should return None when sealed
        assert vm.get_secret("KEY") is None

    def test_set_secret_when_sealed(self) -> None:
        """Test that setting secrets fails when sealed."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.seal_vault(persist=False)

        # Should fail when sealed
        assert not vm.set_secret("KEY", "value")

    def test_unseal_vault(self) -> None:
        """Test unsealing vault."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.seal_vault(persist=False)
        assert vm.is_sealed()

        assert vm.unseal_vault()
        assert not vm.is_sealed()
        assert vm.mode == "env"

    def test_double_seal_fails(self) -> None:
        """Test that sealing twice fails."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        assert vm.seal_vault(persist=False)
        assert not vm.seal_vault(persist=False)  # Should fail

    def test_generate_seal_key(self) -> None:
        """Test seal key generation."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        key = vm.generate_seal_key()
        assert key is not None
        assert len(key) > 0


class TestVaultManagerEncryption:
    """Encryption functionality tests."""

    def test_encryption_with_key(self) -> None:
        """Test encryption with provided key."""
        from AFO.security.vault_manager import VaultManager

        # Generate a valid key
        vm = VaultManager(mode="env")
        seal_key = vm.generate_seal_key()

        # Create new vault with key
        with patch.dict(os.environ, {"VAULT_SEAL_KEY": seal_key}):
            vm2 = VaultManager(mode="env")
            vm2.set_secret("ENCRYPTED_KEY", "secret_value")
            assert vm2.seal_vault(persist=False)
            assert vm2.is_sealed()

    def test_seal_unseal_preserves_secrets(self) -> None:
        """Test that seal/unseal preserves secrets."""
        from AFO.security.vault_manager import VaultManager

        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_file = Path(tmpdir) / "sealed.enc"
            audit_file = Path(tmpdir) / "audit.jsonl"

            with patch.dict(
                os.environ,
                {
                    "VAULT_SEALED_SECRETS_FILE": str(secrets_file),
                    "VAULT_AUDIT_FILE": str(audit_file),
                },
            ):
                vm = VaultManager(mode="env")
                seal_key = vm.generate_seal_key()
                vm._init_encryption(seal_key)

                # Set secrets
                vm.set_secret("KEY1", "value1")
                vm.set_secret("KEY2", "value2")

                # Seal
                assert vm.seal_vault(persist=True)
                assert len(vm.secrets) == 0

                # Unseal
                assert vm.unseal_vault(seal_key)
                assert vm.get_secret("KEY1") == "value1"
                assert vm.get_secret("KEY2") == "value2"


class TestVaultManagerAudit:
    """Audit logging tests."""

    def test_audit_log_created(self) -> None:
        """Test that audit entries are created."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.set_secret("AUDIT_KEY", "value")

        audit = vm.get_audit_log(limit=10)
        assert len(audit) > 0
        assert audit[0]["action"] == "SET"
        assert audit[0]["key"] == "AUDIT_KEY"

    def test_audit_log_on_seal(self) -> None:
        """Test audit logging on seal operation."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.seal_vault(persist=False)

        audit = vm.get_audit_log(limit=10)
        seal_entries = [e for e in audit if e["action"] == "SEAL"]
        assert len(seal_entries) > 0


class TestVaultManagerBreakGlass:
    """Break-glass emergency protocol tests."""

    def test_break_glass_unseals(self) -> None:
        """Test that break-glass unseals the vault."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.seal_vault(persist=False)
        assert vm.is_sealed()

        vm.break_glass()
        assert not vm.is_sealed()
        assert vm.mode == "env"

    def test_break_glass_audit(self) -> None:
        """Test that break-glass creates audit entry."""
        from AFO.security.vault_manager import VaultManager

        vm = VaultManager(mode="env")
        vm.break_glass()

        audit = vm.get_audit_log(limit=10)
        break_glass_entries = [e for e in audit if e["action"] == "BREAK_GLASS"]
        assert len(break_glass_entries) > 0


class TestVaultManagerZeroTrust:
    """Zero Trust policy tests."""

    def test_root_access_denied_without_flag(self) -> None:
        """Test ROOT_ key access is denied without flag."""
        from AFO.security.vault_manager import VaultManager

        # Ensure AFO_ROOT_ACCESS is not set
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AFO_ROOT_ACCESS", None)
            vm = VaultManager(mode="env")
            vm.set_secret("ROOT_SECRET", "sensitive")

            # Should be denied
            assert vm.get_secret("ROOT_SECRET") is None

    def test_root_access_allowed_with_flag(self) -> None:
        """Test ROOT_ key access is allowed with flag."""
        from AFO.security.vault_manager import VaultManager

        with patch.dict(os.environ, {"AFO_ROOT_ACCESS": "1"}):
            vm = VaultManager(mode="env")
            vm.set_secret("ROOT_SECRET", "sensitive")

            # Should be allowed
            assert vm.get_secret("ROOT_SECRET") == "sensitive"
