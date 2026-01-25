# AFO Kingdom Code Validation Package
"""
코드 검증 시스템의 모듈화된 패키지입니다.

Trinity Score 목표:
- 眞 (Truth): AST 기반 정확한 분석 (0.9)
- 善 (Goodness): 모듈화로 안정성 향상 (0.9)
- 美 (Beauty): Clean Architecture 준수 (1.0)
- 孝 (Serenity): 형님 평온 재사용 (1.0)
- 永 (Eternity): 모듈화로 유지보수성 (1.0)
"""

__version__ = "1.0.0"
__author__ = "AFO Kingdom Chancellor System"

# 주요 모듈 임포트
from .ast_analyzer import ASTAnalyzer, analyze_code
from .loader import load_review_module

__all__ = [
    "ASTAnalyzer",
    "analyze_code",
    "load_review_module",
]
