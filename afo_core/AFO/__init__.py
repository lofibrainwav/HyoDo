# Trinity Score: 90.0 (Established by Chancellor)
"""AFO 패키지 - 루트 모듈 re-export
테스트 호환성을 위해 afo-core 루트 모듈들을 AFO 네임스페이스로 노출
MD→티켓 자동화 관련 모듈들도 포함
"""

import sys
from pathlib import Path

# 부모 디렉토리(afo-core 루트)를 path에 추가
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

# MD→티켓 자동화 모듈들 노출 (optional - may not exist)
try:
    from .matching_engine import MatchingEngine
    from .md_parser import MDParser
    from .skeleton_index import ModuleInfo, SkeletonIndex, SkeletonIndexer
    from .ticket_generator import TicketGenerator

    _MD_MODULES_AVAILABLE = True
except ImportError:
    MDParser = None  # type: ignore[misc,assignment]
    MatchingEngine = None  # type: ignore[misc,assignment]
    TicketGenerator = None  # type: ignore[misc,assignment]
    SkeletonIndexer = None  # type: ignore[misc,assignment]
    SkeletonIndex = None  # type: ignore[misc,assignment]
    ModuleInfo = None  # type: ignore[misc,assignment]
    _MD_MODULES_AVAILABLE = False


# 모듈 re-export (lazy import 방식으로 에러 방지)
def __getattr__(name: str) -> None:
    """Lazy import for AFO submodules"""
    import importlib

    # 실제 모듈 위치 매핑 (깨진 심볼릭 링크 대체)
    _module_map = {
        "api_wallet": "domain.wallet.core",
        "llm_router": "infrastructure.llm.router",
        "afo_skills_registry": "afo_soul_engine.afo_skills_registry",
        "chancellor_graph": "AFO.chancellor_graph",
        "kms": "kms",
        "scholars": "scholars",
        "services": "services",
        "utils": "utils",
        "llms": "llms",
        "domain": "domain",
        "schemas": "schemas",
    }

    if name in _module_map:
        return importlib.import_module(_module_map[name])

    raise AttributeError(f"module 'AFO' has no attribute '{name}'")


__all__ = [
    "MDParser",
    "MatchingEngine",
    "ModuleInfo",
    "SkeletonIndex",
    "SkeletonIndexer",
    "TicketGenerator",
]
