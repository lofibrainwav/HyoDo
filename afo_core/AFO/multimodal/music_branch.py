"""
MusicBranch 세부 구현 - TimelineState의 music 지시어 → 실제 오디오 생성 파라미터 변환
멀티모달 병렬 처리의 음악 브랜치 (Suno/MusicGen API 연결 준비)
"""

from typing import Any

# Music 효과 맵 - 추상적 지시어를 실제 오디오 생성 파라미터로 변환
MUSIC_EFFECT_MAP = {
    "slow_build": {
        "energy": "low",
        "tempo": "slow",
        "instruments": ["pads", "ambient", "soft_piano"],
        "build_up": True,
        "bpm_range": "80-100",
        "key": "C Major",
        "suno_prompt": "slow atmospheric pads with soft piano, ambient texture, emotional build",
        "musicgen_params": {
            "model": "melody",
            "duration": 15,
            "temperature": 0.8,
            "top_k": 50,
            "top_p": 0.9,
        },
    },
    "drop_beat": {
        "energy": "high",
        "tempo": "fast",
        "instruments": ["kick", "snare", "808_bass", "synth_lead"],
        "drop_intensity": "heavy",
        "bpm_range": "140-160",
        "key": "C Minor",
        "suno_prompt": "heavy drop beat with 808 bass, kick and snare, synth lead, high energy",
        "musicgen_params": {
            "model": "large",
            "duration": 15,
            "temperature": 1.0,
            "top_k": 100,
            "top_p": 0.95,
        },
    },
    "main_theme": {
        "energy": "medium",
        "tempo": "moderate",
        "instruments": ["guitar", "strings", "drums", "melody"],
        "melody_focus": True,
        "bpm_range": "100-120",
        "key": "G Major",
        "suno_prompt": "melodic guitar with string section, steady drums, emotional theme",
        "musicgen_params": {
            "model": "melody",
            "duration": 15,
            "temperature": 0.9,
            "top_k": 75,
            "top_p": 0.92,
        },
    },
    "peak_energy": {
        "energy": "peak",
        "tempo": "fast",
        "instruments": ["full_orchestra", "fx_risers", "heavy_bass"],
        "climax": True,
        "bpm_range": "160-180",
        "key": "C# Minor",
        "suno_prompt": "epic orchestral climax with risers, heavy bass, full energy peak",
        "musicgen_params": {
            "model": "large",
            "duration": 15,
            "temperature": 1.2,
            "top_k": 150,
            "top_p": 0.98,
        },
    },
    "resolve": {
        "energy": "low",
        "tempo": "slow",
        "instruments": ["piano", "reverb_pads"],
        "fade_out": True,
        "bpm_range": "60-80",
        "key": "F Major",
        "suno_prompt": "gentle piano with reverb pads, emotional resolution, soft fade out",
        "musicgen_params": {
            "model": "melody",
            "duration": 15,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.85,
        },
    },
    "ambient": {
        "energy": "low",
        "tempo": "slow",
        "instruments": ["pads", "ambient"],
        "bpm_range": "70-90",
        "key": "A Minor",
        "suno_prompt": "ambient pads, atmospheric texture, peaceful",
        "musicgen_params": {
            "model": "melody",
            "duration": 15,
            "temperature": 0.8,
            "top_k": 50,
            "top_p": 0.9,
        },
    },
}


