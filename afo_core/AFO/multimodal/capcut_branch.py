"""
CapCutBranch - CapCut 스타일 비디오 편집 통합
MoviePy 기반 프로그래머틱 편집으로 TikTok급 숏폼 콘텐츠 자동 생성

오픈소스 대안: MoviePy (프로그래머틱 편집), OpenCut (UI 클론)
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CapCutBranch:
    """
    CapCut 스타일 비디오 편집 브랜치
    TimelineState를 TikTok급 숏폼으로 변환
    """

    def __init__(self) -> None:
        self.moviepy_available = self._check_moviepy()
        self.templates = self._load_capcut_templates()

    def _check_moviepy(self) -> bool:
        """
        MoviePy 라이브러리 사용 가능 여부 확인

        Returns:
            bool: MoviePy 사용 가능 여부
        """
        try:
            from moviepy import (  # noqa: F401
                ColorClip,
                CompositeVideoClip,
                ImageClip,
                concatenate_videoclips,
            )

            logger.info("MoviePy 라이브러리 사용 가능")
            return True
        except ImportError:
            logger.warning("MoviePy 라이브러리를 찾을 수 없음 - pip install moviepy 필요")
            return False

    def _load_capcut_templates(self) -> dict[str, Any]:
        """
        CapCut 스타일 템플릿 로드

        Returns:
            템플릿 딕셔너리
        """
        return {
            "tiktok_trend": {
                "font": "Arial-Bold",
                "font_size": 60,
                "text_color": "white",
                "stroke_color": "black",
                "stroke_width": 3,
                "bg_music": "trending_beat.mp3",
                "transitions": ["fade", "slide"],
                "effects": ["zoom_in", "text_pop"],
            },
            "story_time": {
                "font": "Helvetica",
                "font_size": 48,
                "text_color": "#FF6B6B",
                "bg_music": "emotional_piano.mp3",
                "transitions": ["dissolve", "wipe"],
                "effects": ["blur_bg", "focus_text"],
            },
            "dance_challenge": {
                "font": "Impact",
                "font_size": 72,
                "text_color": "#FFD93D",
                "stroke_color": "#FF6B6B",
                "stroke_width": 4,
                "bg_music": "dance_beat.mp3",
                "transitions": ["flash", "spin"],
                "effects": ["color_pop", "speed_ramp"],
            },
        }

    def create_capcut_style_video(
        self,
        timeline_sections: list[dict[str, Any]],
        input_video: str,
        output_path: str,
        template: str = "tiktok_trend",
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        TimelineState를 CapCut 스타일 비디오로 변환

        Args:
            timeline_sections: TimelineState sections
            input_video: 입력 비디오 파일 경로
            output_path: 출력 파일 경로
            template: CapCut 템플릿 이름
            dry_run: 실제 렌더링 없이 계획만 생성

        Returns:
            편집 결과 정보
        """
        if not self.moviepy_available:
            return {
                "success": True,
                "mode": "dry_run_fallback",
                "error": "MoviePy 라이브러리가 설치되지 않음 - dry run 모드로 진행",
                "install_command": "pip install moviepy",
                "dry_run_plan": self._generate_dry_run_plan(
                    timeline_sections, input_video, output_path, template
                ),
            }

        try:
            from moviepy import (
                CompositeVideoClip,
                TextClip,
                VideoFileClip,
                concatenate_videoclips,
            )

            # 입력 비디오 로드
            if not Path(input_video).exists():
                return {
                    "success": False,
                    "error": f"입력 비디오 파일을 찾을 수 없음: {input_video}",
                    "dry_run_plan": self._generate_dry_run_plan(
                        timeline_sections, input_video, output_path, template
                    ),
                }

            video = VideoFileClip(input_video)

            # 템플릿 적용
            template_config = self.templates.get(template, self.templates["tiktok_trend"])

            # 클립 편집
            edited_clips = []
            for section in timeline_sections:
                start_time = section.get("start", 0)
                end_time = section.get("end", start_time + 5)
                text_content = section.get("text", "")

                # 시간 범위로 클립 자르기
                subclip = video.subclip(start_time, end_time)

                # 텍스트 오버레이 적용 (CapCut 스타일)
                if text_content:
                    txt_clip = (
                        TextClip(
                            text_content,
                            fontsize=template_config["font_size"],
                            color=template_config["text_color"],
                            font=template_config["font"],
                            stroke_color=template_config.get("stroke_color", "black"),
                            stroke_width=template_config.get("stroke_width", 0),
                        )
                        .set_position("center")
                        .set_duration(subclip.duration)
                    )

                    subclip = CompositeVideoClip([subclip, txt_clip])

                # 효과 적용
                effect = section.get("video_effect", "")
                subclip = self._apply_capcut_effect(subclip, effect)

                edited_clips.append(subclip)

            # 클립 합치기
            if len(edited_clips) == 1:
                final_video = edited_clips[0]
            else:
                final_video = concatenate_videoclips(edited_clips, method="compose")

            # Dry run 모드
            if dry_run:
                result = {
                    "success": True,
                    "mode": "dry_run",
                    "template_used": template,
                    "sections_processed": len(timeline_sections),
                    "total_duration": sum(clip.duration for clip in edited_clips),
                    "output_path": output_path,
                    "render_ready": True,
                    "capcut_style_applied": True,
                }
                logger.info(f"CapCut 스타일 dry run 완료: {len(edited_clips)}개 클립 처리")
                return result

            # 실제 렌더링 (WET 모드)
            logger.info(f"CapCut 스타일 렌더링 시작: {output_path}")
            final_video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")

            return {
                "success": True,
                "mode": "wet_run",
                "template_used": template,
                "output_path": output_path,
                "duration": final_video.duration,
                "resolution": f"{final_video.w}x{final_video.h}",
                "capcut_style_rendered": True,
            }

        except Exception as e:
            logger.error(f"CapCut 스타일 편집 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "template_used": template,
                "dry_run_plan": self._generate_dry_run_plan(
                    timeline_sections, input_video, output_path, template
                ),
            }

    def _apply_capcut_effect(self, clip: Any, effect: str) -> Any:
        """
        CapCut 스타일 효과 적용

        Args:
            clip: MoviePy 클립 객체
            effect: 효과 이름

        Returns:
            효과가 적용된 클립
        """
        try:
            if effect == "zoom_in":
                # 줌인 효과
                return clip.resize(lambda t: 1 + 0.3 * t / clip.duration)
            elif effect == "fade_transition":
                # 페이드 트랜지션
                return clip.fadein(0.5).fadeout(0.5)
            elif effect == "speed_ramp":
                # 속도 램프 (빨라지기)
                return clip.speedx(lambda t: 1 + 0.5 * t / clip.duration)
            elif effect == "color_pop":
                # 컬러 팝 효과
                return clip.set_make_frame(lambda t, frame: self._apply_color_pop(frame))
            elif effect == "blur_bg":
                # 배경 블러 (텍스트 포커스)
                return clip.resize(lambda t: 1.1 if t > clip.duration * 0.2 else 1.0)
            else:
                return clip
        except Exception as e:
            logger.warning(f"효과 적용 실패 ({effect}): {e}")
            return clip

    def _apply_color_pop(self, frame: Any) -> Any:
        """
        컬러 팝 효과 적용 (단순화된 버전)

        Args:
            frame: 비디오 프레임

        Returns:
            효과가 적용된 프레임
        """
        # 실제로는 더 복잡한 이미지 처리 필요
        # 여기서는 간단한 대비 증가로 시뮬레이션
        try:
            import numpy as np

            frame_array = np.array(frame)
            # 대비 증가 (간단한 컬러 팝 시뮬레이션)
            frame_array = np.clip(frame_array * 1.2, 0, 255).astype(np.uint8)
            return frame_array
        except ImportError:
            return frame

    def _generate_dry_run_plan(
        self,
        timeline_sections: list[dict[str, Any]],
        input_video: str,
        output_path: str,
        template: str,
    ) -> dict[str, Any]:
        """
        Dry run용 계획 생성

        Args:
            timeline_sections: TimelineState sections
            input_video: 입력 비디오
            output_path: 출력 경로
            template: 템플릿 이름

        Returns:
            Dry run 계획
        """
        plan = {
            "input_video": input_video,
            "output_path": output_path,
            "template": template,
            "sections_plan": [],
        }

        for i, section in enumerate(timeline_sections):
            plan["sections_plan"].append(
                {
                    "section": i,
                    "time_range": f"{section.get('start', 0)}-{section.get('end', 5)}",
                    "text": section.get("text", ""),
                    "effect": section.get("video", ""),
                    "capcut_style": True,
                }
            )

        return plan

    def get_available_templates(self) -> list[str]:
        """
        사용 가능한 CapCut 템플릿 리스트 반환

        Returns:
            템플릿 이름 리스트
        """
        return list(self.templates.keys())


