from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any

from guardrails import CustomGuard, GuardrailsOpenAI, StreamingGuardrailsOpenAI

from AFO.api.compat import ChancellorInvokeRequest, ChancellorInvokeResponse

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
"""
Advanced Guardrails SDK usage scenarios with graceful fallbacks.

형님이 바로 붙여넣어 실행할 수 있도록, 각 예제는 실제 Guardrails SDK가
설치되어 있을 때는 진짜 호출을 시도하고, 그렇지 않으면 친절한 안내만
출력하도록 구성했습니다. `ENABLE_GUARDRAILS=true` 와
`OPENAI_API_KEY=...` 를 `.env` 에 넣어 두면 동일한 설정을 재사용할 수
있습니다.

실행 방법:
    poetry shell / venv 활성화 후
    python -m afo_soul_engine.examples.guardrails_advanced_examples
"""


try:
    pass  # Placeholder
except ModuleNotFoundError:  # pragma: no cover - 환경에 따라 설치 미완료 가능
    GuardrailsOpenAI = None
    CustomGuard = None

# 스트리밍 전용 클래스는 프리뷰 단계에서 이름이 바뀔 수 있어 optional import 처리
try:  # pragma: no cover - SDK 버전에 따라 달라짐
    pass
except ModuleNotFoundError:
    StreamingGuardrailsOpenAI = None


# Strangler Fig Phase 1: 타입 모델 추가 (眞: Truth 타입 안전성)
try:
    pass  # Placeholder
except ImportError:
    # Fallback for backward compatibility
    ChancellorInvokeRequest = Any  # type: ignore[assignment]
    ChancellorInvokeResponse = Any  # type: ignore[assignment]


def _require_guardrails() -> bool:
    if GuardrailsOpenAI is None:
        print(
            "⚠️ Guardrails SDK가 설치되어 있지 않습니다. `pip install openai-guardrails` 후 다시 실행하세요."
        )
        return False
    return True


def _build_base_config() -> dict[str, Any]:
    """기본 파이프라인 설정. 필요하면 JSON 파일을 따로 전달해도 됩니다."""

    return {
        "input": [
            {
                "name": "Moderation",
                "config": {"categories": ["harassment", "hate", "self-harm"]},
            }
        ],
        "output": [{"name": "PII", "config": {"action": "block"}}],
    }


def example_parallel_input_output() -> None:
    """입력과 출력 가드를 동시에 적용하는 예제."""

    if not _require_guardrails():
        return

    config = _build_base_config()
    client = GuardrailsOpenAI(
        config=config,
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GUARDRAILS_MODEL", "gpt-4o-mini"),
    )

    print("[예제1] 입력/출력 병렬 가드 시험")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "내 주민번호는 123-45-6789 이야."}]
    )
    print("  → 응답:", response.choices[0].message.content)


def example_multi_agent_handoff() -> None:
    """에이전트 간 핸드오프를 시뮬레이션 (간단 버전)."""

    if not _require_guardrails():
        return

    print("[예제2] 멀티 에이전트 핸드오프")
    reviewer = GuardrailsOpenAI(
        config={"input": [{"name": "Moderation"}]},
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GUARDRAILS_MODEL", "gpt-4o-mini"),
    )
    fixer = GuardrailsOpenAI(
        config={"output": [{"name": "PII"}]},
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GUARDRAILS_MODEL", "gpt-4o-mini"),
    )

    first = reviewer.chat.completions.create(
        messages=[{"role": "user", "content": "악의적인 표현이 섞인 코드를 검토해줘"}]
    )
    intermediary = first.choices[0].message.content
    print("  → 1차 검토 결과:", intermediary)

    second = fixer.chat.completions.create(
        messages=[
            {"role": "system", "content": "불필요한 민감 정보는 모두 제거하라"},
            {"role": "user", "content": intermediary},
        ]
    )
    print("  → 2차 정리 결과:", second.choices[0].message.content)


