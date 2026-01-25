#!/usr/bin/env python3
"""
Suno vs 오픈소스 음악 생성 비교 분석기
AFO 왕국의 전략적 학습을 위한 품질/속도/스타일 비교 프레임워크
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# PYTHONPATH 설정
sys.path.insert(0, "/Users/brnestrm/Library/Python/3.9/lib/python/site-packages")

# AFO 모듈 import (Python 3.9 호환성 문제로 독립 실행 모드만 사용)
print("⚠️ Python 3.9 호환성 문제로 AFO 모듈 직접 import 생략 - 독립 실행 모드로 진행")
get_music_router = None
run_suno_pipeline = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class MusicQualityMetrics:
    """음악 품질 메트릭"""

    sample_rate: int = 0
    bit_rate: int = 0
    duration: float = 0.0
    channels: int = 0
    file_size_bytes: int = 0

    # 품질 점수 (0-100)
    clarity_score: float = 0.0  # 명확성
    dynamics_score: float = 0.0  # 다이내믹스
    harmony_score: float = 0.0  # 화성
    rhythm_score: float = 0.0  # 리듬
    overall_quality: float = 0.0  # 종합 품질

    # 스타일 분석
    instrumentation_score: float = 0.0  # 악기 구성
    genre_confidence: dict[str, float] = None  # 장르 신뢰도
    mood_confidence: dict[str, float] = None  # 분위기 신뢰도

    def __post_init__(self) -> None:
        if self.genre_confidence is None:
            self.genre_confidence = {}
        if self.mood_confidence is None:
            self.mood_confidence = {}


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""

    generation_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    network_requests: int = 0
    api_calls: int = 0
    retries: int = 0
    errors: list[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


@dataclass
class ComparisonResult:
    """비교 분석 결과"""

    timeline_state: dict[str, Any]
    suno_result: dict[str, Any]
    opensource_result: dict[str, Any]
    suno_metrics: MusicQualityMetrics
    opensource_metrics: MusicQualityMetrics
    suno_performance: PerformanceMetrics
    opensource_performance: PerformanceMetrics

    # 비교 분석
    quality_difference: float = 0.0  # 품질 차이 (Suno - 오픈소스)
    speed_difference: float = 0.0  # 속도 차이 (Suno - 오픈소스)
    style_similarity: float = 0.0  # 스타일 유사도 (0-1)

    # 학습 인사이트
    suno_strengths: list[str] = None
    opensource_strengths: list[str] = None
    improvement_opportunities: list[str] = None

    timestamp: str = ""
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.suno_strengths is None:
            self.suno_strengths = []
        if self.opensource_strengths is None:
            self.opensource_strengths = []
        if self.improvement_opportunities is None:
            self.improvement_opportunities = []
        if not self.timestamp:
            from datetime import datetime

            self.timestamp = datetime.now().isoformat()


class MusicComparisonAnalyzer:
    """
    Suno vs 오픈소스 음악 생성 비교 분석기
    """

    def __init__(self, output_dir: str = "artifacts/music_comparison") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.router = get_music_router() if get_music_router else None

    def analyze_audio_file(self, file_path: str) -> MusicQualityMetrics:
        """
        오디오 파일 분석 (기술적 메트릭)
        실제로는 ffprobe나 librosa 등을 사용하지만 여기서는 mock
        """
        path = Path(file_path)
        if not path.exists():
            return MusicQualityMetrics()

        # 실제 분석 로직 (ffprobe + librosa 사용 권장)
        # 여기서는 파일 존재 여부만 확인
        file_size = path.stat().st_size

        # Mock 데이터 생성 (실제로는 ffprobe로 분석)
        metrics = MusicQualityMetrics(
            sample_rate=44100,  # 일반적인 값
            bit_rate=128000,  # 일반적인 값
            duration=30.0,  # 가정
            channels=2,  # 스테레오
            file_size_bytes=file_size,
            # 품질 점수 (실제로는 전문가 평가나 AI 분석)
            clarity_score=75.0,
            dynamics_score=70.0,
            harmony_score=80.0,
            rhythm_score=65.0,
            overall_quality=72.5,
            genre_confidence={"epic_orchestral": 0.8, "cinematic": 0.6},
            mood_confidence={"heroic": 0.7, "triumphant": 0.8},
            instrumentation_score=78.0,
        )

        return metrics

    def measure_performance(self, func, *args, **kwargs) -> tuple:
        """
        함수 실행 성능 측정
        """
        start_time = time.time()
        start_memory = 0  # 실제로는 psutil로 측정

        try:
            result = func(*args, **kwargs)
            errors = []
        except Exception as e:
            result = None
            errors = [str(e)]

        end_time = time.time()
        end_memory = 0  # 실제로는 psutil로 측정

        performance = PerformanceMetrics(
            generation_time_seconds=end_time - start_time,
            memory_usage_mb=max(0, end_memory - start_memory),
            errors=errors,
        )

        return result, performance

    def generate_with_suno(self, timeline_state: dict[str, Any]) -> dict[str, Any]:
        """
        Suno로 음악 생성
        """
        if not run_suno_pipeline:
            return {"error": "Suno pipeline not available", "success": False}

        try:
            result = run_suno_pipeline(
                timeline_state,
                dry_run=False,
                target_av_duration_sec=30,
                video_path_for_fusion=None,
            )
            return result
        except Exception as e:
            logger.error(f"Suno generation failed: {e}")
            return {"error": str(e), "success": False}

    def generate_with_opensource(self, timeline_state: dict[str, Any]) -> dict[str, Any]:
        """
        오픈소스 Provider로 음악 생성
        """
        if not self.router:
            return {"error": "Music router not available", "success": False}

        try:
            result = self.router.generate_music(
                timeline_state, quality="high", local_only=True, max_cost=0.0
            )
            return result
        except Exception as e:
            logger.error(f"Open source generation failed: {e}")
            return {"error": str(e), "success": False}

    def compare_providers(self, timeline_state: dict[str, Any]) -> ComparisonResult:
        """
        두 Provider 비교 분석
        """
        logger.info("🎵 음악 생성 비교 분석 시작")

        # Suno 생성
        logger.info("🎵 Suno로 음악 생성 중...")
        suno_result, suno_performance = self.measure_performance(
            self.generate_with_suno, timeline_state
        )

        # 오픈소스 생성
        logger.info("🎵 오픈소스로 음악 생성 중...")
        opensource_result, opensource_performance = self.measure_performance(
            self.generate_with_opensource, timeline_state
        )

        # 품질 분석
        suno_metrics = MusicQualityMetrics()
        opensource_metrics = MusicQualityMetrics()

        if suno_result and suno_result.get("success"):
            audio_path = suno_result.get("outputs", {}).get("audio_raw")
            if audio_path:
                suno_metrics = self.analyze_audio_file(audio_path)

        if opensource_result and opensource_result.get("success"):
            audio_path = opensource_result.get("output_path")
            if audio_path:
                opensource_metrics = self.analyze_audio_file(audio_path)

        # 비교 계산
        quality_diff = suno_metrics.overall_quality - opensource_metrics.overall_quality
        speed_diff = (
            opensource_performance.generation_time_seconds
            - suno_performance.generation_time_seconds
        )

        # 스타일 유사도 계산 (간단 버전)
        style_similarity = 0.5  # 실제로는 더 정교한 계산 필요

        # 강점 분석
        suno_strengths = []
        opensource_strengths = []
        improvements = []

        if suno_metrics.overall_quality > opensource_metrics.overall_quality:
            suno_strengths.append("더 높은 음악 품질")
        else:
            opensource_strengths.append("로컬 실행으로 인한 프라이버시")

        if (
            suno_performance.generation_time_seconds
            < opensource_performance.generation_time_seconds
        ):
            suno_strengths.append("더 빠른 생성 속도")
        else:
            opensource_strengths.append("무료 사용")

        if suno_metrics.harmony_score > opensource_metrics.harmony_score:
            suno_strengths.append("더 정교한 화성 구성")
            improvements.append("화성 생성 알고리즘 향상 필요")

        # 결과 생성
        result = ComparisonResult(
            timeline_state=timeline_state,
            suno_result=suno_result or {},
            opensource_result=opensource_result or {},
            suno_metrics=suno_metrics,
            opensource_metrics=opensource_metrics,
            suno_performance=suno_performance,
            opensource_performance=opensource_performance,
            quality_difference=quality_diff,
            speed_difference=speed_diff,
            style_similarity=style_similarity,
            suno_strengths=suno_strengths,
            opensource_strengths=opensource_strengths,
            improvement_opportunities=improvements,
        )

        return result

    def save_comparison_result(self, result: ComparisonResult, filename: str = None) -> str:
        """
        비교 결과를 파일로 저장
        """
        if not filename:
            timestamp = result.timestamp.replace(":", "").replace("-", "").replace(".", "_")
            filename = f"comparison_{timestamp}.json"

        output_path = self.output_dir / filename

        # JSON 직렬화 가능한 형태로 변환
        result_dict = asdict(result)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 비교 결과 저장됨: {output_path}")
        return str(output_path)


def create_test_timeline() -> dict[str, Any]:
    """
    테스트용 TimelineState 생성
    """
    return {
        "title": "AFO Kingdom Victory Theme",
        "sections": [
            {
                "start": 0,
                "end": 3,
                "text": "Epic orchestral introduction",
                "music_directive": "slow_heroic_build",
            },
            {
                "start": 3,
                "end": 6,
                "text": "Intense battle climax",
                "music_directive": "powerful_orchestral_climax",
            },
            {
                "start": 6,
                "end": 9,
                "text": "Triumphant victory fanfare",
                "music_directive": "triumphant_brass_fanfare",
            },
        ],
        "music": {
            "style": "epic_orchestral_cinematic",
            "mood": "heroic_triumphant",
            "tempo": "dramatic",
        },
    }


def main() -> None:
    """
    메인 실행 함수
    """
    print("🎵 AFO 왕국 Suno vs 오픈소스 음악 생성 비교 분석기")
    print("=" * 60)

    analyzer = MusicComparisonAnalyzer()

    # 테스트 TimelineState
    timeline = create_test_timeline()
    print(f"📋 테스트 TimelineState: {timeline['title']}")

    # 비교 분석 실행
    try:
        result = analyzer.compare_providers(timeline)

        # 결과 출력
        print("\n📊 분석 결과:")
        print(f"🎵 품질 차이: {result.quality_difference:.2f}")
        print(f"⚡ 속도 차이: {result.speed_difference:.2f}")
        print(f"🎵 스타일 유사도: {result.style_similarity:.2f}")

        print("\n🏆 Suno 강점:")
        for strength in result.suno_strengths:
            print(f"  ✅ {strength}")

        print("\n🌟 오픈소스 강점:")
        for strength in result.opensource_strengths:
            print(f"  ✅ {strength}")

        print("\n📈 개선 기회:")
        for improvement in result.improvement_opportunities:
            print(f"  🎯 {improvement}")

        # 결과 저장
        saved_path = analyzer.save_comparison_result(result)
        print(f"\n💾 결과 저장됨: {saved_path}")

        # 학습 인사이트
        print("\n🧠 학습 인사이트:")
        if result.quality_difference > 10:
            print("  📊 Suno 품질이 크게 우세 - 화성/리듬 알고리즘 집중 개선 필요")
        elif result.speed_difference > 30:
            print("  ⚡ 오픈소스 속도가 크게 느림 - 모델 최적화 필요")

        print("\n✅ 비교 분석 완료!")
        print("이 데이터를 기반으로 오픈소스 모델 향상 계획 수립 가능")

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
