"""
VideoBranch 세부 구현 - TimelineState의 video 지시어 → 실제 렌더링 파라미터 변환
멀티모달 병렬 처리의 비디오 브랜치 (FFmpeg/RunwayML API 연결 준비)
"""

from typing import Any

# Video 효과 맵 - 추상적 지시어를 실제 렌더링 파라미터로 변환
VIDEO_EFFECT_MAP = {
    "fade_in": {
        "effect": "opacity_transition",
        "duration": 2.0,
        "ease": "in_out",
        "start_opacity": 0.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "fade=t=in:st=0:d=2.0:alpha=1",
        "runwayml_params": {"transition": "fade_in", "duration_frames": 60},
    },
    "fade_out": {
        "effect": "opacity_transition",
        "duration": 2.0,
        "ease": "in_out",
        "start_opacity": 1.0,
        "end_opacity": 0.0,
        "ffmpeg_filter": "fade=t=out:st=0:d=2.0:alpha=1",
        "runwayml_params": {"transition": "fade_out", "duration_frames": 60},
    },
    "text_overlay": {
        "effect": "text_overlay",
        "position": "center",
        "animation": "slide_up",
        "font_size": 48,
        "font_family": "Arial-Bold",
        "color": "#FFFFFF",
        "duration": 3.0,
        "ffmpeg_filter": "drawtext=text='TITLE':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h-100*t/3.0",
        "runwayml_params": {
            "text": "TITLE",
            "animation": "slide_up",
            "position": "center",
        },
    },
    "zoom_effect": {
        "effect": "zoom",
        "scale_factor": 1.2,
        "duration": 1.0,
        "ease": "in_out",
        "anchor": "center",
        "ffmpeg_filter": "zoompan=z='min(max(zoom,pz),1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1*30:s=1920x1080",
        "runwayml_params": {"zoom": 1.2, "duration_frames": 30, "anchor": "center"},
    },
    "cut_sequence": {
        "effect": "hard_cut",
        "transition": "none",
        "duration": 0.0,
        "ffmpeg_filter": "select='not(mod(n,30))',setpts=N/FRAME_RATE/TB",
        "runwayml_params": {"transition": "cut", "duration_frames": 1},
    },
    "static": {
        "effect": "static",
        "duration": 0.0,
        "ffmpeg_filter": "null",
        "runwayml_params": {"transition": "static"},
    },
    # === 고급 시네마틱 필터 추가 (FFmpeg 2026 기준) ===
    "vintage_grade": {
        "effect": "cinematic_grading",
        "duration": 0.0,
        "ease": "none",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "curves=preset=vintage,colorbalance=rs=0.1:gs=-0.05:bs=0.05",
        "runwayml_params": {"filter": "vintage_grading", "intensity": 0.8},
    },
    "film_look": {
        "effect": "cinematic_filter",
        "duration": 0.0,
        "ease": "none",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "curves=vintage,vignette=angle=PI/5:mode=forward:radius=0.8",
        "runwayml_params": {"filter": "film_look", "vignette": True},
    },
    "lens_distortion": {
        "effect": "lens_correction",
        "duration": 0.0,
        "ease": "none",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "lenscorrection=cx=iw/2:cy=ih/2:k1=0.15:k2=-0.05",
        "runwayml_params": {"filter": "lens_distortion", "k1": 0.15, "k2": -0.05},
    },
    "cinematic_vignette": {
        "effect": "vignette_filter",
        "duration": 0.0,
        "ease": "none",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "vignette=x=iw/2:y=ih/2:angle=0:spread=1:radius=0.75:feather=20",
        "runwayml_params": {"filter": "vignette", "radius": 0.75, "feather": 20},
    },
    "color_boost": {
        "effect": "color_enhancement",
        "duration": 0.0,
        "ease": "none",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "eq=saturation=1.3:contrast=1.1:brightness=0.05",
        "runwayml_params": {
            "filter": "color_boost",
            "saturation": 1.3,
            "contrast": 1.1,
        },
    },
    "hollywood_transition": {
        "effect": "advanced_transition",
        "duration": 1.5,
        "ease": "in_out",
        "start_opacity": 1.0,
        "end_opacity": 1.0,
        "ffmpeg_filter": "xfade=transition=fadeblack:duration=1.5:offset={start_time}",
        "runwayml_params": {"transition": "fadeblack", "duration_frames": 45},
    },
}


