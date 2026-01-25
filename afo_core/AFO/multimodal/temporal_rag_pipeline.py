"""
T-RAG Pipeline - 오디오 시간적 RAG 파이프라인
Temporal RAG: 오디오 분석 → 임베딩 → DB 저장 → 검색
"""

import logging
from pathlib import Path
from typing import Any

from AFO.multimodal.audio_analyzer import AudioTemporalFeatures
from AFO.multimodal.audio_rag_db import initialize_audio_rag_db

logger = logging.getLogger(__name__)


class TemporalRAGPipeline:
    """
    T-RAG 파이프라인 (Temporal Retrieval-Augmented Generation)

    오디오의 시간적 특성을 분석하여 벡터 DB에 저장하고
    시간 윈도우 기반 검색을 제공

    Args:
        audio_analyzer: 오디오 분석기
        db: T-RAG 데이터베이스
    """

    def __init__(
        self,
        audio_analyzer: AudioTemporalFeatures | None = None,
        db_path: str = "artifacts/audio_rag_db",
    ) -> None:
        self.audio_analyzer = audio_analyzer

        if not audio_analyzer:
            self.audio_analyzer = None

        self.db = initialize_audio_rag_db(db_path)

        logger.info("T-RAG Pipeline initialized")

    def process_audio_file(self, audio_path: str) -> dict[str, Any]:
        """
        오디오 파일 처리 (분석 → DB 저장)

        Args:
            audio_path: 오디오 파일 경로

        Returns:
            처리 결과
        """
        if not Path(audio_path).exists():
            return {
                "success": False,
                "error": f"Audio file not found: {audio_path}",
            }

        try:
            analyzer = AudioTemporalFeatures(audio_path)
            analyzer._extract_temporal_features()

            audio_data = analyzer.to_dict()

            result = self.db.add_audio_data(audio_data)

            logger.info(f"Processed audio: {audio_path}")

            return result
        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def batch_process_audio_files(self, audio_paths: list[str]) -> dict[str, Any]:
        """
        여러 오디오 파일 배치 처리

        Args:
            audio_paths: 오디오 파일 경로 리스트

        Returns:
            배치 처리 결과
        """
        results = []
        processed = 0
        failed = 0

        for audio_path in audio_paths:
            result = self.process_audio_file(audio_path)

            if result.get("success"):
                processed += 1
            else:
                failed += 1

            results.append(result)

        summary = {
            "success": True,
            "total": len(audio_paths),
            "processed": processed,
            "failed": failed,
            "results": results,
        }

        logger.info(f"Batch processed: {processed}/{len(audio_paths)}")

        return summary

    def search_by_temporal_window(
        self,
        start_time: float,
        end_time: float,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        시간적 윈도우 기반 검색

        Args:
            start_time: 검색 시작 시간
            end_time: 검색 종료 시간
            limit: 최소 결과 수

        Returns:
            검색 결과
        """
        return self.db.search_by_temporal_window(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def search_by_features(
        self,
        feature_filter: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        특성 기반 검색

        Args:
            feature_filter: 특성 필터
            limit: 최소 결과 수

        Returns:
            검색 결과
        """
        return self.db.search_by_features(
            feature_filter=feature_filter,
            limit=limit,
        )

    def get_pipeline_stats(self) -> dict[str, Any]:
        """
        파이프라인 통계 반환

        Returns:
            파이프라인 통계
        """
        db_stats = self.db.get_stats()

        return {
            "db_status": db_stats.get("connection_status", "unknown"),
            "total_audios": db_stats.get("total_audios", 0),
            "db_path": db_stats.get("db_path", "unknown"),
            "analyzer_initialized": self.audio_analyzer is not None,
        }

    def close(self) -> None:
        """파이프라인 닫기"""
        self.db.close()
        logger.info("T-RAG Pipeline closed")


def create_temporal_rag_pipeline(db_path: str = "artifacts/audio_rag_db") -> TemporalRAGPipeline:
    """
    T-RAG 파이프라인 초기화 (편의 함수)

    Args:
        db_path: 데이터베이스 경로

    Returns:
        TemporalRAGPipeline 인스턴스
    """
    pipeline = TemporalRAGPipeline(db_path=db_path)
    return pipeline


if __name__ == "__main__":
    pipeline = create_temporal_rag_pipeline()

    print("=" * 60)
    print("T-RAG Pipeline 테스트")
    print("=" * 60)

    stats = pipeline.get_pipeline_stats()
    print("\n[파이프라인 상태]")
    print(f"  - DB 연결: {stats.get('db_status', 'unknown')}")
    print(f"  - 총 오디오: {stats.get('total_audios', 0)}")
    print(f"  - DB 경로: {stats.get('db_path', 'N/A')}")

    pipeline.close()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
