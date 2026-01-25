from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from AFO.config.settings import get_settings

from .crypto import Fernet, get_cipher
from .kms import VAULT_AVAILABLE, VaultKMS
from .models import WalletSummary

# Trinity Score: 92.0 (Established by Chancellor)
"""
AFO Wallet Core (domain/wallet/core.py)

Main logic for the API Wallet system.
TICKET-104: Added Vault integration with use_vault and encryption_key properties.
"""


logger = logging.getLogger(__name__)


class APIWallet:
    """
    API Wallet - 암호화 키 관리 시스템 (Encrypted Key Management System)

    Attributes:
        encryption_key: The encryption key used for encrypting API keys
        use_vault: Whether Vault KMS is being used for key management
    """

    def __init__(
        self,
        encryption_key: str | None = None,
        db_connection: Any | None = None,
        use_vault: bool | None = None,
    ) -> None:
        # Vault integration (TICKET-104)
        self.use_vault = False
        vault_key: str | None = None

        if use_vault and VAULT_AVAILABLE and os.getenv("VAULT_ENABLED", "").lower() == "true":
            try:
                vault = VaultKMS()
                if vault.is_available():
                    vault_key = vault.get_encryption_key()
                    if vault_key:
                        self.use_vault = True
                        logger.info("Vault KMS enabled for encryption key management")
            except Exception as e:
                logger.warning(f"Vault initialization failed, falling back to default: {e}")
                self.use_vault = False

        # Encryption Key initialization (priority: vault > param > settings > generate)
        if vault_key:
            encryption_key = vault_key
        elif not encryption_key:
            encryption_key = self._get_encryption_key_from_settings()

        if not encryption_key:
            encryption_key = self._generate_default_key()

        # Store encryption key for property access (TICKET-104)
        self.encryption_key = encryption_key
        self.cipher = get_cipher(encryption_key)

        # Paths
        pkg_root = Path(__file__).parent.parent.parent
        self.storage_path = pkg_root / "data" / "api_wallet.json"
        self.audit_log_path = pkg_root / "logs" / "api_wallet_audit.log"

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Database (TICKET-104 Phase 2)
        self.db = db_connection
        self.use_db = db_connection is not None

        if self.use_db:
            self._ensure_db_table()
        else:
            self._ensure_storage_file()

    def _get_encryption_key_from_settings(self) -> str | None:
        try:
            return cast("str | None", get_settings().API_WALLET_ENCRYPTION_KEY)
        except Exception:  # nosec
            return None

    def _generate_default_key(self) -> str:
        return str(Fernet.generate_key().decode())

    def _ensure_storage_file(self) -> None:
        if not self.storage_path.exists():
            self._save_storage({"keys": []})

    # ============================================================
    # Database Support (TICKET-104 Phase 2)
    # ============================================================

    def _get_db_cursor(self) -> Any:
        """Get database cursor, handling connection pool if present"""
        if hasattr(self.db, "getconn"):
            conn = self.db.getconn()
            return conn.cursor()
        return self.db.cursor()

    def _ensure_db_table(self) -> None:
        """Ensure api_keys table exists in database"""
        with self._get_db_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    key_type VARCHAR(50) DEFAULT 'api',
                    read_only BOOLEAN DEFAULT TRUE,
                    service VARCHAR(255) DEFAULT '',
                    description TEXT DEFAULT '',
                    key_hash VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """
            )

    def _load_storage(self) -> dict[str, Any]:
        try:
            if not self.storage_path.exists():
                return {"keys": []}
            return cast("dict[str, Any]", json.loads(self.storage_path.read_text()))
        except Exception:  # nosec
            return {"keys": []}

    def _save_storage(self, data: dict[str, Any]) -> None:
        self.storage_path.write_text(json.dumps(data, indent=2))

    def _audit_log(self, action: str, key_name: str, details: str = "") -> None:
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} | {action} | {key_name} | {details}\n"
            with open(self.audit_log_path, "a") as f:
                f.write(log_entry)
        except Exception:  # nosec
            pass

    def _hash_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def add(
        self,
        name: str,
        api_key: str,
        key_type: str = "api",
        read_only: bool = True,
        service: str = "",
        description: str = "",
    ) -> int:
        """Add a new API key to wallet"""
        try:
            encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
            key_hash = self._hash_key(api_key)

            # Database path (TICKET-104 Phase 2)
            if self.use_db:
                return self._add_to_db(
                    name,
                    encrypted_key,
                    key_type,
                    read_only,
                    service,
                    description,
                    key_hash,
                )

            # File storage path
            storage = self._load_storage()
            if any(k["name"] == name for k in storage["keys"]):
                raise ValueError(f"Key with name '{name}' already exists")

            key_id = len(storage["keys"]) + 1
            key_data = {
                "id": key_id,
                "name": name,
                "encrypted_key": encrypted_key,
                "key_type": key_type,
                "read_only": read_only,
                "service": service,
                "description": description,
                "key_hash": key_hash,
                "created_at": datetime.now().isoformat(),
                "last_accessed": None,
                "access_count": 0,
            }

            storage["keys"].append(key_data)
            self._save_storage(storage)
            self._audit_log("ADD", name, f"type={key_type}, service={service}")
            return int(key_id)
        except Exception as e:
            self._audit_log("ADD_FAILED", name, str(e))
            raise

    def _add_to_db(
        self,
        name: str,
        encrypted_key: str,
        key_type: str,
        read_only: bool,
        service: str,
        description: str,
        key_hash: str,
    ) -> int:
        """Add key to database with transaction support"""
        try:
            with self._get_db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO api_keys (name, encrypted_key, key_type, read_only, service, description, key_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        name,
                        encrypted_key,
                        key_type,
                        read_only,
                        service,
                        description,
                        key_hash,
                    ),
                )
                result = cursor.fetchone()
                key_id = result[0] if isinstance(result, (list, tuple)) else result["id"]
                self._audit_log("ADD", name, f"type={key_type}, service={service}")
                return int(key_id)
        except Exception as e:
            if hasattr(self.db, "rollback"):
                self.db.rollback()
            self._audit_log("ADD_FAILED", name, str(e))
            raise

    def get(self, name: str, decrypt: bool = True) -> str | None:
        """Retrieve an API key by name"""
        # Database path (TICKET-104 Phase 2)
        if self.use_db:
            return self._get_from_db(name, decrypt)

        # File storage path
        storage = self._load_storage()
        for key in storage["keys"]:
            if key["name"] == name:
                self._update_access_stats(name)
                if decrypt:
                    return cast(
                        "str",
                        self.cipher.decrypt(key["encrypted_key"].encode()).decode(),
                    )
                return cast("str", key["encrypted_key"])
        return None

    def _get_from_db(self, name: str, decrypt: bool = True) -> str | None:
        """Get key from database"""
        with self._get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM api_keys WHERE name = %s",
                (name,),
            )
            row = cursor.fetchone()
            if row:
                self._update_access_stats(name)
                encrypted_key = row["encrypted_key"] if isinstance(row, dict) else row[2]
                if decrypt:
                    return cast("str", self.cipher.decrypt(encrypted_key.encode()).decode())
                return cast("str", encrypted_key)
        return None

    def list_keys(self) -> list[dict[str, Any]]:
        """List all keys in wallet (without decrypted values)"""
        # Database path (TICKET-104 Phase 2)
        if self.use_db:
            return self._list_keys_from_db()

        # File storage path
        storage = self._load_storage()
        return [{k: v for k, v in key.items() if k != "encrypted_key"} for key in storage["keys"]]

    def _list_keys_from_db(self) -> list[dict[str, Any]]:
        """List all keys from database"""
        with self._get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM api_keys")
            rows = cursor.fetchall()
            return [
                {
                    k: v
                    for k, v in (row if isinstance(row, dict) else dict(row)).items()
                    if k != "encrypted_key"
                }
                for row in rows
            ]

    def delete(self, name: str) -> bool:
        """Delete a key from wallet"""
        # Database path (TICKET-104 Phase 2)
        if self.use_db:
            return self._delete_from_db(name)

        # File storage path
        storage = self._load_storage()
        original_count = len(storage["keys"])
        storage["keys"] = [k for k in storage["keys"] if k["name"] != name]

        if len(storage["keys"]) < original_count:
            self._save_storage(storage)
            self._audit_log("DELETE", name)
            return True
        return False

    def _delete_from_db(self, name: str) -> bool:
        """Delete key from database"""
        with self._get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM api_keys WHERE name = %s",
                (name,),
            )
            if cursor.rowcount > 0:
                self._audit_log("DELETE", name)
                return True
        return False

    def _update_access_stats(self, name: str) -> None:
        """Update access stats in local storage, database, and Redis"""
        try:
            # Database path (TICKET-104 Phase 2)
            if self.use_db:
                self._update_access_stats_db(name)
                return

            # File storage path
            storage = self._load_storage()
            for key in storage["keys"]:
                if key["name"] == name:
                    key["last_accessed"] = datetime.now().isoformat()
                    key["access_count"] = key.get("access_count", 0) + 1
                    break
            self._save_storage(storage)
            # Redis sync logic could go here if needed, keeping it simple for now
        except Exception:  # nosec
            pass

    def _update_access_stats_db(self, name: str) -> None:
        """Update access stats in database"""
        with self._get_db_cursor() as cursor:
            cursor.execute(
                """
                UPDATE api_keys
                SET last_accessed = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE name = %s
                """,
                (name,),
            )

    def get_summary(self) -> WalletSummary:
        """Get wallet state summary"""
        keys = self.list_keys()
        services = list({k.get("service") for k in keys if k.get("service")})
        return WalletSummary(
            total_keys=len(keys),
            active_services=services,
            total_token_usage={},
            last_backup=None,
        )