def video_branch_processor(
    timeline_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    TimelineState의 video 지시어 → 실제 렌더링 파라미터 변환

    Args:
        timeline_sections: TimelineState의 sections 리스트

    Returns:
        각 구간별 실제 렌더링 파라미터가 포함된 리스트
    """
    rendered_sections = []

    for section in timeline_sections:
        video_directive = section.get("video", "static")  # 기본값 static

        # 효과 맵에서 파라미터 가져오기
        params = VIDEO_EFFECT_MAP.get(video_directive, VIDEO_EFFECT_MAP["static"])

        # 렌더링 준비된 섹션 생성
        rendered_section = {
            "time": section.get("time"),
            "intent": section.get("intent"),
            "video_params": params,
            "sync_status": "ready_for_join",
            "render_target": "ffmpeg",  # ffmpeg 또는 runwayml
        }

        rendered_sections.append(rendered_section)

    return rendered_sections


def generate_ffmpeg_command(video_plan: dict[str, Any]) -> str:
    """
    Video 계획을 FFmpeg 명령어로 변환

    Args:
        video_plan: video_branch_processor의 출력

    Returns:
        FFmpeg 명령어 문자열
    """
    sections = video_plan.get("sections", [])

    # 간단한 FFmpeg 명령어 생성 (실제로는 더 복잡한 로직 필요)
    filters = []
    for section in sections:
        if "ffmpeg_filter" in section.get("video_params", {}):
            filters.append(section["video_params"]["ffmpeg_filter"])

    if filters:
        filter_complex = ",".join(filters)
        return f"ffmpeg -i input.mp4 -filter_complex '{filter_complex}' output.mp4"
    else:
        return "ffmpeg -i input.mp4 output.mp4"


def prepare_runwayml_payload(video_plan: dict[str, Any]) -> dict[str, Any]:
    """
    Video 계획을 RunwayML API payload로 변환

    Args:
        video_plan: video_branch_processor의 출력

    Returns:
        RunwayML API용 payload 딕셔너리
    """
    sections = video_plan.get("sections", [])

    # RunwayML용 payload 생성
    payload = {
        "model": "gen-2",
        "prompt": "Generate video based on timeline",
        "duration": "15s",
        "effects": [],
    }

    for section in sections:
        if "runwayml_params" in section.get("video_params", {}):
            payload["effects"].append(
                {
                    "time_start": section.get("time", "0:00").split("-")[0],
                    **section["video_params"]["runwayml_params"],
                }
            )

    return payload


if __name__ == "__main__":
    # 테스트용 TimelineState sections (기본 + 고급 필터)
    test_sections = [
        {"time": "0:00-0:15", "intent": "intro", "video": "vintage_grade"},
        {"time": "0:15-0:30", "intent": "hook", "video": "cinematic_vignette"},
        {"time": "0:30-0:45", "intent": "content", "video": "film_look"},
        {"time": "0:45-1:00", "intent": "climax", "video": "color_boost"},
        {"time": "1:00-1:15", "intent": "outro", "video": "hollywood_transition"},
    ]

    # VideoBranch 처리
    video_plan = video_branch_processor(test_sections)

    print("VideoBranch 고급 시네마틱 필터 테스트 결과:")
    print(f"섹션 수: {len(video_plan)}")
    for section in video_plan:
        params = section["video_params"]
        print(
            f"  {section['time']}: {params['effect']} (ffmpeg: {params.get('ffmpeg_filter', 'N/A')[:50]}...)"
        )

    # FFmpeg 명령어 생성 테스트
    ffmpeg_cmd = generate_ffmpeg_command({"sections": video_plan})
    print(f"\nFFmpeg 명령어: {ffmpeg_cmd}")

    # RunwayML payload 생성 테스트
    runway_payload = prepare_runwayml_payload({"sections": video_plan})
    print(f"\nRunwayML payload 효과 수: {len(runway_payload.get('effects', []))}")
