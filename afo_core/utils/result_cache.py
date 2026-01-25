"""
AFO Kingdom Result Caching Utility
Trinity Score: 眞 (Truth) - Efficiency & Consistency
Author: AFO Kingdom Development Team
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

# Use structured logger if available
try:
    from AFO.utils.structured_logger import StructuredLogger

    logger = StructuredLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class ResultCache:
    """
    File-based result caching mechanism.
    Uses SHA-256 hashing of inputs to determine cache keys.
    """

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, file_path: str, params: dict[str, Any]) -> str:
        """Compute SHA-256 hash of file content + parameters"""
        hasher = hashlib.sha256()

        # Hash file content
        path = Path(file_path)
        if path.is_dir():
            # Hash all files in directory deterministically
            for child in sorted(path.glob("**/*")):
                if child.is_file():
                    with open(child, "rb") as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
        elif path.exists():
            # Read in chunks to handle large files
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        else:
            # If file doesn't exist, hash the string path
            hasher.update(str(path).encode("utf-8"))

        # Hash parameters (sorted keys for consistency)
        param_str = json.dumps(params, sort_keys=True)
        hasher.update(param_str.encode("utf-8"))

        return hasher.hexdigest()

    def get(self, file_path: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Retrieve result from cache if valid"""
        cache_key = self._compute_hash(file_path, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                    if hasattr(logger, "info") and isinstance(logger, StructuredLogger):
                        logger.info(
                            "Cache Hit",
                            context={"cache_key": cache_key, "file": file_path},
                        )
                    else:
                        logger.info(f"Cache Hit: {cache_key}")
                    return data
            except json.JSONDecodeError:
                logger.warning(f"Corrupted cache file: {cache_file}")
                return None

        return None

    def set(self, file_path: str, params: dict[str, Any], result: dict[str, Any]) -> None:
        """Save result to cache"""
        cache_key = self._compute_hash(file_path, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            if hasattr(logger, "info") and isinstance(logger, StructuredLogger):
                logger.info("Cache Saved", context={"cache_key": cache_key, "file": file_path})
            else:
                logger.info(f"Cache Saved: {cache_key}")

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
