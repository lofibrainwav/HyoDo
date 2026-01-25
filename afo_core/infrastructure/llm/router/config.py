from __future__ import annotations

import logging
import os
from typing import Any

import yaml

from AFO.config.settings import settings

logger = logging.getLogger(__name__)


class ScholarConfigLoader:
    """Scholar Configuration Loader for SSOT Compliance"""

    @staticmethod
    def load_ssot_scholars() -> dict[str, dict[str, Any]]:
        """TRINITY_OS_PERSONAS.yaml에서 학자 설정 로드 (眞 - Truth)"""
        try:
            ssot_paths = [
                os.path.join(settings.BASE_DIR, "packages/trinity-os/TRINITY_OS_PERSONAS.yaml"),
                "packages/trinity-os/TRINITY_OS_PERSONAS.yaml",
                "../trinity-os/TRINITY_OS_PERSONAS.yaml",
            ]

            ssot_content = None
            for path in ssot_paths:
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        ssot_content = yaml.safe_load(f)
                    break

            if not ssot_content:
                logger.warning("TRINITY_OS_PERSONAS.yaml not found, using fallback config")
                return ScholarConfigLoader.get_fallback_scholars_config()

            scholars = ssot_content.get("personas", {}).get("jiphyeonjeon_scholars", {})
            if not scholars:
                logger.warning("No scholars found in SSOT, using fallback config")
                return ScholarConfigLoader.get_fallback_scholars_config()

            # SSOT 형식 변환
            ssot_scholars = {}
            for scholar_key, config in scholars.items():
                ssot_scholars[config["api_wallet_key"]] = {
                    "codename": config["codename"],
                    "chinese": config.get("chinese", config["codename"]),
                    "role": config["role"],
                    "philosophy_scores": config.get(
                        "philosophy_scores",
                        {"truth": 0.9, "goodness": 0.9, "beauty": 0.9, "serenity": 0.9},
                    ),
                    "provider": config.get("provider"),
                }

            # Pillar 학자 추가 (Ollama 기반 - 항상 포함)
            pillar_scholars = ScholarConfigLoader.get_pillar_scholars_config()
            for key, config in pillar_scholars.items():
                if key not in ssot_scholars:
                    ssot_scholars[key] = config

            logger.info(f"✅ SSOT Scholars loaded: {list(ssot_scholars.keys())}")
            return ssot_scholars

        except Exception as e:
            logger.error(f"Failed to load SSOT scholars: {e}")
            return ScholarConfigLoader.get_fallback_scholars_config()

    @staticmethod
    def get_pillar_scholars_config() -> dict[str, dict[str, Any]]:
        """Pillar 학자 설정 (Ollama 기반 眞善美孝永 평가자)"""
        return {
            "truth_scholar": {
                "codename": "자룡",
                "chinese": "Zilong",
                "role": "眞 (Truth) - 기술적 확실성, 타입 안전성 평가",
                "provider": "ollama",
                "philosophy_scores": {
                    "truth": 0.98,
                    "goodness": 0.90,
                    "beauty": 0.85,
                    "serenity": 0.88,
                },
            },
            "goodness_scholar": {
                "codename": "방통",
                "chinese": "Pangtong",
                "role": "善 (Goodness) - 윤리적 안정성, 보안 평가",
                "provider": "ollama",
                "philosophy_scores": {
                    "truth": 0.90,
                    "goodness": 0.98,
                    "beauty": 0.88,
                    "serenity": 0.92,
                },
            },
            "beauty_scholar": {
                "codename": "육손",
                "chinese": "Lushun",
                "role": "美 (Beauty) - UX, 서사적 일관성 평가",
                "provider": "ollama",
                "philosophy_scores": {
                    "truth": 0.85,
                    "goodness": 0.88,
                    "beauty": 0.98,
                    "serenity": 0.90,
                },
            },
            "serenity_scholar": {
                "codename": "영덕",
                "chinese": "Yeongdeok",
                "role": "孝 (Serenity) - 평온, 마찰 제거 평가",
                "provider": "ollama",
                "philosophy_scores": {
                    "truth": 0.88,
                    "goodness": 0.92,
                    "beauty": 0.90,
                    "serenity": 0.99,
                },
            },
            "eternity_scholar": {
                "codename": "영덕",
                "chinese": "Yeongdeok",
                "role": "永 (Eternity) - 영속성, 문서화 평가",
                "provider": "ollama",
                "philosophy_scores": {
                    "truth": 0.90,
                    "goodness": 0.90,
                    "beauty": 0.88,
                    "serenity": 0.95,
                },
            },
        }

    @staticmethod
    def get_fallback_scholars_config() -> dict[str, dict[str, Any]]:
        """SSOT 로드 실패 시 폴백 설정"""
        return {
            "codex": {
                "codename": "방통",
                "chinese": "Pangtong",
                "role": "구현·실행·프로토타이핑 담당",
                "philosophy_scores": {
                    "truth": 0.95,
                    "goodness": 0.90,
                    "beauty": 0.92,
                    "serenity": 0.88,
                },
            },
            "claude": {
                "codename": "자룡",
                "chinese": "Zhaoyun",
                "role": "논리 검증·리팩터링·구조 정렬 담당",
            },
            # Pillar 학자 매핑 (Ollama 기반)
            **ScholarConfigLoader.get_pillar_scholars_config(),
            "gemini": {
                "codename": "육손",
                "chinese": "Yukson",
                "role": "전략·철학·큰 그림 담당",
                "philosophy_scores": {
                    "truth": 0.97,
                    "goodness": 0.95,
                    "beauty": 0.92,
                    "serenity": 0.90,
                },
            },
            "ollama": {
                "codename": "영덕",
                "chinese": "Yeongdeok",
                "role": "로컬 설명·보안·프라이버시·Bridge Log 아카이빙",
                "philosophy_scores": {
                    "truth": 0.96,
                    "goodness": 0.98,
                    "beauty": 0.95,
                    "serenity": 0.99,
                },
            },
        }
