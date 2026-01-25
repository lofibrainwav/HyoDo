# Trinity Score: 92.0 (Multimodal Audio)
"""
Audio Service for AFO Kingdom (귀/Ears)
Uses Whisper for speech-to-text transcription.

2025 Best Practice: OpenAI Whisper for accurate multilingual ASR.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AudioService:
    """
    Audio Service using OpenAI Whisper for speech recognition.
    Gives agents the ability to "hear" and understand audio.
    """

    def __init__(self, model: str = "base") -> None:
        """
        Initialize AudioService.

        Args:
            model: Whisper model size (tiny, base, small, medium, large, large-v3)
        """
        self.model_name = model
        self.model = None
        self._whisper_available = self._check_whisper()
        logger.info(f"AudioService initialized with model: {model}")

    def _check_whisper(self) -> bool:
        """Check if Whisper is available"""
        try:
            import whisper

            self.model = whisper.load_model(self.model_name)
            return True
        except ImportError:
            logger.warning("Whisper not installed. Run: pip install openai-whisper")
            return False
        except Exception as e:
            logger.warning(f"Whisper not available: {e}")
            return False

    def transcribe(
        self, audio_path: str, language: str | None = None, task: str = "transcribe"
    ) -> dict[str, Any]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Source language (auto-detect if None)
            task: "transcribe" or "translate" (to English)

        Returns:
            dict with transcription text and metadata
        """
        if not self._whisper_available:
            return self._ffmpeg_fallback(audio_path)

        try:
            path = Path(audio_path)
            if not path.exists():
                return {"error": f"Audio file not found: {audio_path}"}

            options = {"task": task}
            if language:
                options["language"] = language

            result = self.model.transcribe(str(path), **options)

            logger.info(f"Audio transcribed: {audio_path}")
            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "model": self.model_name,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"error": str(e), "text": None, "success": False}

    def _ffmpeg_fallback(self, audio_path: str) -> dict[str, Any]:
        """Fallback using ffmpeg for basic audio info"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    audio_path,
                ],
                capture_output=True,
                text=True,
            )
            return {
                "error": "Whisper not installed - audio info only",
                "audio_info": result.stdout,
                "text": None,
                "success": False,
            }
        except Exception:
            return {
                "error": "Whisper not installed. Run: pip install openai-whisper",
                "text": None,
                "success": False,
            }

    def translate_to_english(self, audio_path: str) -> dict[str, Any]:
        """Transcribe and translate audio to English"""
        return self.transcribe(audio_path, task="translate")

    def detect_language(self, audio_path: str) -> dict[str, Any]:
        """Detect the language of audio"""
        result = self.transcribe(audio_path)
        if result.get("success"):
            return {
                "language": result.get("language"),
                "confidence": "high" if result.get("language") else "low",
            }
        return {"error": result.get("error")}


# Singleton instance
_audio_service: AudioService | None = None


def get_audio_service() -> AudioService:
    """Get or create the audio service singleton"""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
