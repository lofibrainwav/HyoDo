"""
Multimodal FANOUT-JOIN Extension - 병렬 브랜치 확장
TimelineState를 입력으로 VideoBranch + MusicBranch를 병렬로 생성하고 JOIN

ABSORB → GENERATE → FANOUT(VideoBranch + MusicBranch) → JOIN → RENDER
"""

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from AFO.multimodal.timeline_state_generator import timeline_generator_node


class MultimodalState(TypedDict):
    """확장된 멀티모달 상태 - 병렬 브랜치 지원"""

    raw_intent: str
    timeline: dict[str, Any]
    video_plan: dict[str, Any]  # VideoBranch 출력
    music_plan: dict[str, Any]  # MusicBranch 출력
    joined_plan: dict[str, Any]  # JOIN 결과


def video_branch_node(state: MultimodalState) -> dict[str, Any]:
    """
    VideoBranch: TimelineState를 비디오 계획으로 변환
    각 구간의 video 지시어를 실제 렌더링 파라미터로 확장
    """
    timeline = state.get("timeline", {})
    sections = timeline.get("sections", [])

    video_plan = {
        "total_duration": timeline.get("total_duration", "0:00"),
        "template_type": timeline.get("template_type", "standard"),
        "sections": [],
    }

    # Parameter Expansion Map
    expansion_map = {
        "fade_in": {"effect": "opacity_transition", "duration": 2.0, "ease": "in_out"},
        "fade_in_zoom": {"effect": "zoom_in_fade", "duration": 1.5, "scale": 1.1},
        "text_overlay": {
            "effect": "text_overlay",
            "position": "center",
            "animation": "slide_up",
        },
        "cut_sequence": {
            "effect": "cut_sequence",
            "interval": 0.5,
            "transition": "hard_cut",
        },
        "zoom_effect": {"effect": "zoom", "scale_factor": 1.2, "duration": 1.0},
        "fade_out": {"effect": "fade_out", "duration": 3.0},
    }

    for section in sections:
        instr = section.get("video", "default")
        video_params = expansion_map.get(instr, {"effect": "default", "instruction": instr})

        video_plan["sections"].append(
            {
                "time": section.get("time"),
                "intent": section.get("intent"),
                "video_params": video_params,
                "description": section.get("description"),
            }
        )

    return {"video_plan": video_plan}


def music_branch_node(state: MultimodalState) -> dict[str, Any]:
    """
    MusicBranch: TimelineState를 음악 계획으로 변환
    각 구간의 music 지시어를 실제 오디오 파라미터로 확장
    """
    timeline = state.get("timeline", {})
    sections = timeline.get("sections", [])

    music_plan = {
        "total_duration": timeline.get("total_duration", "0:00"),
        "bpm": 128 if timeline.get("template_type") == "short" else 95,
        "sections": [],
    }

    # Parameter Expansion Map
    expansion_map = {
        "slow_build": {
            "energy": "low",
            "instruments": ["ambient", "pads"],
            "reverb": "large",
        },
        "drop_beat": {"energy": "high", "kick_intensity": 0.9, "sidechain": True},
        "main_theme": {"energy": "medium", "lead": "synth_brass", "resonance": 0.5},
        "peak_energy": {"energy": "peak", "distortion": 0.2, "compression": "heavy"},
        "resolve": {"energy": "low", "release": 5.0, "fade": "linear"},
    }

    for section in sections:
        instr = section.get("music", "default")
        music_params = expansion_map.get(instr, {"energy": "medium", "instruction": instr})

        music_plan["sections"].append(
            {
                "time": section.get("time"),
                "intent": section.get("intent"),
                "music_params": music_params,
                "description": section.get("description"),
            }
        )

    return {"music_plan": music_plan}


