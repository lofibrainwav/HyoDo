"""
MusicProvider Interface - 오픈소스 음악 생성 서비스 통합
AFO 왕국의 멀티모달 음악 생성을 위한 통합 인터페이스

리팩터링: Provider들을 별도 모듈로 분리하여 500줄 규칙 준수

지원 Provider:
- AudioCraft (Meta): 고품질 + 세부 제어 (메인)
- MusicGen (Meta): 빠른 생성 + 간단 API (백업)
- Stable Audio Open (Stability AI): 안정적 + 유연한 길이 (보조)
- MLX MusicGen: Apple Silicon 최적화 (로컬)
- Suno (외부 API): 상용 서비스 (옵션)
"""

import logging
from typing import Any

# Re-export all providers for backwards compatibility
from AFO.multimodal.providers import (
    AudioCraftProvider,
    MLXMusicGenProvider,
    MusicGenProvider,
    MusicProvider,
    StableAudioProvider,
    SunoProvider,
)

__all__ = [
    # Base class
    "MusicProvider",
    # Providers
    "AudioCraftProvider",
    "MusicGenProvider",
    "StableAudioProvider",
    "MLXMusicGenProvider",
    "SunoProvider",
    # Router
    "MusicProviderRouter",
    "get_music_router",
    "generate_music_with_router",
]

logger = logging.getLogger(__name__)


class MusicProviderRouter:
    """
    MusicProvider 자동 라우터
    품질/속도/비용 기반으로 최적 Provider 선택
    """

    def __init__(self) -> None:
        self.providers: dict[str, MusicProvider] = {}
        self._load_providers()

    def _load_providers(self) -> None:
        """사용 가능한 Provider들 로드"""
        candidates: list[MusicProvider] = [
            AudioCraftProvider(),
            MusicGenProvider(),
            StableAudioProvider(),
            MLXMusicGenProvider(),
            SunoProvider(),
        ]

        for provider in candidates:
            if provider.is_available():
                self.providers[provider.name] = provider
                logger.info(f"Loaded music provider: {provider.name} v{provider.version}")

    def get_available_providers(self) -> list[str]:
        """사용 가능한 Provider 이름 목록"""
        return list(self.providers.keys())

    def select_provider(
        self,
        requirements: dict[str, Any],
    ) -> MusicProvider | None:
        """
        요구사항에 맞는 최적 Provider 선택

        Args:
            requirements: 선택 기준
                - quality: "high", "medium", "low"
                - speed: "fast", "medium", "slow"
                - local_only: True/False
                - max_cost: 최대 비용

        Returns:
            선택된 Provider 또는 None
        """
        local_only = requirements.get("local_only", False)
        max_cost = requirements.get("max_cost", float("inf"))

        candidates: list[tuple[int, MusicProvider]] = []

        for provider in self.providers.values():
            caps = provider.get_capabilities()

            # 필터링
            if local_only and not caps.get("local_only", False):
                continue
            if max_cost < 0.01 and not caps.get("local_only", False):
                continue

            # 점수 계산
            score = self._calculate_score(caps)
            candidates.append((score, provider))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    @staticmethod
    def _calculate_score(caps: dict[str, Any]) -> int:
        """Provider 점수 계산"""
        score = 0

        # 품질 점수
        quality_map = {"excellent": 4, "high": 3, "good": 2, "medium": 1, "low": 0}
        score += quality_map.get(caps.get("quality", "medium"), 1) * 2

        # 속도 점수
        speed_map = {"fast": 3, "medium": 2, "slow": 1}
        score += speed_map.get(caps.get("speed", "medium"), 1)

        return score

    def generate_music(
        self,
        timeline_state: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        자동 Provider 선택 후 음악 생성

        Args:
            timeline_state: TimelineState dict
            **kwargs: 라우터 옵션 + Provider 파라미터

        Returns:
            생성 결과
        """
        # Provider 선택
        requirements = {
            "quality": kwargs.get("quality", "high"),
            "speed": kwargs.get("speed", "medium"),
            "local_only": kwargs.get("local_only", True),
            "max_cost": kwargs.get("max_cost", 0.0),
        }

        provider = self.select_provider(requirements)
        if not provider:
            return {
                "success": False,
                "error": f"No suitable provider found for requirements: {requirements}",
                "available_providers": self.get_available_providers(),
            }

        logger.info(f"Selected music provider: {provider.name} v{provider.version}")

        # Provider별 kwargs 분리
        router_keys = {"quality", "speed", "local_only", "max_cost"}
        provider_kwargs = {k: v for k, v in kwargs.items() if k not in router_keys}

        # 음악 생성
        result = provider.generate_music(timeline_state, **provider_kwargs)

        # 결과에 Provider 정보 추가
        result["selected_provider"] = {
            "name": provider.name,
            "version": provider.version,
            "capabilities": provider.get_capabilities(),
            "estimated_cost": provider.estimate_cost(timeline_state),
        }

        return result


# 글로벌 Router 인스턴스
_music_router: MusicProviderRouter | None = None


def get_music_router() -> MusicProviderRouter:
    """글로벌 MusicProviderRouter 인스턴스"""
    global _music_router
    if _music_router is None:
        _music_router = MusicProviderRouter()
    return _music_router


def generate_music_with_router(
    timeline_state: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """
    MusicProviderRouter를 사용한 음악 생성 편의 함수

    Args:
        timeline_state: TimelineState dict
        **kwargs: 라우터 옵션

    Returns:
        생성 결과
    """
    router = get_music_router()
    return router.generate_music(timeline_state, **kwargs)


def test_music_providers() -> None:
    """사용 가능한 Provider들 테스트"""
    router = get_music_router()

    print("🎵 MusicProvider 테스트")
    print(f"사용 가능한 Provider들: {router.get_available_providers()}")

    test_timeline = {
        "title": "AFO Test Music",
        "sections": [
            {"start": 0, "end": 3, "text": "Epic intro", "music_directive": "slow_build"},
            {"start": 3, "end": 6, "text": "Action scene", "music_directive": "drop_beat"},
        ],
    }

    for provider_name in router.get_available_providers():
        print(f"\n🔍 Testing {provider_name}...")
        try:
            result = router.generate_music(test_timeline, local_only=True, max_cost=0.0)
            if result.get("success"):
                print(f"  ✅ {provider_name}: 성공 - {result.get('output_path')}")
            else:
                print(f"  ❌ {provider_name}: 실패 - {result.get('error')}")
        except Exception as e:
            print(f"  ❌ {provider_name}: 예외 - {e}")


if __name__ == "__main__":
    test_music_providers()
