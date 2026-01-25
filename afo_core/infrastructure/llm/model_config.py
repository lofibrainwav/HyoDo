# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Model Configuration - Task Types and Model Mappings

모델 설정 SSOT (Single Source of Truth)
- TaskType: 작업 유형 분류
- ModelConfig: 모델 설정
- TASK_PATTERNS: 작업 분류 패턴
"""

from __future__ import annotations

import re
from enum import Enum

__all__ = [
    "TaskType",
    "ModelConfig",
    "TASK_PATTERNS",
    "get_compiled_patterns",
]


class TaskType(str, Enum):
    """작업 유형 분류"""

    CHAT = "chat"  # 일반 대화
    VISION = "vision"  # 이미지 분석
    CODE_GENERATE = "code_generate"  # 코드 생성
    CODE_REVIEW = "code_review"  # 코드 분석/리뷰
    REASONING = "reasoning"  # 복잡한 추론
    EMBED = "embed"  # 임베딩 생성
    DOCUMENT = "document"  # 문서화


class ModelConfig:
    """모델 설정 (SSOT)"""

    # 집현전 학자 모델 맵핑 - MLX 우선 (M4 Pro 24GB 최적화)
    # Ollama 모델 (Vision 전용 - MLX 대안 없음)
    HEO_JUN = "qwen3-vl:latest"  # 허준 - 비전/일반대화 (정밀) [Ollama]
    HEO_JUN_FAST = "qwen3-vl:2b"  # 허준 - 비전/일반대화 (빠름) [Ollama]
    EMBEDDING = "embeddinggemma:latest"  # 임베딩 전용 [Ollama]

    # MLX 모델 (Apple Silicon 네이티브 - 2배 빠름)
    JEONG_YAK_YONG = "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit"  # 정약용 - 코딩 [MLX 32B]
    RYU_SEONG_RYONG = "mlx-community/DeepSeek-R1-Distill-Qwen-14B-4bit"  # 류성룡 - 추론 [MLX]

    # Ollama fallback (MLX 실패 시)
    JEONG_YAK_YONG_OLLAMA = "qwen2.5-coder:7b"  # 정약용 fallback
    RYU_SEONG_RYONG_OLLAMA = "deepseek-r1:14b"  # 류성룡 fallback

    # MLX 사용 여부 플래그
    USE_MLX = True  # Apple Silicon 최적화 활성화

    # Task → Model 매핑 (기본값 - 에스컬레이션 전)
    TASK_MODEL_MAP: dict[TaskType, str] = {
        TaskType.CHAT: HEO_JUN,
        TaskType.VISION: HEO_JUN_FAST,
        TaskType.CODE_GENERATE: JEONG_YAK_YONG,
        TaskType.CODE_REVIEW: RYU_SEONG_RYONG,
        TaskType.REASONING: RYU_SEONG_RYONG,
        TaskType.EMBED: EMBEDDING,
        TaskType.DOCUMENT: JEONG_YAK_YONG,
    }

    # Task → Scholar 매핑 (로깅용)
    TASK_SCHOLAR_MAP: dict[TaskType, str] = {
        TaskType.CHAT: "허준 (Heo Jun)",
        TaskType.VISION: "허준 (Heo Jun)",
        TaskType.CODE_GENERATE: "정약용 (Jeong Yak-yong)",
        TaskType.CODE_REVIEW: "류성룡 (Ryu Seong-ryong)",
        TaskType.REASONING: "류성룡 (Ryu Seong-ryong)",
        TaskType.EMBED: "임베딩 엔진",
        TaskType.DOCUMENT: "정약용 (Jeong Yak-yong)",
    }

    # 에스컬레이션 모델 맵핑 (신뢰도 낮을 때 사용)
    ESCALATION_MODEL_MAP: dict[TaskType, str] = {
        TaskType.CHAT: HEO_JUN,
        TaskType.VISION: HEO_JUN,
        TaskType.CODE_GENERATE: RYU_SEONG_RYONG,
        TaskType.CODE_REVIEW: RYU_SEONG_RYONG,
        TaskType.REASONING: RYU_SEONG_RYONG,
        TaskType.DOCUMENT: RYU_SEONG_RYONG,
    }

    # 에스컬레이션 임계값 (SSOT)
    ESCALATION_THRESHOLDS: dict[TaskType, float] = {
        TaskType.CHAT: 88.0,
        TaskType.VISION: 90.0,
        TaskType.CODE_GENERATE: 92.0,
        TaskType.CODE_REVIEW: 0.0,  # Bypass
        TaskType.REASONING: 0.0,  # Bypass
        TaskType.EMBED: 0.0,  # Bypass
        TaskType.DOCUMENT: 85.0,
    }


# 키워드 패턴 정의 (정규식) - 간소화 버전
TASK_PATTERNS: dict[TaskType, list[str]] = {
    TaskType.CHAT: [
        r"어떻게.*생각",
        r"조언",
        r"의견",
        r"추천",
        r"아이디어",
        r"UX",
        r"디자인",
        r"UI",
        r"사용자.*경험",
        r"도와줘",
        r"부탁",
    ],
    TaskType.VISION: [
        r"image",
        r"이미지",
        r"사진",
        r"그림",
        r"vision",
        r"screenshot",
        r"스크린샷",
        r"화면",
        r"보여",
    ],
    TaskType.CODE_GENERATE: [
        r"코드.*(?:작성|생성|만들|짜)",
        r"implement",
        r"구현",
        r"함수.*만들",
        r"클래스.*생성",
        r"컴포넌트",
        r"def\s+\w+",
        r"class\s+\w+",
        r"알고리즘",
        r"프로그래밍",
    ],
    TaskType.CODE_REVIEW: [
        r"코드.*(?:리뷰|분석|검토|확인)",
        r"review",
        r"refactor",
        r"리팩터",
        r"debug",
        r"디버그",
        r"버그.*찾",
    ],
    TaskType.REASONING: [
        r"단계.*분석",
        r"step.*by.*step",
        r"깊이.*생각",
        r"추론",
        r"reasoning",
        r"왜.*(?:그런|이런)",
        r"논리",
    ],
    TaskType.EMBED: [
        r"embed",
        r"임베딩",
        r"벡터",
        r"vector",
        r"similarity",
        r"유사도",
    ],
    TaskType.DOCUMENT: [
        r"문서화",
        r"document",
        r"docstring",
        r"주석",
        r"readme",
        r"설명.*작성",
    ],
}

# 컴파일된 패턴 캐시
_COMPILED_PATTERNS: dict[TaskType, list[re.Pattern[str]]] = {}


def get_compiled_patterns() -> dict[TaskType, list[re.Pattern[str]]]:
    """정규식 패턴 컴파일 (캐시)"""
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        for task_type, patterns in TASK_PATTERNS.items():
            _COMPILED_PATTERNS[task_type] = [re.compile(p, re.IGNORECASE) for p in patterns]
    return _COMPILED_PATTERNS