def join_node(state: MultimodalState) -> dict[str, Any]:
    """
    JOIN: VideoBranch + MusicBranch를 하나의 통합 계획으로 합류
    시간 기반 동기화로 동일한 타임라인에 결혼식처럼 묶기
    """
    video_plan = state.get("video_plan", {})
    music_plan = state.get("music_plan", {})
    timeline = state.get("timeline", {})

    # JOIN 로직: 시간 기반으로 비디오 + 음악 포인트 통합
    joined_sections = []

    video_sections = video_plan.get("sections", [])
    music_sections = music_plan.get("sections", [])

    # 동일한 시간 구간을 기준으로 JOIN (zip으로 동기화)
    for video_sec, music_sec in zip(video_sections, music_sections):
        if video_sec.get("time") == music_sec.get("time"):  # 시간 매칭 검증
            joined_section = {
                "time": video_sec.get("time"),
                "intent": video_sec.get("intent"),
                "video": video_sec.get("video_params", {}),
                "music": music_sec.get("music_params", {}),
                "description": video_sec.get("description"),
                "sync_status": "perfect_sync",  # 동기화 상태 표시
            }
            joined_sections.append(joined_section)

    joined_plan = {
        "total_duration": timeline.get("total_duration", "0:00"),
        "sections": joined_sections,
        "sync_method": "time_based_join",
        "branches_merged": ["video", "music"],
    }

    return {"joined_plan": joined_plan}


def render_node(state: MultimodalState) -> dict[str, Any]:
    """
    RENDER: 통합된 멀티모달 계획을 출력
    세종/개발자/바이브 모드 지원
    """
    joined_plan = state.get("joined_plan", {})

    # 구조화된 출력
    output = {
        "status": "멀티모달 병렬 계획 생성 완료",
        "joined_plan": joined_plan,
        "sections_count": len(joined_plan.get("sections", [])),
        "total_duration": joined_plan.get("total_duration", "0:00"),
        "sync_status": joined_plan.get("sync_status", "unknown"),
    }

    return {"output": json.dumps(output, indent=2, ensure_ascii=False)}


# 확장된 워크플로우 빌드
def build_multimodal_workflow() -> StateGraph:
    """멀티모달 FANOUT-JOIN 워크플로우 빌드"""
    workflow = StateGraph(MultimodalState)

    # 기존 노드
    workflow.add_node(
        "absorb", lambda state: {"raw_intent": state.get("raw_intent", "흥겨운 콘텐츠")}
    )
    workflow.add_node("generate", timeline_generator_node)

    # FANOUT 노드 (병렬)
    workflow.add_node("video_branch", video_branch_node)
    workflow.add_node("music_branch", music_branch_node)

    # JOIN 노드
    workflow.add_node("join", join_node)
    workflow.add_node("render", render_node)

    # 플로우 설정
    workflow.set_entry_point("absorb")
    workflow.add_edge("absorb", "generate")

    # FANOUT: 단일 입력 → 병렬 브랜치
    workflow.add_edge("generate", "video_branch")
    workflow.add_edge("generate", "music_branch")

    # JOIN: 병렬 브랜치 → 단일 출력
    workflow.add_edge("video_branch", "join")
    workflow.add_edge("music_branch", "join")
    workflow.add_edge("join", "render")
    workflow.add_edge("render", END)

    return workflow


# 워크플로우 컴파일
multimodal_workflow = build_multimodal_workflow()
multimodal_app = multimodal_workflow.compile()


def generate_multimodal_plan(intent: str = "흥겨운 콘텐츠") -> dict[str, Any]:
    """
    멀티모달 병렬 계획 생성 편의 함수

    Args:
        intent: 멀티모달 콘텐츠 의도

    Returns:
        통합된 멀티모달 계획 딕셔너리
    """
    initial_state = MultimodalState(
        raw_intent=intent, timeline={}, video_plan={}, music_plan={}, joined_plan={}
    )

    result = multimodal_app.invoke(initial_state)

    # JSON 문자열을 딕셔너리로 변환하여 반환
    if isinstance(result.get("output"), str):
        return json.loads(result["output"])
    return result


if __name__ == "__main__":
    # 테스트 실행
    result = generate_multimodal_plan("신나는 댄스 음악 + 역동적인 비디오")
    print("멀티모달 병렬 계획 생성 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
