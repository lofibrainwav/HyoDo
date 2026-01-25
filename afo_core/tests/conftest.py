import sys
from pathlib import Path

_core = Path(__file__).resolve().parents[1]
if str(_core) not in sys.path:
    sys.path.insert(0, str(_core))

# Add AFO package to path for testing
_afo = _core / "AFO"
if str(_afo) not in sys.path:
    sys.path.insert(0, str(_afo))
