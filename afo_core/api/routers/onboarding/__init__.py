"""Onboarding Package - 에이전트/사용자 온보딩 API

새로운 에이전트나 사용자가 왕국에 들어왔을 때
시스템 아키텍처를 온보딩하는 API를 제공합니다.

Trinity Score: 眞95% 善94% 美96% 孝93% 永92%
"""

from .router import get_onboarding_service, router

__all__ = ["router", "get_onboarding_service"]