def music_branch_processor(
    timeline_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    TimelineState의 music 지시어 → 실제 오디오 생성 파라미터 변환

    Args:
        timeline_sections: TimelineState의 sections 리스트

    Returns:
        각 구간별 실제 오디오 생성 파라미터가 포함된 리스트
    """
    rendered_sections = []

    for section in timeline_sections:
        music_directive = section.get("music", "ambient")  # 기본값 ambient

        # 효과 맵에서 파라미터 가져오기
        params = MUSIC_EFFECT_MAP.get(music_directive, MUSIC_EFFECT_MAP["ambient"])

        # 오디오 생성 준비된 섹션 생성
        rendered_section = {
            "time": section.get("time"),
            "intent": section.get("intent"),
            "music_params": params,
            "sync_status": "ready_for_join",
            "render_target": "suno",  # suno 또는 musicgen
        }

        rendered_sections.append(rendered_section)

    return rendered_sections


def generate_suno_prompt(music_plan: list[dict[str, Any]]) -> str:
    """
    Music 계획을 Suno API용 프롬프트로 변환

    Args:
        music_plan: music_branch_processor의 출력 (섹션 리스트)

    Returns:
        Suno API용 프롬프트 문자열
    """
    # 전체 음악 프롬프트 구성
    prompts = []
    for section in music_plan:
        if "suno_prompt" in section.get("music_params", {}):
            time_range = section.get("time", "")
            intent = section.get("intent", "")
            prompt = section["music_params"]["suno_prompt"]
            prompts.append(f"[{time_range}] {intent}: {prompt}")

    return " | ".join(prompts) if prompts else "ambient music"


def prepare_musicgen_payload(music_plan: dict[str, Any]) -> dict[str, Any]:
    """
    Music 계획을 MusicGen API payload로 변환

    Args:
        music_plan: music_branch_processor의 출력

    Returns:
        MusicGen API용 payload 딕셔너리
    """
    sections = music_plan.get("sections", [])

    # MusicGen용 payload 생성
    # MusicGen은 일반적으로 전체 곡을 한 번에 생성하므로 섹션별 파라미터를 통합
    combined_params = {
        "model": "large",  # 기본값
        "duration": 15,
        "temperature": 1.0,
        "top_k": 100,
        "top_p": 0.95,
    }

    # 섹션별 파라미터를 고려하여 최적값 계산
    for section in sections:
        section_params = section.get("music_params", {})
        if section_params.get("energy") == "peak":
            combined_params["temperature"] = max(combined_params["temperature"], 1.2)
            combined_params["top_k"] = max(combined_params["top_k"], 150)
        elif section_params.get("energy") == "low":
            combined_params["temperature"] = min(combined_params["temperature"], 0.8)
            combined_params["top_k"] = min(combined_params["top_k"], 50)

    # 프롬프트 생성
    combined_params["text"] = generate_suno_prompt(sections)

    return combined_params


def calculate_timeline_bpm(music_plan: list[dict[str, Any]]) -> int:
    """
    전체 음악 계획의 평균 BPM 계산

    Args:
        music_plan: music_branch_processor의 출력 (섹션 리스트)

    Returns:
        평균 BPM 값
    """
    total_bpm = 0
    count = 0

    for section in music_plan:
        bpm_range = section.get("music_params", {}).get("bpm_range", "120-140")
        # BPM 범위의 평균 계산
        try:
            min_bpm, max_bpm = map(int, bpm_range.split("-"))
            avg_bpm = (min_bpm + max_bpm) // 2
            total_bpm += avg_bpm
            count += 1
        except ValueError:
            continue

    return total_bpm // count if count > 0 else 120


if __name__ == "__main__":
    # 테스트용 TimelineState sections
    test_sections = [
        {"time": "0:00-0:15", "intent": "intro", "music": "slow_build"},
        {"time": "0:15-0:30", "intent": "hook", "music": "drop_beat"},
        {"time": "0:30-0:45", "intent": "content", "music": "main_theme"},
        {"time": "0:45-1:00", "intent": "climax", "music": "peak_energy"},
        {"time": "1:00-1:15", "intent": "outro", "music": "resolve"},
    ]

    # MusicBranch 처리
    music_plan = music_branch_processor(test_sections)

    print("MusicBranch 세부 구현 테스트 결과:")
    print(f"섹션 수: {len(music_plan)}")
    print(f"평균 BPM: {calculate_timeline_bpm(music_plan)}")
    print(f"Suno 프롬프트: {generate_suno_prompt(music_plan)}")

    for section in music_plan:
        params = section.get("music_params", {})
        print(f"  {section['time']}: {params.get('energy')} energy, {params.get('tempo')} tempo")
