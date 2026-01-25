# Trinity Score: 94.0 (Phase 30 Multimodal Services Refactoring)
"""Multimodal Services Integration - Vision and Audio Processing"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Service availability flags
_SERVICES_AVAILABLE = False

try:
    from services.audio_service import get_audio_service
    from services.vision_service import get_vision_service

    _SERVICES_AVAILABLE = True
except ImportError:
    logger.warning("Vision/Audio services not available - using fallback mode")


class MultimodalServiceManager:
    """Manages vision and audio services for multimodal RAG.

    Trinity Score: 眞95% 善93% 美94% 孝92% 永91%
    """

    def __init__(self) -> None:
        self.vision_service = None
        self.audio_service = None

        if _SERVICES_AVAILABLE:
            try:
                self.vision_service = get_vision_service()
                self.audio_service = get_audio_service()
                logger.info("Multimodal services initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize multimodal services: %s", str(e))
                self.vision_service = None
                self.audio_service = None
        else:
            logger.warning("Multimodal services not available - using fallback mode")

    def is_vision_available(self) -> bool:
        """Check if vision service is available."""
        return self.vision_service is not None

    def is_audio_available(self) -> bool:
        """Check if audio service is available."""
        return self.audio_service is not None

    async def analyze_image(
        self, image_path: str, prompt: str, language: str = "ko"
    ) -> dict[str, Any]:
        """Analyze image using vision service.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            language: Language for analysis

        Returns:
            Analysis result
        """
        if not self.vision_service:
            return {"success": False, "error": "Vision service not available"}

        try:
            result = self.vision_service.analyze_image(
                image_path=image_path,
                prompt=prompt,
                language=language,
            )
            return result
        except Exception as e:
            logger.error("Image analysis failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def extract_text_from_image(self, image_path: str) -> dict[str, Any]:
        """Extract text from image using OCR.

        Args:
            image_path: Path to image file

        Returns:
            OCR result
        """
        if not self.vision_service:
            return {"success": False, "error": "Vision service not available"}

        try:
            result = self.vision_service.extract_text(image_path)
            return result
        except Exception as e:
            logger.error("OCR failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def transcribe_audio(self, audio_path: str) -> dict[str, Any]:
        """Transcribe audio using audio service.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription result
        """
        if not self.audio_service:
            return {"success": False, "error": "Audio service not available"}

        try:
            result = self.audio_service.transcribe(audio_path)
            return result
        except Exception as e:
            logger.error("Audio transcription failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def get_service_status(self) -> dict[str, bool]:
        """Get status of multimodal services."""
        return {
            "vision_available": self.is_vision_available(),
            "audio_available": self.is_audio_available(),
            "services_initialized": _SERVICES_AVAILABLE,
        }


# Global service manager instance
_service_manager = MultimodalServiceManager()


def get_service_manager() -> MultimodalServiceManager:
    """Get the global multimodal service manager."""
    return _service_manager


def process_image_for_rag(image_path: str) -> dict[str, Any]:
    """Process an image for RAG indexing.

    Args:
        image_path: Path to image file

    Returns:
        Processing result with metadata
    """
    try:
        path = Path(image_path)
        if not path.exists():
            logger.warning("이미지 파일 없음: %s", image_path)
            return {"error": f"Image not found: {image_path}"}

        manager = get_service_manager()

        # Extract text/OCR
        ocr_result = manager.extract_text_from_image(str(path))
        extracted_text = ""
        if ocr_result.get("success") and ocr_result.get("description"):
            extracted_text = ocr_result["description"]

        # Vision analysis
        analysis_result = manager.analyze_image(
            image_path=str(path),
            prompt="Describe this image in detail for search and retrieval purposes.",
            language="ko",
        )
        description = ""
        vision_model = None
        if analysis_result.get("success"):
            description = analysis_result.get("description", "")
            vision_model = analysis_result.get("model")

        return {
            "path": str(path),
            "name": path.name,
            "size": path.stat().st_size,
            "type": path.suffix,
            "indexed": True,
            "extracted_text": extracted_text,
            "description": description,
            "vision_model": vision_model,
            "processing_success": True,
        }
    except (FileNotFoundError, OSError, PermissionError) as e:
        logger.warning("이미지 처리 실패 (파일 시스템 에러): %s", str(e))
        return {"error": str(e), "processing_success": False}
    except Exception as e:
        logger.debug("이미지 처리 중 예상치 못한 에러: %s", str(e))
        return {"error": str(e), "processing_success": False}


def process_audio_for_rag(audio_path: str) -> dict[str, Any]:
    """Process an audio file for RAG indexing.

    Args:
        audio_path: Path to audio file

    Returns:
        Processing result with transcription
    """
    try:
        path = Path(audio_path)
        if not path.exists():
            logger.warning("오디오 파일 없음: %s", audio_path)
            return {"error": f"Audio not found: {audio_path}"}

        manager = get_service_manager()

        # Transcribe audio
        transcription_result = manager.transcribe_audio(str(path))

        transcription = ""
        language = None
        audio_model = None
        segments_count = 0

        if transcription_result.get("success"):
            transcription = transcription_result.get("text", "")
            language = transcription_result.get("language")
            audio_model = transcription_result.get("model")
            segments_count = len(transcription_result.get("segments", []))

        return {
            "path": str(path),
            "name": path.name,
            "size": path.stat().st_size,
            "type": path.suffix,
            "indexed": True,
            "transcription": transcription,
            "language": language,
            "audio_model": audio_model,
            "segments_count": segments_count,
            "processing_success": True,
        }
    except (FileNotFoundError, OSError, PermissionError) as e:
        logger.warning("오디오 처리 실패 (파일 시스템 에러): %s", str(e))
        return {"error": str(e), "processing_success": False}
    except Exception as e:
        logger.debug("오디오 처리 중 예상치 못한 에러: %s", str(e))
        return {"error": str(e), "processing_success": False}
