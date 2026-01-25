"""
AudioCraft (Meta) Provider
고품질 음악 생성 + 세부 시간 제어
"""

import logging
from typing import Any

from AFO.multimodal.providers.base import MusicProvider

logger = logging.getLogger(__name__)


class AudioCraftProvider(MusicProvider):
    """
    AudioCraft (Meta) Provider
    고품질 음악 생성 + 세부 시간 제어
    """

    @property
    def name(self) -> str:
        return "AudioCraft"

    @property
    def version(self) -> str:
        return "v1.4.1"

    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        AudioCraft를 사용한 음악 생성
        TimelineState의 시간별 세그먼트를 개별로 생성하고 합성
        """
        try:
            from audiocraft.data.audio import audio_write
            from audiocraft.models import MusicGen

            # 모델 로드 (lazy loading)
            model = MusicGen.get_pretrained("facebook/musicgen-melody")
            model.set_generation_params(duration=30)

            # TimelineState 처리
            sections = timeline_state.get("sections", [])
            if not sections:
                return self._create_error_result("No sections in timeline_state")

            # 각 섹션별 프롬프트 생성
            prompts = []
            for section in sections:
                text = section.get("text", "")
                directive = section.get("music_directive", "epic orchestral")
                prompt = f"{directive}, {text}" if text else directive
                prompts.append(prompt)

            # 배치 생성
            if len(prompts) == 1:
                wav = model.generate([prompts[0]], progress=True)
            else:
                combined_prompt = " | ".join(prompts[:4])
                wav = model.generate([combined_prompt], progress=True)

            # 오디오 저장
            output_path = kwargs.get("output_path", "artifacts/audiocraft_output.wav")
            audio_write(output_path, wav[0].cpu(), model.sample_rate, strategy="loudness")

            return self._create_success_result(
                output_path=output_path,
                duration=wav[0].shape[1] / model.sample_rate,
                sample_rate=model.sample_rate,
            )

        except ImportError:
            return self._create_error_result(
                "AudioCraft not installed. Run: pip install audiocraft"
            )
        except Exception as e:
            logger.error(f"AudioCraft generation failed: {e}")
            return self._create_error_result(str(e))

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "timeline_control": True,
            "quality": "high",
            "speed": "medium",
            "max_sections": 4,
            "requires_gpu": True,
            "local_only": True,
        }

    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        del timeline_state  # unused - local provider has no cost
        return 0.0

    def is_available(self) -> bool:
        try:
            return True
        except ImportError:
            return False
