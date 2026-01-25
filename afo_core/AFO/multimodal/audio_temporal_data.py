"""
T-RAG Audio Metadata - 시간적 임베딩용 오디오 메타데이터 구조
Temporal RAG: 오디오 신호를 시간 윈도우(Window)로 분석하여 벡터화
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AudioTemporalData:
    """
    오디오 시간적 T-RAG 데이터 구조

    시간 윈도우(Window) 기반 검색을 위해 오디오 특성을 시간적으로 임베딩

    Attributes:
        - audio_path: 오디오 파일 경로
        - duration: 오디오 길이 (초)
        - sample_rate: 샘플 레이트
        - features: 시간적 특징 딕셔너리 (rhythm, timbre, harmony, dynamics, temporal_sequence)
        - temporal_sequence: 슬라이딩 윈도우 별도 시계열
        - embedding: CLAP/HTS-AT 인코딩 벡터
        - metadata: 추가 메타데이터 (created_at, tags)
    """

    audio_path: str

    duration: float

    sample_rate: int

    features: dict[str, Any] = field(default_factory=dict)

    temporal_sequence: list[dict[str, Any]] = field(default_factory=list)

    embedding: list[float] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "audio_path": self.audio_path,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "features": self.features,
            "temporal_sequence": self.temporal_sequence,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioTemporalData":
        """딕셔너리에서 생성"""
        return cls(
            audio_path=data.get("audio_path", ""),
            duration=data.get("duration", 0.0),
            sample_rate=data.get("sample_rate", 22050),
            features=data.get("features", {}),
            temporal_sequence=data.get("temporal_sequence", []),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )


def create_search_index(_embedding_dim: int) -> str:
    """
    시간적 검색용 인덱스 구조 설명

    윈도우 기반 검색을 위해 embedding을 여러 차원으로 분리하여 저장

    Returns:
        LanceDB 스키마 정의
    """
    schema = """{
        "type": "object",
        "properties": {
            "audio_path": {"type": "string", "index": True},
            "duration": {"type": "float", "index": True},
            "sample_rate": {"type": "int", "index": True},
            "metadata": {"type": "object", "index": True},
            "features": {
                "type": "object",
                "properties": {
                    "rhythm": {
                        "type": "object",
                        "properties": {
                            "bpm": {"type": "float"},
                            "beat_strength": {"type": "float"}
                        }
                    },
                    "timbre": {
                        "type": "object",
                        "properties": {
                            "spectral_centroid": {"type": "array", "items": {"type": "float"}},
                            "spectral_rolloff": {"type": "array", "items": {"type": "float"}},
                            "zero_crossing_rate": {"type": "array", "items": {"type": "float"}}
                        }
                    },
                    "dynamics": {
                        "type": "object",
                        "properties": {
                            "rms_mean": {"type": "float"},
                            "rms_std": {"type": "float"},
                            "dynamic_range": {"type": "float"}
                        }
                    }
                }
            },
            "temporal_sequence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "window_index": {"type": "int"},
                        "window_start": {"type": "float"},
                        "window_end": {"type": "float"},
                        "features": {
                            "type": "object",
                            "properties": {
                                "mean": {"type": "float"},
                                "std": {"type": "float"},
                                "max": {"type": "float"},
                                "min": {"type": "float"},
                                "energy": {"type": "float"},
                                "zero_crossing_rate": {"type": "float"}
                            }
                        }
                    }
                }
            },
            "embedding": {
                "type": "array",
                "items": {"type": "float"}
            }
        }
    }
    """

    return schema


def build_temporal_query(
    start_time: float,
    end_time: float,
    features_filter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    시간적 검색 쿼리 빌더

    Args:
        start_time: 검색 시작 시간 (초)
        end_time: 검색 종료 시간 (초)
        features_filter: 특성 필터 (선택 사항)

    Returns:
        LanceDB 검색 쿼리
    """
    query = f"temporal_time >= {start_time} AND temporal_time <= {end_time}"

    if features_filter:
        for key, value in features_filter.items():
            query += f" AND features.{key} = {value}"

    return {
        "filter": query,
        "limit": 100,
    }


def prepare_temporal_sequence(features: dict[str, Any]) -> list[dict[str, Any]]:
    """
    시간적 시퀀스를 준비 (슬라이딩 윈도우)

    Args:
        features: 오디오 특성 딕셔너리

    Returns:
        시간적 시퀀스 (window별 특징)
    """
    sequence = []

    temporal_seq = features.get("temporal_sequence", {})
    windows = temporal_seq.get("windows", [])

    for window in windows:
        window_features = {
            "window_index": window.get("window_index", 0),
            "window_start": window.get("window_start", 0.0),
            "window_end": window.get("window_end", 0.0),
            "features": window.get("features", {}),
        }
        sequence.append(window_features)

    return sequence
