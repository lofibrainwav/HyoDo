from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Wallet Models (domain/wallet/models.py)

Data models for the API Wallet system.
"""


class KeyMetadata(BaseModel):
    """Metadata for a single API key"""

    id: int | None = None
    name: str = Field(..., description="Unique key name")
    encrypted_key: str = Field(..., description="Encrypted API key")
    key_hash: str = Field(..., description="SHA-256 hash for audit")
    key_type: str = Field(default="api", description="Type of key")
    read_only: bool = Field(default=True)
    service: str = Field(default="")
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime | None = None
    access_count: int = 0


class WalletSummary(BaseModel):
    """Summary of wallet state"""

    total_keys: int
    active_services: list[str]
    total_token_usage: dict[str, int]
    last_backup: datetime | None = None
