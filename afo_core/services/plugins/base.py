"""
AFO Kingdom Log Analysis Plugin Interface
Trinity Score: 美 (Beauty) - Extensibility & Structure
Author: AFO Kingdom Development Team
"""

from abc import ABC, abstractmethod
from typing import Any


class LogAnalysisPlugin(ABC):
    """
    Abstract Base Class for Log Analysis Plugins.
    All plugins must inherit from this class and implement the `analyze` method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the plugin"""
        pass

    @abstractmethod
    def analyze(self, chunk_path: str) -> dict[str, Any]:
        """
        Analyze a specific log chunk.

        Args:
            chunk_path: Path to the log chunk file.

        Returns:
            Dictionary containing analysis results.
        """
        pass
