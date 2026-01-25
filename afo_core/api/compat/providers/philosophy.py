"""Philosophy Data Provider

철학 데이터 제공자 (眞善美孝永 5기둥).
"""

from typing import Any


class PhilosophyDataProvider:
    """
    철학 데이터 제공자 (眞善美孝永 5기둥)

    Trinity Score: 眞 (Truth) - 정확한 철학 데이터 제공
    아름다운 코드: 단일 책임 + 불변 데이터 + 타입 안전성
    """

    @staticmethod
    def get_philosophy_data() -> dict[str, Any]:
        """5기둥 철학 데이터 반환"""
        return {
            "pillars": [
                {
                    "id": "truth",
                    "name": "眞",
                    "weight": 35,
                    "role": "제갈량 - 기술적 확실성",
                    "color": "#3b82f6",
                },
                {
                    "id": "goodness",
                    "name": "善",
                    "weight": 35,
                    "role": "사마의 - 윤리·안정성",
                    "color": "#10b981",
                },
                {
                    "id": "beauty",
                    "name": "美",
                    "weight": 20,
                    "role": "주유 - 단순함·우아함",
                    "color": "#8b5cf6",
                },
                {
                    "id": "serenity",
                    "name": "孝",
                    "weight": 8,
                    "role": "승상 - 평온 수호",
                    "color": "#f59e0b",
                },
                {
                    "id": "eternity",
                    "name": "永",
                    "weight": 2,
                    "role": "승상 - 영속성",
                    "color": "#ef4444",
                },
            ],
            "total_weight": 100,
            "description": "AFO Kingdom 철학 시스템",
        }
