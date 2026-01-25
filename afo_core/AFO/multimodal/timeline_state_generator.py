"""
TimelineState Generator Node - LangGraph Implementation
멀티모달 병렬 처리의 핵심: TimelineState 자동 생성

ABSORB → TIMELINE_GENERATE → RENDER 플로우 구현
"""

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class TimelineState(TypedDict):
    """멀티모달 TimelineState - 음악/비디오 동기화의 SSOT"""

    sections: list[dict[str, Any]]
    raw_intent: str
    timeline: dict[str, Any]


def absorb_node(state: TimelineState) -> dict[str, Any]:
    """
    ABSORB_STATE: 의도와 미디어 데이터 흡수
    기존 multimodal_rag_engine 활용
    """
    # 현재 상태에서 의도 추출 (실제로는 multimodal_rag_engine에서 가져옴)
    raw_intent = state.get("raw_intent", "흥겨운 인트로 + 클라이맥스 드롭")

    return {"raw_intent": raw_intent, "sections": [], "timeline": {}}


def timeline_generator_node(state: TimelineState) -> dict[str, Any]:
    """
    TIMELINE_GENERATOR: Intent 기반 동적 TimelineState 생성
    형님 정의 SSOT 기반 구조화 (3구간/5구간 가변 대응)
    """
    raw_intent = state.get("raw_intent", "").lower()

    # 동적 템플릿 선택 (Simple Intent Analyzer)
    is_short = any(k in raw_intent for k in ["짧은", "틱톡", "쇼츠", "short", "tiktok", "shorts"])

    if is_short:
        timeline_sections = [
            {
                "time": "0:00-0:10",
                "intent": "hook",
                "video": "fade_in_zoom",
                "music": "drop_beat",
                "description": "빠른 시선 강탈",
            },
            {
                "time": "0:10-0:25",
                "intent": "main",
                "video": "cut_sequence",
                "music": "main_theme",
                "description": "핵심 메시지 전달",
            },
            {
                "time": "0:25-0:30",
                "intent": "outro",
                "video": "fade_out",
                "music": "resolve",
                "description": "짧고 강한 여운",
            },
        ]
        total_duration = "0:30"
    else:
        # Default 5-section (Standard)
        timeline_sections = [
            {
                "time": "0:00-0:15",
                "intent": "intro",
                "video": "fade_in",
                "music": "slow_build",
                "description": "분위기 조성",
            },
            {
                "time": "0:15-0:30",
                "intent": "hook",
                "video": "text_overlay",
                "music": "drop_beat",
                "description": "관심 유도",
            },
            {
                "time": "0:30-0:45",
                "intent": "content",
                "video": "cut_sequence",
                "music": "main_theme",
                "description": "본론 전개",
            },
            {
                "time": "0:45-1:00",
                "intent": "climax",
                "video": "zoom_effect",
                "music": "peak_energy",
                "description": "감정 고조",
            },
            {
                "time": "1:00-1:15",
                "intent": "outro",
                "video": "fade_out",
                "music": "resolve",
                "description": "마무리",
            },
        ]
        total_duration = "1:15"

    return {
        "timeline": {
            "sections": timeline_sections,
            "total_duration": total_duration,
            "generated_from": raw_intent,
            "template_type": "short" if is_short else "standard",
        },
        "sections": timeline_sections,
    }


def render_node(state: TimelineState) -> dict[str, Any]:
    """
    RENDER: TimelineState를 원하는 포맷으로 출력
    세종/개발자/바이브 모드 지원
    """
    timeline = state.get("timeline", {})

    # JSON 포맷으로 구조화된 출력
    output = {
        "status": "TimelineState 생성 완료",
        "timeline": timeline,
        "sections_count": len(timeline.get("sections", [])),
        "total_duration": timeline.get("total_duration", "0:00"),
        "generated_from": timeline.get("generated_from", ""),
    }

    return {"output": json.dumps(output, indent=2, ensure_ascii=False)}


# LangGraph 워크플로우 빌드
def build_timeline_workflow() -> StateGraph:
    """TimelineState 생성 워크플로우 빌드"""
    workflow = StateGraph(TimelineState)

    # 노드 추가
    workflow.add_node("absorb", absorb_node)
    workflow.add_node("generate", timeline_generator_node)
    workflow.add_node("render", render_node)

    # 플로우 설정
    workflow.set_entry_point("absorb")
    workflow.add_edge("absorb", "generate")
    workflow.add_edge("generate", "render")
    workflow.add_edge("render", END)

    return workflow


# 워크플로우 컴파일
timeline_workflow = build_timeline_workflow()
timeline_app = timeline_workflow.compile()


def generate_timeline_state(
    intent: str = "흥겨운 인트로 + 클라이맥스 드롭",
) -> dict[str, Any]:
    """
    TimelineState 생성 편의 함수

    Args:
        intent: 멀티모달 콘텐츠 의도

    Returns:
        생성된 TimelineState 딕셔너리
    """
    initial_state = TimelineState(sections=[], raw_intent=intent, timeline={})

    result = timeline_app.invoke(initial_state)

    # JSON 문자열을 딕셔너리로 변환하여 반환
    if isinstance(result.get("output"), str):
        return json.loads(result["output"])
    return result


if __name__ == "__main__":
    # 테스트 실행
    result = generate_timeline_state("신나는 댄스 음악 + 역동적인 비디오")
    print("TimelineState 생성 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
