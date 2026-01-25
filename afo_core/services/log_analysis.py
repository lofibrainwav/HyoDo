"""
AFO Kingdom Log Analysis Service
Trinity Score: 眞.선 (Truth & Goodness)
- Robust, resilient pipeline for log analysis
- Uses safe_step for graceful degradation

Author: AFO Kingdom Development Team
"""

import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


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

# Import legacy components
try:
    from sequential_analyzer import SequentialAnalyzer

except ImportError as e:
    logging.getLogger(__name__).warning(f"Could not import script components: {e}")
    LogChunker = None  # type: ignore
    SequentialAnalyzer = None  # type: ignore

from AFO.config.log_analysis import log_analysis_settings
from AFO.services.plugin_manager import PluginManager
from AFO.utils.performance import monitor_memory
from AFO.utils.resilience import safe_step
from AFO.utils.result_cache import ResultCache
from AFO.utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class LogAnalysisService:
    """
    Resilient Log Analysis Service
    Wraps legacy scripts in a robust pipeline with error handling.
    """

    def __init__(self, output_dir: str | None = None) -> None:
        # Use config if not provided
        self.output_dir = Path(output_dir) if output_dir else log_analysis_settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Cache
        self.cache = ResultCache(self.output_dir / ".cache")

        # Initialize Plugin Manager
        self.plugin_manager = PluginManager()

        logger.info(
            "LogAnalysisService initialized",
            context={"output_dir": str(self.output_dir)},
        )

    @safe_step(
        fallback_return={"status": "failed", "chunks_created": 0},
        log_level=logging.ERROR,
        step_name="Log Chunking",
    )
    @monitor_memory
    def chunk_logs(self, log_path: str, chunk_size: int | None = None) -> dict[str, Any]:
        """
        Step 1: Chunk logs using streaming generator.
        Fallback: Returns empty result dict.
        """
        # Use config if not provided
        target_chunk_size = (
            chunk_size if chunk_size is not None else log_analysis_settings.CHUNK_SIZE
        )

        # CHECK CACHE
        cache_params = {"step": "chunk_logs", "chunk_size": target_chunk_size}
        cached_result = self.cache.get(log_path, cache_params)
        if cached_result:
            return cached_result

        logger.info(
            "Starting Log Chunking (Streaming)",
            context={"log_path": log_path, "chunk_size": target_chunk_size},
        )

        chunk_dir = self.output_dir / "chunks"
        chunk_dir.mkdir(exist_ok=True)

        chunks_created = []
        current_chunk = []
        chunk_index = 0
        total_lines = 0

        try:
            with open(log_path, encoding="utf-8") as f:
                for line in f:
                    total_lines += 1
                    current_chunk.append(line)

                    if len(current_chunk) >= target_chunk_size:
                        chunk_filename = f"chunk_{chunk_index:04d}.json"
                        chunk_path = chunk_dir / chunk_filename

                        chunk_data = {
                            "chunk_id": f"chunk_{chunk_index:04d}",
                            "lines": current_chunk,
                        }

                        with open(chunk_path, "w", encoding="utf-8") as cf:
                            json.dump(chunk_data, cf)

                        chunks_created.append(str(chunk_path))
                        current_chunk = []
                        chunk_index += 1

                # Write remaining lines
                if current_chunk:
                    chunk_filename = f"chunk_{chunk_index:04d}.json"
                    chunk_path = chunk_dir / chunk_filename
                    chunk_data = {
                        "chunk_id": f"chunk_{chunk_index:04d}",
                        "lines": current_chunk,
                    }
                    with open(chunk_path, "w", encoding="utf-8") as cf:
                        json.dump(chunk_data, cf)
                    chunks_created.append(str(chunk_path))

        except FileNotFoundError:
            raise FileNotFoundError(f"Log file not found: {log_path}")

        logger.info(
            "Chunking completed",
            context={"chunks_count": len(chunks_created), "total_lines": total_lines},
        )

        result = {
            "status": "success",
            "chunks_created": len(chunks_created),
            "output_dir": str(chunk_dir),
            "statistics": {
                "total_chunks": len(chunks_created),
                "total_lines": total_lines,
            },
        }

        # SAVE TO CACHE
        self.cache.set(log_path, cache_params, result)

        return result

    @safe_step(
        fallback_return={"status": "partial_failure", "analysis": []},
        log_level=logging.ERROR,
        step_name="Sequential Analysis",
    )
    def analyze_sequential(self, chunks_dir: str) -> dict[str, Any]:
        """
        Step 2: sequential Analysis.
        Fallback: Returns empty analysis list.
        """
        # Lazy import retry to support test environments where sys.path is updated late
        global SequentialAnalyzer
        if not SequentialAnalyzer:
            try:
                import importlib

                if "sequential_analyzer" in sys.modules:
                    importlib.reload(sys.modules["sequential_analyzer"])
                else:
                    # Try adding path again if missing
                    s_dir = _get_scripts_dir()
                    if s_dir and str(s_dir) not in sys.path:
                        sys.path.append(str(s_dir))

                from sequential_analyzer import SequentialAnalyzer as SA

                SequentialAnalyzer = SA
            except ImportError:
                pass

        if not SequentialAnalyzer:
            raise ImportError("SequentialAnalyzer module not found")

        # CHECK CACHE
        # Use chunks_dir as the 'file' key since it represents the input data source
        cache_params = {"step": "analyze_sequential"}
        cached_result = self.cache.get(chunks_dir, cache_params)
        if cached_result:
            return cached_result

        logger.info("Starting Sequential Analysis", context={"chunks_dir": chunks_dir})
        analyzer = SequentialAnalyzer(chunks_dir)
        analyses = analyzer.analyze_all_chunks()
        report_file = analyzer.generate_report(str(self.output_dir / "sequential_report.md"))

        result = {
            "status": "success",
            "analysis_count": len(analyses),
            "report_file": report_file,
            "analyses": [asdict(a) for a in analyses],
        }

        # SAVE TO CACHE
        self.cache.set(chunks_dir, cache_params, result)

        return result

    def run_pipeline(self, log_file: str) -> dict[str, Any]:
        """
        Execute the full resilient pipeline.
        Each step is protected by safe_step.
        """
        logger.info(
            "🚀 Starting Resilient Log Analysis Pipeline",
            context={"log_file": log_file},
        )
        results = {}

        # 1. Chunking
        chunk_result = self.chunk_logs(log_file)
        results["chunking"] = chunk_result

        # 2. Sequential Analysis (only if chunking succeeded or partially succeeded)
        if chunk_result.get("chunks_created", 0) > 0:
            chunks_dir = chunk_result.get("output_dir")
            results["sequential"] = self.analyze_sequential(chunks_dir)
        else:
            reason = "No chunks created"
            results["sequential"] = {"status": "skipped", "reason": reason}
            logger.warning("Skipping Sequential Analysis", context={"reason": reason})

        # 3. Validation / Plugins
        plugin_results = {}
        if chunk_result.get("chunks_created", 0) > 0:
            chunks_dir = chunk_result.get("output_dir")
            # Support both json and log for plugin compatibility
            chunk_files = sorted(
                list(Path(chunks_dir).glob("*.json")) + list(Path(chunks_dir).glob("*.log"))
            )

            # Run each plugin on the first chunk (sample) for now, or all chunks
            # For performance, let's run on the first chunk as a sample verification
            if chunk_files:
                sample_chunk = str(chunk_files[0])
                for plugin in self.plugin_manager.get_all_plugins():
                    try:
                        logger.info(
                            f"Running Plugin: {plugin.name}",
                            context={"plugin": plugin.name},
                        )
                        p_result = plugin.analyze(sample_chunk)
                        plugin_results[plugin.name] = p_result
                    except Exception as e:
                        logger.error(f"Plugin {plugin.name} failed", context={"error": str(e)})
                        plugin_results[plugin.name] = {
                            "status": "error",
                            "message": str(e),
                        }

        results["plugins"] = plugin_results

        # 4. Report (Safe Generation)
        # TODO: Move Context7 and Integration Report to this service in next steps

        logger.info("✅ Pipeline completed", context={"results_summary": list(results.keys())})
        return results
