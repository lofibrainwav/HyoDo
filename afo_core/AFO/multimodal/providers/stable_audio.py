"""
Stable Audio Open (Stability AI) Provider
안정적인 오픈소스 음악 생성
"""

import logging
from typing import Any

from AFO.multimodal.providers.base import MusicProvider

logger = logging.getLogger(__name__)


class StableAudioProvider(MusicProvider):
    """
    Stable Audio Open (Stability AI) Provider
    안정적인 오픈소스 음악 생성
    """

    @property
    def name(self) -> str:
        return "Stable Audio Open"

    @property
    def version(self) -> str:
        return "v1.0.0"

    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Stable Audio Open을 사용한 음악 생성"""
        try:
            from stable_audio_tools import get_pretrained_model
            from stable_audio_tools.inference import generate_audio

            # 모델 로드
            model, processor = get_pretrained_model("stabilityai/stable-audio-open-1.0")

            # TimelineState에서 프롬프트 추출
            prompt = self._extract_prompt_from_timeline(timeline_state, "instrumental")

            # 음악 생성
            duration = kwargs.get("duration", 10)
            sample_rate = 44100

            output = generate_audio(
                model=model,
                processor=processor,
                prompt=prompt,
                duration=duration,
                num_samples=1,
            )

            # 오디오 저장
            import torchaudio

            output_path = kwargs.get("output_path", "artifacts/stable_audio_output.wav")
            torchaudio.save(output_path, output[0], sample_rate)

            return self._create_success_result(
                output_path=output_path,
                duration=duration,
                sample_rate=sample_rate,
            )

        except ImportError:
            return self._create_error_result(
                "Stable Audio Open not installed. Run: pip install stable-audio-tools"
            )
        except Exception as e:
            logger.error(f"Stable Audio generation failed: {e}")
            return self._create_error_result(str(e))

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "timeline_control": False,
            "quality": "good",
            "speed": "medium",
            "max_sections": 1,
            "requires_gpu": True,
            "local_only": True,
            "duration_range": [1, 47],
        }

    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        del timeline_state  # unused - local provider has no cost
        return 0.0

    def is_available(self) -> bool:
        try:
            return True
        except ImportError:
            return False
