# Trinity Score: 96.0 (Phase 30 Package Initialization)
"""AFO Input Server Package - API Key Management Service"""

from .core import app
from .utils import parse_env_text

__version__ = "1.0.0"
__all__ = ["app", "parse_env_text"]
