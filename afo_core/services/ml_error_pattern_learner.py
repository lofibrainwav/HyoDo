from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
"""
Machine Learning Error Pattern Learner
머신러닝 기반 에러 패턴 학습 시스템

眞善美孝永 철학에 기반한 ML 진단 강화
眞 (Truth): 정확한 패턴 인식 및 분류
善 (Goodness): 안전한 학습 및 예측
美 (Beauty): 우아한 패턴 매칭 알고리즘
孝 (Serenity): 개발자 경험 최적화
永 (Eternity): 지속적인 학습 및 개선
"""


logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """에러 패턴 데이터 클래스"""

    error_type: str
    category: str
    error_message_pattern: str
    file_path_pattern: str | None = None
    common_fixes: list[dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    occurrence_count: int = 0
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())


class MLErrorPatternLearner:
    """
    머신러닝 기반 에러 패턴 학습 시스템
    Sequential Thinking: 패턴 학습 및 예측적 진단
    """

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = Path(project_root)
        self.patterns: dict[str, ErrorPattern] = {}
        self.pattern_file = self.project_root / "logs" / "error_patterns.json"
        self.pattern_file.parent.mkdir(parents=True, exist_ok=True)

        # 학습 데이터 로드
        self._load_patterns()

    def _load_patterns(self) -> None:
        """저장된 패턴 로드"""
        try:
            if self.pattern_file.exists():
                with open(self.pattern_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for key, pattern_data in data.items():
                        self.patterns[key] = ErrorPattern(**pattern_data)
                logger.info(f"✅ {len(self.patterns)}개 에러 패턴 로드 완료")
        except Exception as e:
            logger.warning(f"패턴 로드 실패: {e}")

    def _save_patterns(self) -> None:
        """패턴 저장"""
        try:
            data = {
                key: {
                    "error_type": pattern.error_type,
                    "category": pattern.category,
                    "error_message_pattern": pattern.error_message_pattern,
                    "file_path_pattern": pattern.file_path_pattern,
                    "common_fixes": pattern.common_fixes,
                    "success_rate": pattern.success_rate,
                    "occurrence_count": pattern.occurrence_count,
                    "last_seen": pattern.last_seen,
                }
                for key, pattern in self.patterns.items()
            }
            with open(self.pattern_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"✅ {len(self.patterns)}개 패턴 저장 완료")
        except Exception as e:
            logger.error(f"패턴 저장 실패: {e}")

    def learn_from_error(
        self,
        error_type: str,
        category: str,
        error_message: str,
        file_path: str | None = None,
        fix_applied: dict[str, Any] | None = None,
        success: bool = False,
    ) -> None:
        """
        에러로부터 학습 (眞 - Truth)

        Args:
            error_type: 에러 타입
            category: 에러 카테고리
            error_message: 에러 메시지
            file_path: 파일 경로
            fix_applied: 적용된 수정 사항
            success: 수정 성공 여부
        """
        # 패턴 키 생성 (에러 타입 + 카테고리)
        pattern_key = f"{error_type}:{category}"

        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = ErrorPattern(
                error_type=error_type,
                category=category,
                error_message_pattern=error_message[:100],  # 처음 100자만
                file_path_pattern=file_path,
            )

        pattern = self.patterns[pattern_key]

        # 발생 횟수 증가
        pattern.occurrence_count += 1
        pattern.last_seen = datetime.now().isoformat()

        # 수정 사항 기록
        if fix_applied and success:
            # 기존 수정 사항과 비교하여 성공률 계산
            existing_fix = next(
                (f for f in pattern.common_fixes if f.get("type") == fix_applied.get("type")),
                None,
            )

            if existing_fix:
                existing_fix["success_count"] = existing_fix.get("success_count", 0) + 1
                existing_fix["total_count"] = existing_fix.get("total_count", 0) + 1
                existing_fix["success_rate"] = (
                    existing_fix["success_count"] / existing_fix["total_count"]
                )
            else:
                pattern.common_fixes.append(
                    {
                        **fix_applied,
                        "success_count": 1,
                        "total_count": 1,
                        "success_rate": 1.0,
                    }
                )

            # 전체 성공률 업데이트
            total_successes = sum(f.get("success_count", 0) for f in pattern.common_fixes)
            total_attempts = sum(f.get("total_count", 0) for f in pattern.common_fixes)
            if total_attempts > 0:
                pattern.success_rate = total_successes / total_attempts
        elif fix_applied:
            # 실패한 수정도 기록
            existing_fix = next(
                (f for f in pattern.common_fixes if f.get("type") == fix_applied.get("type")),
                None,
            )

            if existing_fix:
                existing_fix["total_count"] = existing_fix.get("total_count", 0) + 1
                existing_fix["success_rate"] = (
                    existing_fix.get("success_count", 0) / existing_fix["total_count"]
                )

        # 패턴 저장
        self._save_patterns()

    def predict_fix(
        self, error_type: str, category: str, error_message: str
    ) -> list[dict[str, Any]]:
        """
        에러에 대한 수정 예측 (眞 - Truth)

        Args:
            error_type: 에러 타입
            category: 에러 카테고리
            error_message: 에러 메시지

        Returns:
            예측된 수정 사항 목록 (성공률 순으로 정렬)
        """
        pattern_key = f"{error_type}:{category}"

        if pattern_key not in self.patterns:
            return []

        pattern = self.patterns[pattern_key]

        # 성공률이 높은 순으로 정렬
        sorted_fixes = sorted(
            pattern.common_fixes,
            key=lambda x: x.get("success_rate", 0.0),
            reverse=True,
        )

        return [
            {
                "type": fix.get("type"),
                "description": fix.get("description"),
                "command": fix.get("command"),
                "confidence": fix.get("success_rate", 0.0),
                "source": "ml_pattern_learner",
            }
            for fix in sorted_fixes[:5]  # 상위 5개만 반환
        ]

    def get_pattern_statistics(self) -> dict[str, Any]:
        """
        패턴 통계 조회 (永 - Eternity)

        Returns:
            패턴 통계 정보
        """
        total_patterns = len(self.patterns)
        total_occurrences = sum(p.occurrence_count for p in self.patterns.values())
        avg_success_rate = (
            sum(p.success_rate for p in self.patterns.values()) / total_patterns
            if total_patterns > 0
            else 0.0
        )

        category_distribution: dict[str, int] = defaultdict(int)
        for pattern in self.patterns.values():
            category_distribution[pattern.category] += pattern.occurrence_count

        return {
            "total_patterns": total_patterns,
            "total_occurrences": total_occurrences,
            "average_success_rate": avg_success_rate,
            "category_distribution": dict(category_distribution),
        }
