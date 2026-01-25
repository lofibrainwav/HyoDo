"""
AFO 왕국 Memory 패키지 (Mem0 통합)

Trinity Score 목표:
- 永 (Eternity): 1.0 - 영원한 상태 보존
- 眞 (Truth): 0.9 - 정확한 메모리 관리
- 善 (Goodness): 0.95 - 안정적 상태 공유
- 美 (Beauty): 0.9 - Clean Architecture 통합
- 孝 (Serenity): 1.0 - 형님 평온 유지

기능:
- Mem0 기반 long-term 메모리 관리
- Context7 지식 베이스 통합
- thread/session 기반 상태 공유
- user-level personalization
"""

__version__ = "1.0.0"
__author__ = "AFO Kingdom Chancellor System"

# 주요 모듈 임포트
try:
    from .context7_integration import Context7MemoryManager
    from .mem0_client import AFO_MemoryClient, get_memory_client

    __all__ = [
        "AFO_MemoryClient",
        "Context7MemoryManager",
        "get_memory_client",
    ]
except ImportError as e:
    # Mem0가 설치되지 않은 경우
    __all__ = []
    import warnings

    warnings.warn(
        f"Mem0 integration not available: {e}. Install with: pip install mem0ai",
        stacklevel=2,
    )
