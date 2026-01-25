"""Learning Profile Loader - Boot-time loading of optimization results."""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LearningProfile:
    """Represents a loaded learning profile with metadata."""

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        source_path: str | None = None,
        loaded_at: str | None = None,
        sha256: str | None = None,
        status: str = "disabled",
        errors: list[str] | None = None,
        version: str | None = None,
    ):
        self.data = data or {}
        self.source_path = source_path
        self.loaded_at = loaded_at or datetime.now().isoformat()
        self.sha256 = sha256
        self.status = status  # "applied", "fallback", "disabled"
        self.errors = errors or []
        self.version = version

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.status,
            "loaded_at": self.loaded_at,
            "source_path": self.source_path,
            "sha256": self.sha256,
            "version": self.version,
            "errors": self.errors,
            "has_data": bool(self.data),
        }


class LearningLoader:
    """Loader for learning profiles with comprehensive error handling."""

    def __init__(self) -> None:
        self.profile: LearningProfile = LearningProfile()
        self._loaded = False

    def load_profile(self) -> LearningProfile:
        """Load learning profile from environment variable path."""
        if self._loaded:
            return self.profile

        self._loaded = True

        # Get profile path from environment
        profile_path = os.getenv("AFO_LEARNING_PROFILE_PATH")

        if not profile_path:
            logger.info("AFO_LEARNING_PROFILE_PATH not set - learning profile disabled")
            self.profile = LearningProfile(status="disabled")
            return self.profile

        # Check if file exists
        path = Path(profile_path)
        if not path.exists():
            error_msg = f"Learning profile file not found: {profile_path}"
            logger.warning(error_msg)
            self.profile = LearningProfile(
                status="fallback", errors=[error_msg], source_path=str(path)
            )
            return self.profile

        try:
            # Read and parse JSON
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # Calculate SHA256
            with open(path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

            # Basic validation
            errors = self._validate_profile(data)

            if errors:
                logger.warning(f"Learning profile validation failed: {errors}")
                self.profile = LearningProfile(
                    status="fallback",
                    errors=errors,
                    source_path=str(path),
                    sha256=sha256,
                    loaded_at=datetime.now().isoformat(),
                )
            else:
                # Success
                version = data.get("version") or data.get("profile_version")
                logger.info(f"Learning profile loaded successfully from {profile_path}")
                self.profile = LearningProfile(
                    data=data,
                    source_path=str(path),
                    sha256=sha256,
                    status="applied",
                    version=version,
                    loaded_at=datetime.now().isoformat(),
                )

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in learning profile: {e}"
            logger.error(error_msg)
            self.profile = LearningProfile(
                status="fallback", errors=[error_msg], source_path=str(path)
            )
        except Exception as e:
            error_msg = f"Failed to load learning profile: {e}"
            logger.error(error_msg)
            self.profile = LearningProfile(
                status="fallback", errors=[error_msg], source_path=str(path)
            )

        return self.profile

    def _validate_profile(self, data: Any) -> list[str]:
        """Validate learning profile structure."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Profile must be a JSON object")
            return errors

        # Check for required fields (minimal validation for now)
        # This can be expanded based on specific profile schema requirements

        # Check for known invalid patterns
        if data.get("error"):
            errors.append(f"Profile contains error: {data['error']}")

        return errors

    def get_profile(self) -> LearningProfile:
        """Get the current learning profile."""
        if not self._loaded:
            return self.load_profile()
        return self.profile


# Global loader instance
_loader = LearningLoader()


def get_learning_profile() -> LearningProfile:
    """Get the global learning profile instance."""
    return _loader.get_profile()


def reload_learning_profile() -> LearningProfile:
    """Force reload the learning profile (for testing/debugging)."""
    global _loader
    _loader = LearningLoader()
    return _loader.load_profile()
