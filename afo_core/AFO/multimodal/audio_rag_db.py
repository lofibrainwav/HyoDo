"""
T-RAG LanceDB Manager - 오디오 시간적 데이터 벡터 저장소
Temporal RAG: 시간적 윈도우 기반 오디오 데이터 저장 및 검색
"""

import logging
from pathlib import Path
from typing import Any

try:
    import lancedb

    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logging.warning("lancedb not installed. RAG functionality will be limited")

logger = logging.getLogger(__name__)


class AudioRAGDatabase:
    """
    오디오 T-RAG용 LanceDB 관리자

    시간적 윈도우 기반 오디오 데이터 저장 및 검색
    """

    DB_NAME = "audio_temporal_rag"
    EMBEDDING_DIM = 512

    def __init__(self, db_path: str = "artifacts/audio_rag_db") -> None:
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        self._connection = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """데이터베이스 초기화"""
        if not LANCEDB_AVAILABLE:
            logger.warning("LanceDB not available. Using fallback storage.")
            return

        db_uri = str(self.db_path / self.DB_NAME)

        try:
            conn = lancedb.connect(db_uri)
            self._connection = conn

            existing_tables = conn.table_names()

            if self.DB_NAME in existing_tables:
                logger.info(f"Existing database found: {db_uri}")
            else:
                logger.info(f"Creating new database: {db_uri}")

                sample_data = [
                    {
                        "audio_path": "sample",
                        "duration": 0.0,
                        "sample_rate": 22050,
                        "bpm": 120.0,
                        "beat_strength": 0.5,
                        "spectral_centroid": [],
                        "harmony_chroma": [],
                        "temporal_sequence": [],
                        "embedding": [],
                        "created_at": 0.0,
                    }
                ]

                conn.create_table(
                    name=self.DB_NAME,
                    data=sample_data,
                    mode="overwrite",
                )
                logger.info("Table created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _get_schema(self) -> list[dict[str, Any]]:
        """LanceDB 스키마 정의"""
        return [
            {
                "name": "audio_path",
                "data_type": "string",
                "nullable": False,
            },
            {
                "name": "duration",
                "data_type": "float",
                "nullable": False,
            },
            {
                "name": "sample_rate",
                "data_type": "int",
                "nullable": False,
            },
            {
                "name": "bpm",
                "data_type": "float",
                "nullable": True,
            },
            {
                "name": "beat_strength",
                "data_type": "float",
                "nullable": True,
            },
            {
                "name": "spectral_centroid",
                "data_type": "list[float]",
                "nullable": True,
            },
            {
                "name": "harmony_chroma",
                "data_type": "list[float]",
                "nullable": True,
            },
            {
                "name": "temporal_sequence",
                "data_type": "list[dict]",
                "nullable": True,
            },
            {
                "name": "embedding",
                "data_type": "list[float]",
                "nullable": True,
            },
            {
                "name": "created_at",
                "data_type": "float",
                "nullable": False,
            },
        ]

    def add_audio_data(self, audio_data: dict[str, Any]) -> dict[str, Any]:
        """
        오디오 데이터 추가

        Args:
            audio_data: 오디오 분석 결과 데이터

        Returns:
            추가 결과
        """
        if not self._connection:
            return {
                "success": False,
                "error": "Database connection not available",
            }

        try:
            data_to_insert = self._prepare_data_for_insert(audio_data)

            table = self._connection.open_table(self.DB_NAME)
            table.add([data_to_insert])

            logger.info(f"Added audio data: {audio_data.get('audio_path', 'unknown')}")

            return {
                "success": True,
                "audio_path": audio_data.get("audio_path"),
            }
        except Exception as e:
            logger.error(f"Failed to add audio data: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _prepare_data_for_insert(self, audio_data: dict[str, Any]) -> dict[str, Any]:
        """데이터베이스 삽입용 데이터 준비"""
        features = audio_data.get("features", {})

        rhythm = features.get("rhythm", {})
        timbre = features.get("timbre", {})
        harmony = features.get("harmony", {})
        dynamics = features.get("dynamics", {})
        temporal_seq = features.get("temporal_sequence", {})

        return {
            "audio_path": audio_data.get("audio_path", ""),
            "duration": audio_data.get("duration", 0.0),
            "sample_rate": audio_data.get("sample_rate", 22050),
            "bpm": rhythm.get("bpm"),
            "beat_strength": rhythm.get("beat_strength"),
            "spectral_centroid": timbre.get("spectral_centroid", []),
            "harmony_chroma": harmony.get("chromagram", []),
            "temporal_sequence": temporal_seq.get("sequence", []),
            "rms_mean": dynamics.get("rms_mean", 0.0),
            "rms_std": dynamics.get("rms_std", 0.0),
            "dynamic_range": dynamics.get("dynamic_range", 0.0),
            "embedding": audio_data.get("embedding_vector", []),
            "created_at": audio_data.get("created_at", 0.0),
        }

    def search_by_temporal_window(
        self,
        start_time: float,
        end_time: float,
        _similarity_threshold: float = 0.7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        시간적 윈도우 기반 검색

        Args:
            start_time: 검색 시작 시간
            end_time: 검색 종료 시간
            similarity_threshold: 유사도 임계값
            limit: 최소 결과 수

        Returns:
            검색 결과
        """
        if not self._connection:
            logger.warning("Database connection not available for search")
            return []

        try:
            table = self._connection.open_table(self.DB_NAME)

            if table.count_rows() == 0:
                logger.warning("No data in table for temporal search")
                return []

            results = table.search().limit(limit).to_list()

            filtered_results = []
            for result in results:
                result_data = result.get("vector", result)
                created_at = result_data.get("created_at", 0.0)

                if start_time <= created_at <= end_time:
                    filtered_results.append(result_data)

            return filtered_results[:limit]
        except Exception as e:
            logger.error(f"Temporal search failed: {e}")
            return []

    def search_by_features(
        self,
        feature_filter: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        특성 기반 검색

        Args:
            feature_filter: 특성 필터 (예: {"bpm_min": 100, "bpm_max": 140})
            limit: 최소 결과 수

        Returns:
            검색 결과
        """
        if not self._connection:
            logger.warning("Database connection not available for feature search")
            return []

        try:
            table = self._connection.open_table("data")

            filter_parts = []

            if "bpm_min" in feature_filter:
                filter_parts.append(f"bpm >= {feature_filter['bpm_min']}")
            if "bpm_max" in feature_filter:
                filter_parts.append(f"bpm <= {feature_filter['bpm_max']}")
            if "beat_strength_min" in feature_filter:
                filter_parts.append(f"beat_strength >= {feature_filter['beat_strength_min']}")

            filter_str = " AND ".join(filter_parts) if filter_parts else None

            if filter_str:
                results = table.search().where(filter_str).limit(limit).to_list()
            else:
                results = table.search().limit(limit).to_list()

            return results
        except Exception as e:
            logger.error(f"Feature search failed: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """데이터베이스 통계 반환"""
        if not self._connection:
            return {
                "total_audios": 0,
                "error": "Database connection not available",
            }

        try:
            table = self._connection.open_table(self.DB_NAME)
            total_count = len(table)

            return {
                "total_audios": total_count,
                "db_path": str(self.db_path),
                "connection_status": "connected" if self._connection else "disconnected",
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_audios": 0,
                "error": str(e),
            }

    def close(self) -> None:
        """데이터베이스 연결 닫기"""
        if self._connection:
            pass
            self._connection = None
            logger.info("Database connection closed (LanceDB manages connection automatically)")


def initialize_audio_rag_db(db_path: str = "artifacts/audio_rag_db") -> AudioRAGDatabase:
    """
    오디오 T-RAG 데이터베이스 초기화 (편의 함수)

    Args:
        db_path: 데이터베이스 경로

    Returns:
        AudioRAGDatabase 인스턴스
    """
    db = AudioRAGDatabase(db_path)
    return db


if __name__ == "__main__":
    db = initialize_audio_rag_db()

    print("=" * 60)
    print("T-RAG LanceDB Manager 테스트")
    print("=" * 60)

    stats = db.get_stats()
    print("\n[데이터베이스 통계]")
    print(f"  - 총 오디오 수: {stats.get('total_audios', 0)}")
    print(f"  - 데이터베이스 경로: {stats.get('db_path', 'N/A')}")
    print(f"  - 연결 상태: {stats.get('connection_status', 'N/A')}")

    if stats.get("error"):
        print(f"  - 에러: {stats['error']}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

    db.close()
