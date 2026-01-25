"""
Chancellor Router Package
500줄 규칙 준수를 위해 분리된 모듈

구조:
- imports.py: 공통 import 및 fallback 로직
- helpers.py: 헬퍼 함수들
- executors.py: 실행 함수들
- router.py: API 엔드포인트
"""

from api.routers.chancellor.router import router

__all__ = ["router"]