def example_streaming_guard() -> None:
    """스트리밍 모드에서 토큰을 실시간 검증하는 예제."""

    if StreamingGuardrailsOpenAI is None:
        print(
            "⚠️ StreamingGuardrailsOpenAI 클래스를 찾을 수 없습니다. SDK 프리뷰 버전을 확인하세요."
        )
        return

    client = StreamingGuardrailsOpenAI(
        config={"output": [{"name": "StreamingModeration", "config": {"threshold": "low"}}]},
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GUARDRAILS_MODEL", "gpt-4o-mini"),
    )

    print("[예제3] 스트리밍 가드")
    stream = client.chat.completions.create(
        messages=[{"role": "user", "content": "폭력적인 이야기를 길게 써줘"}],
        stream=True,
    )

    for chunk in stream:
        if "tripwire" in chunk:
            print("\n  → ⚠️ 위험 감지:", chunk["tripwire"]["message"])
            break
        delta = chunk.choices[0].delta.content
        if delta:
            sys.stdout.write(delta)
            sys.stdout.flush()
    print()


def example_custom_guard() -> None:
    """사용자 정의 규칙을 적용하는 예제."""

    if not _require_guardrails():
        return
    if CustomGuard is None:
        print("⚠️ CustomGuard 클래스를 불러올 수 없습니다. SDK 버전을 업데이트하세요.")
        return

    class BrandGuard(CustomGuard):
        def validate(self, text: str) -> bool:
            return "brand_name" not in text.lower()

    config = {"output": [{"name": "Custom", "guard": BrandGuard()}]}
    client = GuardrailsOpenAI(
        config=config,
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("GUARDRAILS_MODEL", "gpt-4o-mini"),
    )

    print("[예제4] 커스텀 가드")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "brand_name 제품 후기를 써줘"}]
    )
    print("  → 결과:", response.choices[0].message.content)


EXAMPLES: dict[str, Callable[[], None]] = {
    "parallel": example_parallel_input_output,
    "handoff": example_multi_agent_handoff,
    "streaming": example_streaming_guard,
    "custom": example_custom_guard,
}


# Strangler Fig Phase 2: 함수 분해 (美: 우아한 구조)
def _validate_example_target(
    target: str,
) -> tuple[bool, str | None, Callable[[], None] | None]:
    """
    예제 타겟 검증 (순수 함수)

    Args:
        target: 실행할 예제 이름

    Returns:
        (유효성, 에러 메시지, 실행 함수)
    """
    if target == "all":
        return True, None, None

    runner = EXAMPLES.get(target)
    if runner is None:
        available = ", ".join(EXAMPLES.keys())
        error_msg = f"알 수 없는 예제입니다: {target}. 사용 가능: {available}"
        return False, error_msg, None

    return True, None, runner


def _execute_single_example(key: str, runner: Callable[[], None]) -> None:
    """
    단일 예제 실행 (순수 함수)

    Args:
        key: 예제 키
        runner: 실행 함수
    """
    print("=" * 60)
    print(f"실행: {key}")
    try:
        runner()
    except Exception as exc:
        print(f"  → 예제 실행 중 오류 발생: {exc}")


def _execute_all_examples() -> None:
    """
    모든 예제 실행 (순수 함수)
    """
    for key, runner in EXAMPLES.items():
        _execute_single_example(key, runner)


def _handle_execution_error(error_msg: str) -> None:
    """
    실행 에러 처리 (순수 함수)

    Args:
        error_msg: 에러 메시지
    """
    print(error_msg)
    sys.exit(1)


def run_all_examples() -> None:
    """
    모든 예제 실행 (Strangler Fig Facade - 외부 인터페이스 유지)
    """
    _execute_all_examples()


if __name__ == "__main__":
    # Strangler Fig Phase 2: 메인 로직 분해 적용
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    # 타겟 검증
    is_valid, error_msg, runner = _validate_example_target(target)

    if not is_valid:
        _handle_execution_error(error_msg)  # type: ignore

    # 실행
    if target == "all":
        _execute_all_examples()
    else:
        _execute_single_example(target, runner)  # type: ignore
