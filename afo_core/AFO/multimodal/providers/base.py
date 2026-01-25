"""
MusicProvider 베이스 클래스

모든 음악 생성 Provider의 표준 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import Any


class MusicProvider(ABC):
    """
    음악 생성 Provider의 표준 인터페이스
    모든 음악 생성 서비스는 이 인터페이스를 구현해야 함
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 이름"""

    @property
    @abstractmethod
    def version(self) -> str:
        """Provider 버전"""

    @abstractmethod
    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        TimelineState를 기반으로 음악 생성

        Args:
            timeline_state: TimelineState dict
            **kwargs: Provider별 추가 파라미터

        Returns:
            생성 결과 dict
        """

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """
        Provider의 기능/제한사항 반환

        Returns:
            capabilities dict
        """

    @abstractmethod
    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        """
        음악 생성 비용 추정 (로컬은 0, API는 실제 비용)

        Args:
            timeline_state: TimelineState dict

        Returns:
            예상 비용 (USD)
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Provider가 사용 가능한지 확인

        Returns:
            사용 가능 여부
        """

    def _extract_prompt_from_timeline(
        self,
        timeline_state: dict[str, Any],
        default_directive: str = "instrumental",
    ) -> str:
        """
        TimelineState에서 프롬프트 추출 (공통 유틸리티)

        Args:
            timeline_state: TimelineState dict
            default_directive: 기본 음악 지시어

        Returns:
            생성된 프롬프트 문자열
        """
        sections = timeline_state.get("sections", [])
        music = timeline_state.get("music", {})

        if sections:
            first_section = sections[0]
            directive = first_section.get("music_directive", default_directive)
            text = first_section.get("text", "")
            return f"{directive} {text}".strip() if text else directive

        return music.get("prompt", f"{default_directive} music")

    def _create_success_result(
        self,
        output_path: str,
        duration: float,
        sample_rate: int,
        **extra: Any,
    ) -> dict[str, Any]:
        """성공 결과 생성 (공통 유틸리티)"""
        result = {
            "success": True,
            "provider": self.name,
            "output_path": output_path,
            "duration": duration,
            "sample_rate": sample_rate,
        }
        result.update(extra)
        return result

    def _create_error_result(self, error: str, **extra: Any) -> dict[str, Any]:
        """에러 결과 생성 (공통 유틸리티)"""
        result = {
            "success": False,
            "error": error,
            "provider": self.name,
        }
        result.update(extra)
        return result
