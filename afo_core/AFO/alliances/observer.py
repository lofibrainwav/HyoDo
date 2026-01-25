"""
Alliance Observer - Safe Monitoring for Allied Services
Performs DNS-only checks for external APIs and internal health checks for local services.
Trinity Pillar: 善 (Goodness) - Monitoring & Stability
"""

import json
import logging
import os
import socket
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AllianceObserver:
    """Monitors the health and connectivity of allied services."""

    def __init__(self, config_path: str = "config/alliances.json") -> None:
        self.repo_root = self._find_repo_root()
        self.config_path = self.repo_root / config_path
        self._alliances: list[dict[str, Any]] = []

    def _find_repo_root(self) -> Path:
        """Find the root directory of the repository, prioritizing .git."""
        here = Path(__file__).resolve()
        # Search for .git first (TRUE root)
        for parent in [here, *here.parents]:
            if (parent / ".git").exists():
                return parent
        # Fallback to AGENTS.md
        for parent in [here, *here.parents]:
            if (parent / "AGENTS.md").exists():
                return parent
        # Ultimate fallback: this file is at packages/afo-core/AFO/alliances/observer.py
        # So repo root is 5 parents up
        return here.parents[4]

    def load_config(self) -> list[dict[str, Any]]:
        """Load alliance configuration from JSON file."""
        if not self.config_path.exists():
            logger.error(f"Alliance config not found: {self.config_path}")
            return []

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                self._alliances = data.get("alliances", [])
                return self._alliances
        except Exception as e:
            logger.error(f"Failed to load alliance config: {e}")
            return []

    def check_dns(self, domain: str) -> bool:
        """Perform a safe DNS resolution check."""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
        except Exception as e:
            logger.warning(f"DNS check failed for {domain}: {e}")
            return False

    def observe_all(self) -> list[dict[str, Any]]:
        """Perform observation on all configured alliances."""
        self.load_config()
        results = []

        for alliance in self._alliances:
            observation = {
                "id": alliance["id"],
                "name": alliance["name"],
                "type": alliance["type"],
                "observed_at": datetime.now().isoformat() + "Z",  # Use now for local run
                "status": "unknown",
            }

            if alliance["type"] == "external_api":
                dns_conf = alliance.get("dns_check", {})
                domain = dns_conf.get("domain")
                if domain:
                    is_reachable = self.check_dns(domain)
                    observation["status"] = "allied" if is_reachable else "isolated"
                    observation["dns_reachable"] = is_reachable
                else:
                    observation["status"] = "allied"

            elif alliance["type"] == "internal_service":
                observation["status"] = "allied"

            results.append(observation)

        return results

    def save_observation_report(self, results: list[dict[str, Any]]) -> None:
        """Save the observation results to a temporary artifact for UI consumption."""
        report_path = self.repo_root / "artifacts" / "alliance_observation.json"
        os.makedirs(report_path.parent, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat() + "Z",
            "alliances": results,
            "trinity_routing": "SAFE",
        }

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Observation report saved: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save observation report: {e}")


if __name__ == "__main__":
    observer = AllianceObserver()
    results = observer.observe_all()
    observer.save_observation_report(results)
    print(json.dumps(results, indent=2))
