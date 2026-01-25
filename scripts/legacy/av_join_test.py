#!/usr/bin/env python3
"""
AVJoinEngine 독립 테스트 스크립트
AFO 왕국의 AV JOIN 기능을 독립적으로 테스트
"""

import logging
from pathlib import Path
from typing import Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AVJoinEngine:
    """
    MoviePy 기반 AV 합성 엔진
    영상 + 음악 → 최종 숏폼 AV 자동 생성
    """

    def __init__(self) -> None:
        self.moviepy_available = self._check_moviepy()
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_moviepy(self) -> bool:
        """
        MoviePy 라이브러리 사용 가능 여부 확인
        """
        try:
            from moviepy import AudioFileClip, VideoFileClip

            logger.info("✅ MoviePy 라이브러리 사용 가능")
            return True
        except ImportError:
            logger.warning("❌ MoviePy 라이브러리를 찾을 수 없음 - pip install moviepy 필요")
            return False

    def _check_ffmpeg(self) -> bool:
        """
        Ffmpeg 사용 가능 여부 확인
        """
        import subprocess

        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info("✅ ffmpeg 사용 가능")
                return True
            logger.warning("❌ ffmpeg 실행 실패")
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("❌ ffmpeg를 찾을 수 없음 - brew install ffmpeg 필요")
            return False

    def join_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        duration_match: str = "min",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        오디오와 비디오를 합성하여 최종 AV 파일 생성
        """
        if not self.moviepy_available:
            return {
                "success": False,
                "error": "MoviePy 라이브러리가 설치되지 않음",
                "install_command": "pip install moviepy",
                "fallback_available": self.ffmpeg_available,
            }

        try:
            from moviepy import AudioFileClip, VideoFileClip

            # 파일 존재 확인
            if not Path(video_path).exists():
                return {
                    "success": False,
                    "error": f"비디오 파일을 찾을 수 없음: {video_path}",
                }

            if not Path(audio_path).exists():
                return {
                    "success": False,
                    "error": f"오디오 파일을 찾을 수 없음: {audio_path}",
                }

            # 비디오와 오디오 로드
            logger.info(f"🎬 비디오 로드 중: {video_path}")
            video = VideoFileClip(video_path)

            logger.info(f"🎵 오디오 로드 중: {audio_path}")
            audio = AudioFileClip(audio_path)

            # Duration 맞춤 처리
            video_duration = video.duration
            audio_duration = audio.duration

            logger.info(f"🎬 비디오 길이: {video_duration:.2f}초")
            logger.info(f"🎵 오디오 길이: {audio_duration:.2f}초")

            if duration_match == "min":
                # 짧은 쪽에 맞춰 자르기
                target_duration = min(video_duration, audio_duration)
                logger.info(f"🎯 Duration 맞춤: {target_duration:.2f}초 (짧은 쪽 기준)")

                if video_duration > target_duration:
                    video = video.subclip(0, target_duration)
                if audio_duration > target_duration:
                    audio = audio.subclip(0, target_duration)

            # Dry run 모드
            if dry_run:
                result = {
                    "success": True,
                    "mode": "dry_run",
                    "video_path": video_path,
                    "audio_path": audio_path,
                    "output_path": output_path,
                    "original_video_duration": video_duration,
                    "original_audio_duration": audio_duration,
                    "final_duration": min(video_duration, audio_duration),
                    "render_ready": True,
                    "av_join_planned": True,
                }
                logger.info("🎬 AV JOIN dry run 완료")
                return result

            # 오디오를 비디오에 설정 (MoviePy 방식)
            logger.info("🎵 오디오를 비디오에 설정 중...")
            # MoviePy에서 오디오를 비디오에 할당하는 올바른 방식
            video.audio = audio  # VideoFileClip.audio 속성에 직접 할당
            final_video = video

            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 렌더링 (WET 모드)
            logger.info(f"🎬 AV 렌더링 시작: {output_path}")

            # 고품질 렌더링 설정
            final_video.write_videofile(
                output_path,
                fps=30,  # TikTok 표준
                codec="libx264",
                audio_codec="aac",
                preset="medium",  # 속도 vs 품질 밸런스
                bitrate="8000k",  # 고품질 비트레이트
                audio_bitrate="192k",
                threads=4,  # 병렬 처리
            )

            # 결과 검증
            if Path(output_path).exists():
                output_size = Path(output_path).stat().st_size
                result = {
                    "success": True,
                    "mode": "wet_run",
                    "output_path": output_path,
                    "file_size_bytes": output_size,
                    "file_size_mb": round(output_size / (1024 * 1024), 2),
                    "duration": final_video.duration,
                    "resolution": f"{final_video.w}x{final_video.h}",
                    "fps": 30,
                    "video_codec": "libx264",
                    "audio_codec": "aac",
                    "av_join_completed": True,
                }
                logger.info(f"✅ AV JOIN 완료: {output_path} ({result['file_size_mb']}MB)")
                return result
            return {
                "success": False,
                "error": f"출력 파일이 생성되지 않음: {output_path}",
            }

        except Exception as e:
            logger.error(f"❌ AV JOIN 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "video_path": video_path,
                "audio_path": audio_path,
                "ffmpeg_fallback": self.ffmpeg_available,
            }


if __name__ == "__main__":
    print("🎬 AFO 왕국 AV JOIN 엔진 독립 테스트")
    print("=" * 50)

    engine = AVJoinEngine()
    print(f"MPS GPU 사용 가능: {__import__('torch').backends.mps.is_available()}")

    # 실제 존재하는 파일로 테스트
    test_video = "artifacts/capcut_real_shortform.mp4"
    test_audio = "artifacts/fallback_silence.m4a"
    test_output = "artifacts/av_join_test.mp4"

    print("테스트 파일 존재 확인:")
    print(f"비디오: {Path(test_video).exists()}")
    print(f"오디오: {Path(test_audio).exists()}")

    # Dry run 테스트
    print("\n🎬 Dry run 테스트...")
    dry_result = engine.join_audio_video(test_video, test_audio, test_output, dry_run=True)

    print("📊 Dry run 결과:")
    print(f"✅ 성공: {dry_result.get('success', False)}")
    if dry_result.get("success"):
        print(f"🎬 비디오 길이: {dry_result.get('original_video_duration', 0):.2f}초")
        print(f"🎵 오디오 길이: {dry_result.get('original_audio_duration', 0):.2f}초")
        print(f"🎯 최종 길이: {dry_result.get('final_duration', 0):.2f}초")
        print("✅ AV JOIN 엔진 정상 작동!")

        # Wet run 테스트 (자동 실행)
        print("\n🎬 Wet run 테스트 (자동 실행)...")
        wet_result = engine.join_audio_video(test_video, test_audio, test_output, dry_run=False)
        print("📊 Wet run 결과:")
        print(f"✅ 성공: {wet_result.get('success', False)}")
        if wet_result.get("success"):
            print(f"📁 파일 크기: {wet_result.get('file_size_mb', 0)}MB")
            print(f"⏱️ 길이: {wet_result.get('duration', 0):.2f}초")
            print(f"📐 해상도: {wet_result.get('resolution', 'N/A')}")
            print(f"🎬 출력 파일: {wet_result.get('output_path', 'N/A')}")
            print("🎉 AFO 왕국의 첫 번째 완전 AV 탄생!")

            # 파일 존재 확인
            if Path(test_output).exists():
                print(f"✅ 출력 파일 확인됨: {Path(test_output).stat().st_size} bytes")
            else:
                print("❌ 출력 파일이 생성되지 않음")
        else:
            print(f"❌ 오류: {wet_result.get('error', '알 수 없는 오류')}")
    else:
        print(f"❌ Dry run 실패: {dry_result.get('error', '알 수 없는 오류')}")
        if not engine.moviepy_available:
            print("💡 MoviePy 설치 필요: pip install moviepy")
        if not engine.ffmpeg_available:
            print("💡 ffmpeg 설치 필요: brew install ffmpeg")
