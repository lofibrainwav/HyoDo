# Trinity Score: 92.0 (Multimodal Vision)
"""
Vision Service for AFO Kingdom (눈/Eyes)
Uses Ollama qwen3-vl for image understanding and visual analysis.

2025 Best Practice: Local VLM for privacy and speed.
Uses LOCAL Ollama (host.docker.internal:11434) for GPU acceleration.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

# Local Ollama endpoint (accessible from Docker via host.docker.internal, localhost for local dev)
OLLAMA_HOST = settings.OLLAMA_BASE_URL


class VisionService:
    """
    Vision Service using Ollama Vision Language Models.
    Gives agents the ability to "see" and understand images.
    Uses LOCAL Ollama for GPU acceleration.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.VISION_MODEL
        self._ollama_available = self._check_ollama()
        logger.info(f"VisionService initialized with model: {self.model} (host: {OLLAMA_HOST})")

    def _check_ollama(self) -> bool:
        """Check if Ollama is available (uses LOCAL Ollama via OLLAMA_HOST)"""
        try:
            # Set OLLAMA_HOST env var for the ollama library
            os.environ["OLLAMA_HOST"] = OLLAMA_HOST
            import ollama

            models = ollama.list()
            logger.info(
                f"Connected to Ollama at {OLLAMA_HOST}, models: {len(models.get('models', []))}"
            )
            return True
        except Exception as e:
            logger.warning(f"Ollama not available at {OLLAMA_HOST}: {e}")
            return False

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail.",
        language: str = "ko",
    ) -> dict[str, Any]:
        """
        Analyze an image using Ollama VLM.

        Args:
            image_path: Path to the image file
            prompt: Question or instruction about the image
            language: Response language (ko, en, etc.)

        Returns:
            dict with description and metadata
        """
        if not self._ollama_available:
            return {
                "error": "Ollama not available",
                "description": None,
                "model": self.model,
            }

        try:
            import ollama

            # Adjust prompt for language
            if language == "ko":
                system_prompt = "당신은 이미지를 분석하는 AI입니다. 한국어로 상세히 설명하세요."
            else:
                system_prompt = "You are an AI that analyzes images. Describe in detail."

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt, "images": [image_path]},
                ],
            )

            description = response["message"]["content"]

            logger.info(f"Image analyzed: {image_path}")
            return {
                "description": description,
                "model": self.model,
                "image_path": image_path,
                "prompt": prompt,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "description": None,
                "model": self.model,
                "success": False,
            }

    def detect_objects(self, image_path: str) -> dict[str, Any]:
        """Detect and list objects in an image"""
        prompt = "List all objects visible in this image. Format: - object1\n- object2\n..."
        return self.analyze_image(image_path, prompt, language="en")

    def extract_text(self, image_path: str) -> dict[str, Any]:
        """Extract text/OCR from an image"""
        prompt = "Extract all visible text from this image. If no text is visible, say 'No text detected'."
        return self.analyze_image(image_path, prompt, language="en")

    def answer_question(self, image_path: str, question: str) -> dict[str, Any]:
        """Visual Question Answering (VQA)"""
        return self.analyze_image(image_path, question)


# Singleton instance
_vision_service: VisionService | None = None


def get_vision_service() -> VisionService:
    """Get or create the vision service singleton"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
