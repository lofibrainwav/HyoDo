#!/usr/bin/env python3
"""
AVJoinEngine - MoviePy 기반 오디오-비디오 합성 엔진
AFO 왕국의 멀티모달 파이프라인 최종 단계: 영상 + 음악 → 완전 AV

TimelineState SSOT로 영상과 음악을 자동으로 합성하여 숏폼 콘텐츠 완성.
"""

import logging
from pathlib import Path
from typing import Any

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

        Returns:
            bool: MoviePy 사용 가능 여부
        """
        try:
            from moviepy import AudioFileClip, VideoFileClip  # noqa: F401

            logger.info("✅ MoviePy 라이브러리 사용 가능")
            return True
        except ImportError:
            logger.warning("❌ MoviePy 라이브러리를 찾을 수 없음 - pip install moviepy 필요")
            return False

    def _check_ffmpeg(self) -> bool:
        """
        ffmpeg 사용 가능 여부 확인

        Returns:
            bool: ffmpeg 사용 가능 여부
        """
        import subprocess

        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logger.info("✅ ffmpeg 사용 가능")
                return True
            else:
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

        Args:
            video_path: 입력 비디오 파일 경로
            audio_path: 입력 오디오 파일 경로
            output_path: 출력 AV 파일 경로
            duration_match: 길이 맞춤 방식 ("min": 짧은 쪽 맞춤, "max": 긴 쪽에 패딩)
            dry_run: 실제 렌더링 없이 계획만 생성

        Returns:
            합성 결과 정보
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

            elif duration_match == "max":
                # 긴 쪽에 맞춰 패딩 (아직 구현되지 않음)
                target_duration = max(video_duration, audio_duration)
                logger.info(f"🎯 Duration 맞춤: {target_duration:.2f}초 (긴 쪽 기준)")

                # 긴 쪽에 맞춰 패딩하는 로직 (미래 구현)
                # video_padding = target_duration - video_duration
                # audio_padding = target_duration - audio_duration

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

            # 오디오를 비디오에 설정
            logger.info("🎵 오디오를 비디오에 설정 중...")
            final_video = video.set_audio(audio)

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
                verbose=False,
                logger=None,
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
            else:
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

    def join_with_timeline_state(
        self,
        timeline_state: dict[str, Any],
        video_path: str,
        audio_path: str,
        output_path: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        TimelineState 기반 AV JOIN (메타데이터 포함)

        Args:
            timeline_state: TimelineState 정보
            video_path: 비디오 파일 경로
            audio_path: 오디오 파일 경로
            output_path: 출력 경로
            dry_run: Dry run 모드

        Returns:
            AV JOIN 결과 + TimelineState 메타데이터
        """
        result = self.join_audio_video(video_path, audio_path, output_path, dry_run=dry_run)

        if result["success"]:
            # TimelineState 메타데이터 추가
            result["timeline_state"] = timeline_state
            result["title"] = timeline_state.get("title", "AFO Kingdom AV")
            result["sections_count"] = len(timeline_state.get("sections", []))
            result["music_style"] = timeline_state.get("music", {}).get("style", "epic_orchestral")

        return result

    def create_complete_av_from_timeline(
        self,
        timeline_state: dict[str, Any],
        video_path: str,
        audio_path: str,
        output_path: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        TimelineState 하나로 완전 자동 AV 생성
        (미래: CapCut + MusicGen 자동 호출 통합)

        Args:
            timeline_state: TimelineState
            video_path: 입력 비디오 경로
            audio_path: 입력 오디오 경로
            output_path: 출력 AV 경로
            dry_run: Dry run 모드

        Returns:
            완전 자동 AV 생성 결과
        """
        logger.info("🎬 TimelineState 기반 완전 자동 AV 생성 시작")

        # 현재는 수동 파일 기반 (미래: 자동 생성 통합)
        result = self.join_with_timeline_state(
            timeline_state, video_path, audio_path, output_path, dry_run
        )

        if result["success"]:
            result["complete_av_generated"] = True
            result["pipeline"] = "ABSORB → GENERATE → FANOUT → JOIN → RENDER"
            logger.info("✅ 완전 자동 AV 생성 완료")

        return result


# 글로벌 AVJoinEngine 인스턴스
_av_join_engine = None


def get_av_join_engine() -> AVJoinEngine:
    """
    AVJoinEngine 싱글톤 인스턴스 반환

    Returns:
        AVJoinEngine 인스턴스
    """
    global _av_join_engine
    if _av_join_engine is None:
        _av_join_engine = AVJoinEngine()
    return _av_join_engine


def join_audio_video_simple(
    video_path: str, audio_path: str, output_path: str, dry_run: bool = False
) -> dict[str, Any]:
    """
    간단한 AV JOIN 편의 함수

    Args:
        video_path: 비디오 파일 경로
        audio_path: 오디오 파일 경로
        output_path: 출력 파일 경로
        dry_run: Dry run 모드

    Returns:
        AV JOIN 결과
    """
    engine = get_av_join_engine()
    return engine.join_audio_video(video_path, audio_path, output_path, dry_run=dry_run)


if __name__ == "__main__":
    # 테스트 실행
    print("🎬 AFO 왕국 AV JOIN 엔진 테스트")
    print("=" * 50)

    engine = get_av_join_engine()

    # 테스트 파일 경로 (실제로는 artifacts/에서 가져옴)
    test_video = "artifacts/sample_video.mp4"
    test_audio = "artifacts/mlx_music_test.wav"
    test_output = "artifacts/av_join_test.mp4"

    # Dry run 테스트
    print("🎬 Dry run 테스트...")
    dry_result = engine.join_audio_video(test_video, test_audio, test_output, dry_run=True)

    print("📊 Dry run 결과:")
    print(f"✅ 성공: {dry_result.get('success', False)}")
    print(f"🎬 비디오: {dry_result.get('video_path', 'N/A')}")
    print(f"🎵 오디오: {dry_result.get('audio_path', 'N/A')}")
    print(f"📤 출력: {dry_result.get('output_path', 'N/A')}")
    print(f"🎯 최종 길이: {dry_result.get('final_duration', 0):.2f}초")

    if dry_result.get("success"):
        print("\n🎬 Wet run 테스트...")
        wet_result = engine.join_audio_video(test_video, test_audio, test_output, dry_run=False)

        print("📊 Wet run 결과:")
        print(f"✅ 성공: {wet_result.get('success', False)}")
        if wet_result.get("success"):
            print(f"📁 파일 크기: {wet_result.get('file_size_mb', 0)}MB")
            print(f"⏱️ 길이: {wet_result.get('duration', 0):.2f}초")
            print(f"📐 해상도: {wet_result.get('resolution', 'N/A')}")
            print("🎉 AFO 왕국의 첫 번째 완전 AV 탄생!")
        else:
            print(f"❌ 오류: {wet_result.get('error', '알 수 없는 오류')}")
    else:
        print("❌ Dry run 실패 - 파일 경로 확인 필요")
        if not engine.moviepy_available:
            print("💡 MoviePy 설치 필요: pip install moviepy")
        if not engine.ffmpeg_available:
            print("💡 ffmpeg 설치 필요: brew install ffmpeg")