# 글로벌 CapCutBranch 인스턴스
_capcut_branch = None


def get_capcut_branch() -> CapCutBranch:
    """
    CapCutBranch 싱글톤 인스턴스 반환

    Returns:
        CapCutBranch 인스턴스
    """
    global _capcut_branch
    if _capcut_branch is None:
        _capcut_branch = CapCutBranch()
    return _capcut_branch


def capcut_edit_video(
    timeline: list[dict[str, Any]],
    input_video: str,
    output_path: str,
    template: str = "tiktok_trend",
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    CapCut 스타일 편집 편의 함수

    Args:
        timeline: TimelineState sections
        input_video: 입력 비디오 파일 경로
        output_path: 출력 파일 경로
        template: CapCut 템플릿 이름
        dry_run: 실제 렌더링 없이 계획만 생성

    Returns:
        편집 결과
    """
    capcut = get_capcut_branch()
    return capcut.create_capcut_style_video(timeline, input_video, output_path, template, dry_run)


if __name__ == "__main__":
    # 테스트용 TimelineState
    test_timeline = [
        {"start": 0, "end": 5, "text": "AFO Kingdom!", "video": "zoom_in"},
        {"start": 5, "end": 10, "text": "영원히!", "video": "fade_transition"},
        {"start": 10, "end": 15, "text": "TikTok급!", "video": "color_pop"},
    ]

    # Dry run 테스트
    result = capcut_edit_video(
        test_timeline,
        "input_video.mp4",
        "capcut_style_output.mp4",
        template="tiktok_trend",
        dry_run=True,
    )

    print("CapCut 스타일 편집 테스트 결과:")
    print(f"성공: {result.get('success', False)}")
    print(f"모드: {result.get('mode', 'unknown')}")
    print(f"설치 명령: {result.get('install_command', 'N/A')}")
    if result.get("dry_run_plan"):
        plan = result["dry_run_plan"]
        print(f"계획된 섹션 수: {len(plan.get('sections_plan', []))}")
        print(f"템플릿: {plan.get('template', 'none')}")
    print(f"CapCut 스타일 적용: {result.get('capcut_style_applied', False)}")
