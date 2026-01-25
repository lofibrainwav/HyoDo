"""
Suno (외부 API) Provider
상용 서비스 통합
"""

import os
from typing import Any

from AFO.multimodal.providers.base import MusicProvider


class SunoProvider(MusicProvider):
    """
    Suno (외부 API) Provider
    기존 SunoBranch를 Provider 인터페이스로 래핑
    """

    @property
    def name(self) -> str:
        return "Suno"

    @property
    def version(self) -> str:
        return "API"

    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        Suno API를 통한 음악 생성
        기존 suno_branch 모듈 활용
        """
        try:
            from AFO.multimodal.suno_branch import run_suno_pipeline

            result = run_suno_pipeline(
                timeline_state,
                dry_run=False,
                target_av_duration_sec=kwargs.get("duration"),
                video_path_for_fusion=None,
            )

            if result.get("success"):
                outputs = result.get("outputs", {})
                return {
                    "success": True,
                    "provider": self.name,
                    "output_path": outputs.get("audio_raw"),
                    "duration": "aligned" if outputs.get("audio_aligned") else "original",
                }
            else:
                return self._create_error_result(result.get("error", "Unknown Suno error"))

        except Exception as e:
            return self._create_error_result(str(e))

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "timeline_control": True,
            "quality": "excellent",
            "speed": "slow",
            "max_sections": 10,
            "requires_gpu": False,
            "local_only": False,
        }

    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        sections = len(timeline_state.get("sections", []))
        return sections * 0.08

    def is_available(self) -> bool:
        return bool(os.getenv("SUNO_API_KEY"))
