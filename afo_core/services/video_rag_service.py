# Trinity Score: 92.0 (Multimodal Video RAG)
"""
Video RAG Service for AFO Kingdom
Combines Vision + Audio for full video understanding.

2025 Best Practice: Video-RAG with keyframes + ASR + OCR
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from services.audio_service import get_audio_service
from services.vision_service import get_vision_service

logger = logging.getLogger(__name__)


class VideoRAGService:
    """
    Video RAG Service for full video understanding.
    Extracts keyframes, transcribes audio, and combines for RAG.
    """

    def __init__(self) -> None:
        self.vision = get_vision_service()
        self.audio = get_audio_service()
        self._ffmpeg_available = self._check_ffmpeg()
        logger.info("VideoRAGService initialized")

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except Exception:
            logger.warning("ffmpeg not available - video processing limited")
            return False

    def extract_audio(self, video_path: str, output_dir: str | None = None) -> str | None:
        """Extract audio track from video"""
        if not self._ffmpeg_available:
            logger.error("ffmpeg required for audio extraction")
            return None

        try:
            path = Path(video_path)
            if output_dir:
                audio_path = Path(output_dir) / f"{path.stem}_audio.wav"
            else:
                audio_path = path.parent / f"{path.stem}_audio.wav"

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(path),
                    "-vn",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    str(audio_path),
                ],
                capture_output=True,
                check=True,
            )

            logger.info(f"Audio extracted: {audio_path}")
            return str(audio_path)

        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None

    def extract_keyframes(
        self, video_path: str, num_frames: int = 5, output_dir: str | None = None
    ) -> list[str]:
        """Extract keyframes from video"""
        if not self._ffmpeg_available:
            logger.error("ffmpeg required for keyframe extraction")
            return []

        try:
            path = Path(video_path)
            out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())

            # Get video duration
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ],
                capture_output=True,
                text=True,
            )

            duration = float(result.stdout.strip())
            interval = duration / (num_frames + 1)

            frames = []
            for i in range(1, num_frames + 1):
                timestamp = i * interval
                frame_path = out_dir / f"frame_{i:03d}.jpg"

                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-ss",
                        str(timestamp),
                        "-i",
                        str(path),
                        "-vframes",
                        "1",
                        "-q:v",
                        "2",
                        str(frame_path),
                    ],
                    capture_output=True,
                    check=True,
                )

                frames.append(str(frame_path))

            logger.info(f"Extracted {len(frames)} keyframes from {video_path}")
            return frames

        except Exception as e:
            logger.error(f"Keyframe extraction failed: {e}")
            return []

    def process_video(
        self,
        video_path: str,
        num_frames: int = 5,
        transcribe: bool = True,
        language: str = "ko",
    ) -> dict[str, Any]:
        """
        Full video processing pipeline.

        Args:
            video_path: Path to video file
            num_frames: Number of keyframes to extract
            transcribe: Whether to transcribe audio
            language: Response language for descriptions

        Returns:
            dict with frame analysis, transcript, and combined text
        """
        results = {
            "video_path": video_path,
            "frames": [],
            "transcript": None,
            "combined_text": "",
            "success": True,
        }

        # 1. Extract and analyze keyframes
        keyframes = self.extract_keyframes(video_path, num_frames)
        for i, frame_path in enumerate(keyframes):
            analysis = self.vision.analyze_image(
                frame_path,
                prompt=(
                    f"프레임 {i + 1}: 이 장면을 설명하세요."
                    if language == "ko"
                    else f"Frame {i + 1}: Describe this scene."
                ),
                language=language,
            )
            results["frames"].append(
                {
                    "frame_number": i + 1,
                    "path": frame_path,
                    "description": analysis.get("description", ""),
                }
            )

        # 2. Extract and transcribe audio
        if transcribe:
            audio_path = self.extract_audio(video_path)
            if audio_path:
                transcript = self.audio.transcribe(audio_path, language)
                results["transcript"] = transcript

        # 3. Combine for RAG
        combined_parts = []

        # Add frame descriptions
        for frame in results["frames"]:
            if frame.get("description"):
                combined_parts.append(f"[Frame {frame['frame_number']}] {frame['description']}")

        # Add transcript
        if results["transcript"] and results["transcript"].get("text"):
            combined_parts.append(f"[Audio Transcript] {results['transcript']['text']}")

        results["combined_text"] = "\n\n".join(combined_parts)

        logger.info(f"Video processed: {video_path}")
        return results


# Singleton instance
_video_rag_service: VideoRAGService | None = None


def get_video_rag_service() -> VideoRAGService:
    """Get or create the video RAG service singleton"""
    global _video_rag_service
    if _video_rag_service is None:
        _video_rag_service = VideoRAGService()
    return _video_rag_service
