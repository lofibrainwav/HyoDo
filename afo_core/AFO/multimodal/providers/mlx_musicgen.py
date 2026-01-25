"""
MLX MusicGen Provider
Apple Silicon 최적화된 고성능 음악 생성
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from AFO.multimodal.providers.base import MusicProvider

logger = logging.getLogger(__name__)

# MLX 스크립트 템플릿
_MLX_SCRIPT_TEMPLATE = """
import sys
import json
sys.path.insert(0, "{musicgen_dir}")

try:
    from musicgen import MusicGen
    import numpy as np

    model = MusicGen.from_pretrained("{model_name}")
    print(f"Model loaded with sample rate: {{model.sampling_rate}}")

    prompt = "{prompt}"
    print(f"Generating music for prompt: {{prompt}}")

    duration = {duration}
    max_steps = min(int(duration * 50), 1000)
    print(f"Duration: {{duration}}s -> max_steps: {{max_steps}}")

    audio = model.generate([prompt], max_steps=max_steps)
    print(f"Generated audio shape: {{audio.shape}}")

    audio_np = np.array(audio).squeeze()
    print(f"Audio numpy shape: {{audio_np.shape}}")

    import scipy.io.wavfile
    output_path = "{output_path}"
    scipy.io.wavfile.write(output_path, model.sampling_rate, audio_np)

    result = {{
        "success": True,
        "output_path": output_path,
        "duration": len(audio_np) / model.sampling_rate,
        "sample_rate": model.sampling_rate,
        "prompt": prompt,
        "max_steps": max_steps
    }}
    print(json.dumps(result))

except Exception as e:
    import traceback
    error_result = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(error_result))
"""


class MLXMusicGenProvider(MusicProvider):
    """
    MLX MusicGen Provider
    Apple Silicon 최적화된 고성능 음악 생성
    """

    def __init__(self, venv_path: str | None = None) -> None:
        self.venv_path = venv_path or os.environ.get("AFO_MLX_MUSICGEN_VENV", "venv_musicgen")
        self._model_cache: dict[str, Any] = {}
        self._model_loaded = False
        self._audio_cache: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "MLX MusicGen"

    @property
    def version(self) -> str:
        return "v1.0.0"

    def generate_music(self, timeline_state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        MLX MusicGen을 사용한 음악 생성
        venv 환경에서 Apple Silicon 최적화 모델 실행
        """
        try:
            # 프롬프트 추출
            prompt = self._extract_prompt_from_timeline(timeline_state, "epic orchestral")

            # 스크립트 생성
            duration = kwargs.get("duration", 30)
            output_path = kwargs.get("output_path", "artifacts/mlx_music_output.wav")
            musicgen_dir = os.environ.get(
                "AFO_MLX_MUSICGEN_DIR",
                str(Path(__file__).resolve().parents[5] / "mlx-examples-official" / "musicgen"),
            )
            model_name = kwargs.get(
                "model_name", os.environ.get("AFO_MLX_MUSICGEN_MODEL", "facebook/musicgen-small")
            )

            script_content = _MLX_SCRIPT_TEMPLATE.format(
                prompt=prompt,
                duration=duration,
                output_path=output_path,
                musicgen_dir=musicgen_dir,
                model_name=model_name,
            )

            # 임시 스크립트 파일 생성
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(script_content)
                script_path = f.name

            try:
                cache_key = f"{prompt}_{duration}_{model_name}"
                if cache_key in self._audio_cache:
                    return self._audio_cache[cache_key]

                result = self._run_in_venv(script_path, use_cache=False)
                if result.get("success") and result.get("output_path"):
                    self._audio_cache[cache_key] = result
                return result
            finally:
                os.unlink(script_path)

        except Exception as e:
            logger.error(f"MLX MusicGen generation failed: {e}")
            return self._create_error_result(str(e))

    def _run_in_venv(self, script_path: str, use_cache: bool = True) -> dict[str, Any]:
        """venv에서 스크립트 실행"""
        venv_python = f"{self.venv_path}/bin/python3"
        if not os.path.exists(venv_python):
            return self._create_error_result(f"MLX venv not found at {venv_python}")

        result = subprocess.run(
            [venv_python, script_path],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(Path(__file__).resolve().parents[5]),
        )

        if result.returncode != 0:
            return self._create_error_result(
                f"MLX execution failed: {result.stderr}",
                stdout=result.stdout,
            )

        parsed = self._parse_output(result.stdout)

        if use_cache and parsed.get("success") and parsed.get("output_path"):
            self._audio_cache[script_path] = parsed

        return parsed

    def _parse_output(self, stdout: str) -> dict[str, Any]:
        """MLX 출력 파싱"""
        lines = stdout.strip().split("\n")

        for line in reversed(lines):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    output_data = json.loads(line)
                    if output_data.get("success"):
                        return self._create_success_result(
                            output_path=output_data["output_path"],
                            duration=output_data["duration"],
                            sample_rate=output_data["sample_rate"],
                            prompt=output_data["prompt"],
                        )
                    else:
                        return self._create_error_result(
                            output_data.get("error", "Unknown MLX error"),
                            traceback=output_data.get("traceback"),
                        )
                except json.JSONDecodeError as e:
                    return self._create_error_result(
                        f"Failed to parse MLX JSON: {e}",
                        stdout=stdout,
                    )

        return self._create_error_result(f"No JSON found in MLX output: {stdout}")

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "timeline_control": False,
            "quality": "excellent",
            "speed": "fast",
            "max_sections": 1,
            "requires_gpu": True,
            "local_only": True,
            "model_sizes": ["small", "medium", "large"],
            "apple_silicon_optimized": True,
        }

    def estimate_cost(self, timeline_state: dict[str, Any]) -> float:
        del timeline_state  # unused - local provider has no cost
        return 0.0

    def _load_model_cached(self, model_name: str, musicgen_dir: str) -> Any:
        """캐싱된 모델 로드 - 첫 로드 후 재사용"""
        cache_key = f"{model_name}_{musicgen_dir}"
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        try:
            from musicgen import MusicGen

            model = MusicGen.from_pretrained(model_name)
            self._model_cache[cache_key] = model
            return model
        except Exception as e:
            logger.warning(f"Model load failed: {e}")
            raise

    def is_available(self) -> bool:
        """MLX venv 환경과 MusicGen 사용 가능 여부 확인"""
        venv_python = f"{self.venv_path}/bin/python3"
        if not os.path.exists(venv_python):
            return False

        try:
            # MLX import 테스트
            result = subprocess.run(
                [venv_python, "-c", "import mlx; print('MLX OK')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return False

            # MusicGen import 테스트
            musicgen_dir = os.environ.get(
                "AFO_MLX_MUSICGEN_DIR",
                str(Path(__file__).resolve().parents[5] / "mlx-examples-official" / "musicgen"),
            )
            result = subprocess.run(
                [
                    venv_python,
                    "-c",
                    f"import sys; sys.path.insert(0, '{musicgen_dir}'); from musicgen import MusicGen; print('MusicGen OK')",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0

        except Exception:
            return False
