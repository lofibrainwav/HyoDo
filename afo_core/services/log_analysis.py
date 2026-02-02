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
# NOTE: SequentialAnalyzer import removed - was unused (Ruff F401)
# Can be re-added when actually needed for log analysis pipeline
try:
    pass  # Placeholder for future imports
except ImportError as e:
    logging.getLogger(__name__).warning(f"Could not import script components: {e}")
