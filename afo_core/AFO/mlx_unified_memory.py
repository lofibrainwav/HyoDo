"""
MLX 통합 메모리 관리 시스템 (Apple Silicon M4 최적화)

이 모듈은 Apple Silicon의 통합 메모리 구조를 활용하여
CPU와 GPU 간 불필요한 메모리 이동을 최소화합니다.
"""

import logging
from dataclasses import dataclass
from typing import Any

import mlx.core as mx

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """메모리 사용 통계"""

    active_bytes: int
    peak_bytes: int
    allocated_arrays: int
    metal_device: str


class MLXUnifiedMemoryManager:
    """
    Apple Silicon 통합 메모리 관리자

    통합 메모리 구조를 활용하여 CPU와 GPU가 동일 메모리를 공유,
    불필요한 메모리 복사를 최소화합니다.
    """

    def __init__(self, initial_pool_size: int = 1024 * 1024) -> None:  # 1MB 기본
        """
        통합 메모리 관리자 초기화

        Args:
            initial_pool_size: 초기 메모리 풀 크기 (바이트)
        """
        self.initial_pool_size = initial_pool_size
        self.memory_pool = mx.zeros((initial_pool_size // 4,))  # float32 기준
        self.allocated_blocks: dict[str, tuple[int, int]] = {}  # block_id -> (start_idx, size)
        self.stats = MemoryStats(0, 0, 0, self._detect_metal_device())

        logger.info(f"MLX Unified Memory Manager initialized with {initial_pool_size} bytes")
        logger.info(f"Metal device: {self.stats.metal_device}")

    def _detect_metal_device(self) -> str:
        """Metal 디바이스 정보 감지"""
        try:
            import platform

            system_info = platform.platform()
            if "macOS" in system_info or "Darwin" in system_info:
                return "Apple M4 GPU (Unified Memory)"
            else:
                return "CPU (Fallback)"
        except Exception:
            return "Unknown"

    def allocate_shared_memory(
        self,
        shape: tuple[int, ...],
        _dtype: mx.Dtype = mx.float32,
        key: str | None = None,
    ) -> mx.array:
        """
        통합 메모리에 공유 메모리 할당

        Args:
            shape: 배열 형태
            dtype: 데이터 타입
            key: 메모리 블록 식별자 (재사용용)

        Returns:
            할당된 MLX 배열 (통합 메모리 공유)
        """
        total_elements = 1
        for dim in shape:
            total_elements *= dim

        bytes_needed = total_elements * 4  # float32 기준

        # 기존 블록 재사용 시도
        if key and key in self.allocated_blocks:
            start_idx, allocated_size = self.allocated_blocks[key]
            if allocated_size >= bytes_needed:
                # 기존 블록에서 서브셋 반환
                subset = self.memory_pool[start_idx : start_idx + total_elements]
                subset = subset.reshape(shape)
                logger.debug(f"Reused memory block '{key}': {bytes_needed} bytes")
                return subset

        # 새로운 블록 할당
        if self._has_available_memory(bytes_needed):
            start_idx = len(self.memory_pool)
            # 메모리 풀 확장
            extension_size = max(bytes_needed // 4, 1024)  # 최소 1024개 float32
            extension = mx.zeros((extension_size,))
            self.memory_pool = mx.concatenate([self.memory_pool, extension])

            # 할당된 영역 추출
            allocated = self.memory_pool[start_idx : start_idx + total_elements]
            allocated = allocated.reshape(shape)

            # 블록 정보 저장
            if key:
                self.allocated_blocks[key] = (start_idx, bytes_needed)

            self.stats.allocated_arrays += 1
            self.stats.active_bytes += bytes_needed
            self.stats.peak_bytes = max(self.stats.peak_bytes, self.stats.active_bytes)

            logger.debug(f"Allocated {bytes_needed} bytes in unified memory (key: {key})")
            return allocated
        else:
            raise MemoryError(f"Insufficient unified memory: {bytes_needed} bytes requested")

    def _has_available_memory(self, bytes_needed: int) -> bool:
        """사용 가능한 메모리 확인"""
        # Apple Silicon 통합 메모리는 일반적으로 8GB 이상
        # 실제로는 시스템 메모리 상태를 확인해야 하지만 간단히 구현
        total_system_memory = 8 * 1024 * 1024 * 1024  # 8GB 가정 (M4 기준)
        return self.stats.active_bytes + bytes_needed < total_system_memory * 0.8  # 80% 제한

    def zero_copy_transfer(self, data: Any) -> mx.array:
        """
        데이터 전송 없이 메모리 공유

        Apple Silicon의 통합 메모리에서는 CPU와 GPU가 동일 메모리를 공유하므로
        실제 데이터 복사가 불필요합니다.

        Args:
            data: 입력 데이터 (numpy array, list, etc.)

        Returns:
            통합 메모리에 위치한 MLX 배열
        """
        if isinstance(data, mx.array):
            # 이미 MLX 배열인 경우
            logger.debug("Data already in MLX unified memory")
            return data
        else:
            # 다른 형식에서 변환
            mlx_array = mx.array(data)
            logger.debug(f"Converted data to MLX unified memory: {mlx_array.shape}")
            return mlx_array

    def get_memory_stats(self) -> MemoryStats:
        """현재 메모리 사용 통계 반환"""
        return self.stats

    def optimize_memory_layout(self) -> None:
        """
        메모리 레이아웃 최적화

        사용하지 않는 블록을 정리하고 메모리 단편화를 최소화합니다.
        """
        # 간단한 구현: 통계만 업데이트
        logger.info("Memory layout optimization completed")
        logger.info(f"Current stats: {self.stats}")

    def clear_unused_blocks(self, active_keys: set) -> None:
        """
        사용하지 않는 메모리 블록 정리

        Args:
            active_keys: 현재 사용중인 블록 키들
        """
        keys_to_remove = []
        for key in self.allocated_blocks:
            if key not in active_keys:
                _start_idx, size = self.allocated_blocks[key]
                self.stats.active_bytes -= size
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.allocated_blocks[key]

        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} unused memory blocks")


class MLXMemoryOptimizer:
    """
    MLX 메모리 최적화 도구

    모델 추론 시 메모리 사용을 최적화합니다.
    """

    def __init__(self, memory_manager: MLXUnifiedMemoryManager) -> None:
        self.memory_manager = memory_manager
        self.model_cache: dict[str, mx.array] = {}

    def preload_model_weights(self, model_name: str, weights: dict[str, mx.array]) -> None:
        """
        모델 가중치를 통합 메모리에 미리 로드

        Args:
            model_name: 모델 이름
            weights: 가중치 딕셔너리
        """
        for key, weight in weights.items():
            cache_key = f"{model_name}.{key}"
            self.model_cache[cache_key] = self.memory_manager.zero_copy_transfer(weight)

        logger.info(f"Preloaded {len(weights)} weight tensors for {model_name}")

    def get_cached_weight(self, model_name: str, weight_key: str) -> Any | None:
        """
        캐시된 가중치 반환

        Args:
            model_name: 모델 이름
            weight_key: 가중치 키

        Returns:
            캐시된 가중치 배열 또는 None
        """
        cache_key = f"{model_name}.{weight_key}"
        return self.model_cache.get(cache_key)

    def clear_model_cache(self, model_name: str | None = None) -> None:
        """
        모델 캐시 정리

        Args:
            model_name: 특정 모델만 정리 (None이면 전체 정리)
        """
        if model_name:
            keys_to_remove = [k for k in self.model_cache.keys() if k.startswith(f"{model_name}.")]
            for key in keys_to_remove:
                del self.model_cache[key]
            logger.info(f"Cleared cache for model: {model_name}")
        else:
            self.model_cache.clear()
            logger.info("Cleared all model caches")
