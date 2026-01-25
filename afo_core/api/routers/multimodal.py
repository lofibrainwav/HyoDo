# Trinity Score: 92.0 (Multimodal Integration)
"""
Multimodal Router for AFO Kingdom
Exposes Vision, Audio, and Video RAG services via REST API.

2025 Best Practice: Unified multimodal endpoint with graceful degradation.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multimodal", tags=["Multimodal"])


@shield(pillar="眞")
@router.get("/status")
async def get_multimodal_status() -> dict[str, Any]:
    """Get status of all multimodal services."""
    status = {
        "vision": {"available": False, "model": None},
        "audio": {"available": False, "model": None},
        "video": {"available": False, "dependencies": []},
    }

    # Check Vision Service
    try:
        from services.vision_service import get_vision_service

        vision = get_vision_service()
        status["vision"] = {
            "available": vision._ollama_available,
            "model": vision.model if vision._ollama_available else None,
        }
    except Exception as e:
        logger.warning(f"Vision service not available: {e}")

    # Check Audio Service
    try:
        from services.audio_service import get_audio_service

        audio = get_audio_service()
        status["audio"] = {
            "available": audio._whisper_available,
            "model": audio.model_name if audio._whisper_available else None,
        }
    except Exception as e:
        logger.warning(f"Audio service not available: {e}")

    # Check Video Service
    try:
        from services.video_rag_service import get_video_rag_service

        video = get_video_rag_service()
        status["video"] = {
            "available": video._ffmpeg_available,
            "dependencies": ["ffmpeg", "vision", "audio"],
        }
    except Exception as e:
        logger.warning(f"Video service not available: {e}")

    return status


@shield(pillar="眞")
@router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(default="Describe this image in detail."),
    language: str = Form(default="en"),
) -> dict[str, Any]:
    """
    Analyze an image using Vision AI (qwen3-vl).

    Args:
        file: Image file (jpg, png, webp)
        prompt: Analysis prompt
        language: Response language (en, ko)
    """
    try:
        from services.vision_service import get_vision_service

        vision = get_vision_service()

        if not vision._ollama_available:
            raise HTTPException(status_code=503, detail="Vision service not available")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = vision.analyze_image(tmp_path, prompt=prompt, language=language)
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@shield(pillar="眞")
@router.post("/audio/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    task: str = Form(default="transcribe"),
) -> dict[str, Any]:
    """
    Transcribe audio using Whisper.

    Args:
        file: Audio file (mp3, wav, m4a)
        language: Source language (auto-detect if None)
        task: "transcribe" or "translate" (to English)
    """
    try:
        from services.audio_service import get_audio_service

        audio = get_audio_service()

        if not audio._whisper_available:
            raise HTTPException(status_code=503, detail="Whisper not available")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = audio.transcribe(tmp_path, language=language, task=task)
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@shield(pillar="眞")
@router.post("/video/process")
async def process_video(
    file: UploadFile = File(...),
    num_frames: int = Form(default=5),
    transcribe: bool = Form(default=True),
    language: str = Form(default="ko"),
) -> dict[str, Any]:
    """
    Process video with keyframe extraction and audio transcription.

    Args:
        file: Video file (mp4, mov, avi)
        num_frames: Number of keyframes to extract
        transcribe: Whether to transcribe audio
        language: Response language for descriptions
    """
    try:
        from services.video_rag_service import get_video_rag_service

        video = get_video_rag_service()

        if not video._ffmpeg_available:
            raise HTTPException(status_code=503, detail="ffmpeg not available")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = video.process_video(
                tmp_path,
                num_frames=num_frames,
                transcribe=transcribe,
                language=language,
            )
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@shield(pillar="眞")
@router.post("/music/generate")
async def generate_music(request: dict[str, Any]) -> dict[str, Any]:
    """
    Generate music from TimelineState using MLX MusicGen.

    Args:
        request: Request containing timeline_state and generation parameters
    """
    try:
        timeline_state = request.get("timeline_state")
        if not timeline_state:
            raise HTTPException(status_code=400, detail="timeline_state is required")

        provider = request.get("provider", "mlx_musicgen")
        quality = request.get("quality", "high")

        # Import MLX MusicGen provider
        try:
            from AFO.multimodal.music_provider import get_music_router

            router = get_music_router()
            result = router.generate_music(
                timeline_state, quality=quality, local_only=True, max_cost=0.0
            )

            if result.get("success"):
                # Return audio file URL for frontend access
                audio_path = result.get("output_path", result.get("audio_path"))
                if audio_path:
                    # Convert to web-accessible URL
                    audio_url = f"/api/audio/{Path(audio_path).name}"
                    return {
                        "success": True,
                        "audio_path": audio_path,
                        "audio_url": audio_url,
                        "duration": result.get("duration", 30),
                        "title": timeline_state.get("title", "Generated Music"),
                        "provider": provider,
                    }

            return {
                "success": False,
                "error": result.get("error", "Music generation failed"),
                "details": result,
            }

        except ImportError:
            raise HTTPException(status_code=503, detail="Music generation service not available")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Music generation failed: {e!s}")


@shield(pillar="眞")
@router.get("/audio/{filename}")
async def get_audio_file(filename: str) -> Any:
    """
    Serve generated audio files.

    Args:
        filename: Audio file name
    """
    from fastapi.responses import FileResponse

    audio_path = Path("artifacts") / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(path=audio_path, media_type="audio/wav", filename=filename)


@shield(pillar="眞")
@router.post("/av/join")
async def join_audio_video(request: dict[str, Any]) -> dict[str, Any]:
    """
    Join audio and video files to create complete AV content.

    Args:
        request: Request containing video_path, audio_path, and output options
    """
    try:
        video_path = request.get("video_path")
        audio_path = request.get("audio_path")
        output_path = request.get(
            "output_path", f"artifacts/av_join_{int(__import__('time').time())}.mp4"
        )
        duration_match = request.get("duration_match", "min")
        timeline_state = request.get("timeline_state")

        if not video_path or not audio_path:
            raise HTTPException(status_code=400, detail="video_path and audio_path are required")

        # AV Join Engine 사용
        try:
            from AFO.multimodal.av_join_engine import get_av_join_engine

            engine = get_av_join_engine()

            if timeline_state:
                # TimelineState 기반 AV 생성
                result = engine.join_with_timeline_state(
                    timeline_state, video_path, audio_path, output_path
                )
            else:
                # 기본 AV JOIN
                result = engine.join_audio_video(
                    video_path, audio_path, output_path, duration_match=duration_match
                )

            if result.get("success"):
                # 웹 접근 가능한 URL로 변환
                output_filename = Path(output_path).name
                result["av_url"] = f"/api/av/{output_filename}"

            return result

        except ImportError:
            raise HTTPException(status_code=503, detail="AV Join engine not available")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AV join failed: {e}")
        raise HTTPException(status_code=500, detail=f"AV join failed: {e!s}")


@shield(pillar="眞")
@router.post("/av/create-complete")
async def create_complete_av(request: dict[str, Any]) -> dict[str, Any]:
    """
    Create complete AV from TimelineState (CapCut + MLX MusicGen + AV Join 자동 통합).

    Args:
        request: Request containing timeline_state and options
    """
    try:
        timeline_state = request.get("timeline_state")
        if not timeline_state:
            raise HTTPException(status_code=400, detail="timeline_state is required")

        # Phase 5: run_id 기반 출력 구조 (동시 실행 안전)
        import hashlib
        import time

        run_id = hashlib.sha256(
            f"{timeline_state.get('title', 'untitled')}_{int(time.time())}".encode()
        ).hexdigest()[:8]

        run_dir = Path("artifacts/runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # run_id 기반 파일 경로 설정
        music_path = run_dir / "music.wav"
        video_path = run_dir / "video.mp4"
        final_av_path = run_dir / "final.mp4"
        meta_path = run_dir / "meta.json"

        # 메타데이터 저장
        import json

        meta_data = {
            "run_id": run_id,
            "timeline_state": timeline_state,
            "created_at": time.time(),
            "status": "processing",
        }
        with open(meta_path, "w") as f:
            json.dump(meta_data, f, indent=2, default=str)

        try:
            # 1. MLX MusicGen으로 음악 생성
            from AFO.multimodal.music_provider import get_music_router

            music_router = get_music_router()
            music_result = music_router.generate_music(
                timeline_state,
                quality="excellent",
                local_only=True,
                max_cost=0.0,
                duration=30,  # 기본 30초
                output_path=f"artifacts/auto_music_{int(__import__('time').time())}.wav",
            )

            if not music_result.get("success"):
                return {
                    "success": False,
                    "error": f"Music generation failed: {music_result.get('error')}",
                    "stage": "music_generation",
                }

            audio_path = music_result["output_path"]
            logger.info(f"✅ Music generated: {audio_path}")

            # 2. CapCut + MLX 통합 어댑터 (Phase 5)
            video_path = request.get("video_path")
            if not video_path:
                # TimelineState 기반 샘플 영상 생성 (CapCut 자동화 대체)
                video_path = await _generate_sample_video(timeline_state)

            # MLX 실패 시 silence AAC 폴백 (Phase 5)
            audio_path_for_av = audio_path
            try:
                # 추가 검증: 실제로 생성된 파일이 있는지 확인
                if not Path(audio_path).exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")
            except Exception as audio_check_error:
                logger.warning(
                    f"MLX audio generation failed, using silence fallback: {audio_check_error}"
                )
                # Silence AAC 생성 (fail-closed 전략)
                from AFO.multimodal.av_join import make_silence_aac

                silence_path = Path(audio_path).parent / "silence_fallback.m4a"
                audio_path_for_av = make_silence_aac(30, silence_path)  # 30초 silence
                logger.info(f"Using silence fallback: {audio_path_for_av}")

            # 3. AV Join Engine로 완전 AV 생성
            from AFO.multimodal.av_join_engine import get_av_join_engine

            engine = get_av_join_engine()
            av_result = engine.create_complete_av_from_timeline(
                timeline_state,
                str(video_path),
                str(audio_path_for_av),
                str(final_av_path),
            )

            if av_result.get("success"):
                output_filename = final_av_path.name
                av_result.update(
                    {
                        "av_url": f"/api/av/runs/{run_id}/{output_filename}",
                        "run_id": run_id,
                        "music_path": audio_path,
                        "video_path": str(video_path),
                        "final_path": str(final_av_path),
                        "pipeline": "complete_auto",
                        "stages_completed": [
                            "music_generation",
                            "video_prep",
                            "av_join",
                        ],
                    }
                )

                # 메타데이터 업데이트
                meta_data["status"] = "completed"
                meta_data["files"] = {
                    "music": str(music_path),
                    "video": str(video_path),
                    "final": str(final_av_path),
                }
                with open(meta_path, "w") as f:
                    json.dump(meta_data, f, indent=2, default=str)

                logger.info(f"✅ Complete AV created: {final_av_path}")
                return av_result
            else:
                return {
                    "success": False,
                    "error": f"AV join failed: {av_result.get('error')}",
                    "stage": "av_join",
                    "music_path": audio_path,
                }

        except ImportError as e:
            raise HTTPException(status_code=503, detail=f"Required service not available: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete AV creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Complete AV creation failed: {e!s}")


async def _generate_sample_video(timeline_state: dict[str, Any]) -> str:
    """
    TimelineState 기반 샘플 비디오 생성 (CapCut 자동화 대체).

    Args:
        timeline_state: TimelineState dict

    Returns:
        생성된 비디오 파일 경로
    """
    try:
        import subprocess
        import tempfile

        # 간단한 FFmpeg 기반 샘플 비디오 생성
        title = timeline_state.get("title", "Sample Video")
        theme = timeline_state.get("theme", "modern")

        # 배경색상 테마별 설정
        theme_colors = {
            "epic": "0x2C1810",  # 어두운 브라운
            "modern": "0x1a1a2e",  # 어두운 블루
            "corporate": "0x2d3748",  # 그레이
        }
        bgcolor = theme_colors.get(theme, "0x1a1a2e")

        # 임시 비디오 파일 생성
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_path = tmp.name

        # FFmpeg 명령어로 간단한 비디오 생성
        duration = 30  # 30초
        resolution = "1920x1080"

        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"color=c={bgcolor}:s={resolution}:d={duration}",
            "-vf",
            f"drawtext=text='{title}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-y",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            logger.error(f"Sample video generation failed: {result.stderr}")
            # 폴백: 기존 샘플 사용
            return "artifacts/templates/default_video.mp4"

        logger.info(f"Sample video generated: {video_path}")
        return video_path

    except Exception as e:
        logger.error(f"Sample video generation error: {e}")
        return "artifacts/templates/default_video.mp4"


@shield(pillar="眞")
@router.get("/av/{filename}")
async def get_av_file(filename: str) -> Any:
    """
    Serve generated AV files.

    Args:
        filename: AV file name
    """
    from fastapi.responses import FileResponse

    av_path = Path("artifacts") / filename
    if not av_path.exists():
        raise HTTPException(status_code=404, detail="AV file not found")

    return FileResponse(path=av_path, media_type="video/mp4", filename=filename)
