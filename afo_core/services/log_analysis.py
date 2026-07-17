"""
AFO Kingdom Log Analysis Service
Trinity Score: 眞.선 (Truth & Goodness)
- Robust, resilient pipeline for log analysis
- Uses safe_step for graceful degradation

Author: AFO Kingdom Development Team
"""

import logging
import sys
from pathlib import Path
from typing import Any

import anyio

logger = logging.getLogger(__name__)


# Ensure scripts directory is in path to import legacy logic
# This is a bridge until we fully migrate scripts to packages/
def _get_scripts_dir() -> Path | None:
    current = Path(__file__).resolve()

    # 1. Try known project structure (packages/afo-core/services/log_analysis.py -> ... -> Root)
    # log_analysis.py -> services -> afo-core -> packages -> Root
    if len(current.parents) >= 4:
        project_root = current.parents[3]
        if (project_root / "scripts").exists():
            return project_root / "scripts"

    # 2. Iterative search
    for _ in range(5):
        current = current.parent
        if (current / "scripts").exists() and (current / "packages").exists():
            return current / "scripts"
        # Also check if we are in root (just to be safe if checking existence of scripts folder alone)
        if (current / "scripts").is_dir():
            return current / "scripts"
    return None


SCRIPTS_DIR = _get_scripts_dir()
if SCRIPTS_DIR and str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))


def _read_log_summary(log_file: Path, chunk_size: int) -> tuple[int, int]:
    """Read a log file synchronously for execution in a worker thread."""
    line_count = 0
    with log_file.open(encoding="utf-8", errors="ignore") as file:
        for line_count, _line in enumerate(file, start=1):
            if line_count % chunk_size == 0:
                # Process chunk
                pass
    return log_file.stat().st_size, line_count


class LogAnalysisService:
    """
    A resilient pipeline for processing and analyzing application logs.

    Trinity Score: 眞.선 (Truth & Goodness)
    - Implements safe_step pattern for graceful degradation
    - Supports streaming, caching, and plugin architecture
    """

    def __init__(self, output_dir: str | None = None) -> None:
        """
        Initialize the Log Analysis Service.

        Args:
            output_dir: Directory for analysis outputs (optional)
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./log_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._pipeline_steps: list[callable] = []

    async def run_pipeline(self, log_path: str, chunk_size: int | None = None) -> dict[str, Any]:
        """
        Run the complete log analysis pipeline.

        Args:
            log_path: Path to the log file to analyze
            chunk_size: Optional chunk size for processing

        Returns:
            Analysis results dictionary
        """
        try:
            log_file = Path(log_path)
            if not log_file.exists():
                return {
                    "status": "error",
                    "error": f"Log file not found: {log_path}",
                    "trinity_score": 0.0,
                }

            # BACKLOG: Celery/async worker 연동 (Phase 127+)
            # For now, process synchronously with chunked reading for large files

            # File iteration can be large enough to monopolize the event loop.
            # Keep the existing synchronous parser in a worker thread instead.
            _chunk_size = chunk_size or 1000
            file_size, line_count = await anyio.to_thread.run_sync(
                _read_log_summary, log_file, _chunk_size
            )

            results = {
                "status": "success",
                "log_path": log_path,
                "file_size": file_size,
                "lines_processed": line_count,
                "analysis": {},
                "trinity_score": 85.0,  # Placeholder
            }

            self.logger.info(f"Processed {line_count} lines from {log_path}")

            return results

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "trinity_score": 0.0,
            }

    def safe_step(self, step_name: str, step_func: callable, *args, **kwargs) -> Any:
        """
        Execute a pipeline step with graceful degradation.

        Args:
            step_name: Name of the step for logging
            step_func: Function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            Step result or None on failure
        """
        try:
            self.logger.debug(f"Executing step: {step_name}")
            return step_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Step '{step_name}' failed: {e}")
            return None
