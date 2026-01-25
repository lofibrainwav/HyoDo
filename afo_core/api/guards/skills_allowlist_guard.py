from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

"""Skills Allowlist Runtime Enforcement.

Loads skills_allowlist.yaml and provides guard function for skill execution.
"""


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_allowlist() -> dict[str, Any]:
    """Load and cache skills allowlist from YAML."""
    # Path relative to afo-core root: config/skills_allowlist.yaml
    allowlist_path = Path(__file__).parent.parent.parent / "config" / "skills_allowlist.yaml"

    if not allowlist_path.exists():
        logger.warning(f"Skills allowlist not found: {allowlist_path}")
        return {"approved_skills": [], "blocked_skills": [], "fallback_rules": []}

    try:
        data = yaml.safe_load(allowlist_path.read_text(encoding="utf-8")) or {}
        logger.info(f"Skills allowlist loaded: {len(data.get('approved_skills', []))} approved")
        return data
    except ImportError:
        logger.error("PyYAML not installed, allowlist disabled")
        return {"approved_skills": [], "blocked_skills": [], "fallback_rules": []}
    except Exception as e:
        logger.error(f"Failed to load skills allowlist: {e}")
        return {"approved_skills": [], "blocked_skills": [], "fallback_rules": []}


def is_skill_allowed(skill_id: str) -> tuple[bool, str]:
    """Check if skill is allowed to execute.

    Returns:
        (allowed: bool, reason: str)
    """
    allowlist = _load_allowlist()

    blocked = set(allowlist.get("blocked_skills", []))
    approved = set(allowlist.get("approved_skills", []))

    if skill_id in blocked:
        return False, f"Skill '{skill_id}' is blocked by policy"

    # If approved list exists and is non-empty, skill must be in it
    if approved and skill_id not in approved:
        return False, f"Skill '{skill_id}' is not in approved list"

    return True, "allowed"


def get_fallback_action(condition: str) -> str:
    """Get fallback action for a condition."""
    allowlist = _load_allowlist()

    for rule in allowlist.get("fallback_rules", []):
        if rule.get("if") == condition:
            return rule.get("then", "log_and_skip")

    return "log_and_skip"


def clear_allowlist_cache() -> None:
    """Clear the cached allowlist (for testing or hot-reload)."""
    _load_allowlist.cache_clear()
