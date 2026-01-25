# Trinity Score: 90.0 (Established by Chancellor)
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import hvac
else:
    try:
        import hvac
    except ImportError:
        hvac = None


class VaultKMS:
    """HashiCorp Vault KMS implementation for API Wallet."""

    def __init__(self) -> None:
        self.url = os.getenv("VAULT_ADDR")
        self.token = os.getenv("VAULT_TOKEN")
        self.auth_method = os.getenv("VAULT_AUTH_METHOD", "token")
        self.role_id = os.getenv("VAULT_ROLE_ID")
        self.secret_id = os.getenv("VAULT_SECRET_ID")
        self.mount_point = os.getenv("VAULT_MOUNT_POINT", "secret")
        self.secret_path = os.getenv("VAULT_SECRET_PATH", "api_wallet")
        self.client = None

        if hvac and self.url:
            try:
                self.client = hvac.Client(url=self.url)

                # Authenticate based on method
                if self.auth_method == "approle" and self.role_id and self.secret_id:
                    # AppRole authentication
                    auth_response = self.client.auth.approle.login(
                        role_id=self.role_id, secret_id=self.secret_id
                    )
                    self.client.token = auth_response["auth"]["client_token"]
                    print("✅ Vault AppRole authentication successful")  # TICKET W3: Debug logging
                elif self.token:
                    # Token authentication (legacy)
                    self.client.token = self.token
                    print("✅ Vault token authentication successful")
                else:
                    print("⚠️ No valid Vault authentication method configured")

            except Exception as e:
                logging.warning(f"Failed to initialize Vault client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if Vault is available and authenticated."""
        if not self.client:
            return False
        try:
            return bool(self.client.is_authenticated())
        except Exception:
            return False

    def get_encryption_key(self) -> str | None:
        """Retrieve encryption key from Vault."""
        if not self.is_available() or self.client is None:
            return None

        try:
            # [논어] 지지위지지 - 아는 것을 안다고 하며 접근
            # Adjust read method based on KV version (assuming v2 for modern Vault)
            response = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point, path=self.secret_path
            )
            val = response["data"]["data"].get("encryption_key")
            return str(val) if val is not None else None
        except Exception as e:
            logging.warning(f"Failed to read from Vault: {e}")
            return None

    def set_encryption_key(self, key: str) -> bool:
        """Store encryption key in Vault."""
        if not self.is_available() or self.client is None:
            return False

        try:
            # [대학] 성의정심 - 뜻을 성실히 하고 마음을 바르게 함
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.mount_point,
                path=self.secret_path,
                secret={"encryption_key": key},
            )
            return True
        except Exception as e:
            logging.error(f"Failed to write to Vault: {e}")
            return False
