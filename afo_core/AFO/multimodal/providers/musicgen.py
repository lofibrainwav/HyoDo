"""
MusicGen (Meta) Provider
빠른 음악 생성 + 간단 API
"""

import logging
from collections import Counter
from typing import Any

from AFO.multimodal.providers.base import MusicProvider

logger = logging.getLogger(__name__)


class MusicGenProvider(MusicProvider):
    """
    MusicGen (Meta) Provider
    빠르고 간단한 텍스트-음악 변환
    """

    @property
    def name(self) -> str:
        return "MusicGen"

    @property
    def version(self) -> str:
        return "v1.2.0"

    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        MusicGen을 사용한 음악 생성
        빠르고 간단한 텍스트-음악 변환
        """
        try:
            from audiocraft.data.audio import audio_write
            from audiocraft.models import MusicGen

            # 모델 선택 (small/medium/large)
            model_size = kwargs.get("model_size", "medium")
            model = MusicGen.get_pretrained(f"facebook/musicgen-{model_size}")

            # TimelineState에서 통합 프롬프트 생성
            sections = timeline_state.get("sections", [])
            music = timeline_state.get("music", {})

            if sections:
                directives = [s.get("music_directive", "instrumental") for s in sections]
                main_directive = Counter(directives).most_common(1)[0][0]
                final_prompt = f"{main_directive}, {len(sections)} sections composition"
            else:
                final_prompt = music.get("prompt", "epic orchestral music")

            # 음악 생성
            model.set_generation_params(
                duration=kwargs.get("duration", 30),
                temperature=kwargs.get("temperature", 0.8),
            )

            wav = model.generate([final_prompt], progress=True)

            # 오디오 저장
            output_path = kwargs.get("output_path", "artifacts/musicgen_output.wav")
            audio_write(output_path, wav[0].cpu(), model.sample_rate, strategy="loudness")

            return self._create_success_result(
                output_path=output_path,
                duration=wav[0].shape[1] / model.sample_rate,
                sample_rate=model.sample_rate,
                model_size=model_size,
            )

        except ImportError:
            return self._create_error_result("MusicGen not installed. Run: pip install audiocraft")
        except Exception as e:
            logger.error(f"MusicGen generation failed: {e}")
            return self._create_error_result(str(e))

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "timeline_control": False,
            "quality": "good",
            "speed": "fast",
            "max_sections": 1,
            "requires_gpu": True,
            "local_only": True,
            "model_sizes": ["small", "medium", "large"],
        }

    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        del timeline_state  # unused - local provider has no cost
        return 0.0

    def is_available(self) -> bool:
        try:
            return True
        except ImportError:
            return False
