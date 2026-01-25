"""
DSPy Trinity Score 메트릭 구현 (TICKET-004 완성)
왕국 철학 眞善美孝永 기반 최적화 메트릭

형님 제시 코드 기반으로 구현 - 직접적이고 왕국 문화 반영
"""

import logging
import re
from difflib import SequenceMatcher

from AFO.domain.metrics.trinity import calculate_trinity

logger = logging.getLogger(__name__)

# DSPy 임포트 (설치되지 않은 경우 Mock 사용)
try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None  # type: ignore


class TrinityMetric:
    """
    DSPy Custom Metric: 眞善美孝永 기반 종합 평가
    - DSPy 표준 __call__ 준수
    - example(정답), pred(예측) 비교로 5기둥 점수 산출
    """

    def __init__(self) -> None:
        pass  # 가중치는 trinity.py에서 중앙 관리

    def __call__(self, example, pred, trace=None) -> None:
        gold = getattr(example, "gold", None)
        if gold is None and hasattr(example, "get"):
            gold = example.get("gold", "")
        gold = gold or ""

        output = getattr(pred, "output", None) or getattr(pred, "answer", None) or str(pred)

        pillar_scores = {
            "truth": self._evaluate_truth(gold, output),
            "goodness": self._evaluate_goodness(gold, output),
            "beauty": self._evaluate_beauty(gold, output),
            "filial_serenity": self._evaluate_serenity(gold, output),
            "eternity": self._evaluate_eternity(example, gold, output),
        }

        # calculate_trinity 결과 스케일이 0~1인지 0~100인지 모를 때 안전 가드
        result = calculate_trinity(**pillar_scores)
        score = getattr(result, "trinity_score", result)

        score = float(score)
        if score > 1.0:
            score = score / 100.0
        return max(0.0, min(1.0, score))

    def _evaluate_truth(self, gold: str, output: str) -> float:
        if not gold.strip():
            return 1.0
        sim = SequenceMatcher(None, gold.lower(), output.lower()).ratio()
        return max(0.0, min(1.0, sim))

    def _evaluate_goodness(self, gold: str, output: str) -> float:
        txt = output.lower()

        harmful_keywords = ["해킹", "불법", "폭력", "사기", "위협"]
        refusal_markers = [
            "하지 마",
            "하지마",
            "금지",
            "불가",
            "허용하지",
            "안 됩니다",
            "안됩니다",
            "거절",
            "도와드릴 수 없",
        ]

        has_harm = any(k in txt for k in harmful_keywords)
        has_refusal = any(m in txt for m in refusal_markers)

        if not has_harm:
            return 1.0
        if has_refusal:
            return 1.0  # 위험 키워드가 "거부/경고" 맥락이면 감점하지 않음

        # 실제로 위험한 방향(조언/방법 제공)일 때만 감점
        return 0.3

    def _evaluate_beauty(self, gold: str, output: str) -> float:
        # gold 길이 비교는 불안정하니 output 자체의 간결/구조로만 평가
        L = len(output.strip())
        if L == 0:
            return 0.0
        concise = 1.0 if L <= 800 else max(0.5, 800 / L)
        structured = 0.2 if re.search(r"(^|\n)([-*•]\s|\d+\.\s|#{1,3}\s)", output) else 0.0
        return min(1.0, concise + structured)

    def _evaluate_serenity(self, gold: str, output: str) -> float:
        # 역할극 보상 제거: 존댓말/명확한 액션 중심만 가점
        polite = 0.2 if re.search(r"(습니다|세요|드립니다)", output) else 0.0
        actionable = 0.2 if re.search(r"(다음|1\)|1\.|커맨드|명령|체크리스트)", output) else 0.0
        too_roleplay = 0.2 if re.search(r"(왕이시여|아뢰나이다|받들어)", output) else 0.0
        base = 0.6
        return max(0.0, min(1.0, base + polite + actionable - too_roleplay))

    def _evaluate_eternity(self, example, gold: str, output: str) -> float:
        # Evidence가 필요한 작업일 때만 가점 (다양한 필드명 지원)
        needs = (
            getattr(example, "needs_evidence", False)
            or getattr(example, "needsEvidence", False)
            or (hasattr(example, "get") and example.get("needs_evidence", False))
        )

        if not needs:
            return 0.8  # 평소엔 스팸 유도 방지용으로 높은 기본값

        # 증거 키워드 카운트 (형님 제시대로)
        txt = output.lower()
        hits = sum(
            1 for kw in ["artifacts/", "manifest", "sha256", "기록됨", "미관측"] if kw in txt
        )

        # 증거 태스크에서만 가점 적용
        return min(1.0, 0.6 + hits * 0.1)


# DSPy 메트릭 함수 (함수형 인터페이스)
trinity_metric = TrinityMetric()


def create_dspy_compatible_metric() -> None:
    """
    DSPy MIPROv2와 호환되는 메트릭 함수 생성
    TICKET-004 요구사항 준수
    """
    return trinity_metric


def get_trinity_score_breakdown(example: dict, pred: str) -> dict:
    """
    Trinity Score 세부 내역 반환
    디버깅 및 분석용
    """
    metric = TrinityMetric()
    gold = example.get("gold", example.get("answer", ""))

    return {
        "truth": metric._evaluate_truth(gold, pred),
        "goodness": metric._evaluate_goodness(gold, pred),
        "beauty": metric._evaluate_beauty(gold, pred),
        "serenity": metric._evaluate_serenity(gold, pred),
        "eternity": metric._evaluate_eternity(example, gold, pred),
        "total": metric(example, {"output": pred}),
    }


# MIPROv2 준비 함수 (DSPy 설치 시 사용)
def prepare_mipro_optimizer() -> None:
    """
    MIPROv2 옵티마이저 준비
    DSPy 설치 후 활성화
    """
    try:
        import dspy  # noqa: F401
        from dspy.teleprompt import MIPROv2

        optimizer = MIPROv2(
            metric=trinity_metric, num_candidates=10, init_temperature=1.0, verbose=True
        )

        logger.info("MIPROv2 옵티마이저 준비 완료 (Trinity Score 메트릭 적용)")
        return optimizer

    except ImportError:
        logger.warning("DSPy가 설치되지 않음 - MIPROv2 옵티마이저 준비 보류")
        return None


if __name__ == "__main__":
    # 테스트 실행
    metric = TrinityMetric()

    # 샘플 예시
    example = {"question": "왕국 철학 설명", "answer": "眞善美孝永"}
    pred = type("MockPred", (), {"answer": "眞善美孝永 철학"})()

    score = metric(example, pred)
    pred_text = pred.answer  # 텍스트 추출
    breakdown = get_trinity_score_breakdown(example, pred_text)

    print(f"Trinity Score: {score}")
    print(f"세부 내역: {breakdown}")
