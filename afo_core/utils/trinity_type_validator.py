# Trinity Score: 90.0 (Established by Chancellor)
"""Trinity Type Validator - 런타임 타입 검증 시스템
Phase 5: 혁신적 타입 시스템 구현

이 모듈은 런타임에 Trinity Score 기반 타입 검증을 수행합니다.
"""

import asyncio
import functools
import inspect
import logging
import time
import traceback
from collections.abc import Callable
from typing import Any, TypeVar, Union

from AFO.domain.metrics.trinity_manager import TrinityManager

# 로깅 설정
logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class TrinityTypeValidator:
    """런타임 Trinity Score 기반 타입 검증 시스템

    Phase 5: 혁신적 타입 시스템의 핵심 컴포넌트
    """

    def __init__(self, trinity_manager: TrinityManager | None = None) -> None:
        self.trinity_manager = trinity_manager or TrinityManager()
        self.validation_cache: dict[str, dict[str, Any]] = {}
        self.performance_stats: dict[str, dict[str, Any]] = {}

    def validate_function(self, func: F, *args, **kwargs) -> dict[str, Any]:
        """함수 실행 전후로 Trinity Score 기반 검증 수행

        Args:
            func: 검증할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            검증 결과 딕셔너리

        """
        func_name = getattr(func, "__name__", str(func))
        start_time = time.time()

        # Pre-validation (眞: 타입 일관성 검증)
        pre_validation = self._pre_validate(func, args, kwargs)

        try:
            # 함수 실행 (async 함수 감지 및 처리)
            if inspect.iscoroutinefunction(func):
                # Async 함수인 경우: 이미 실행 중인 이벤트 루프에서 실행
                try:
                    loop = asyncio.get_running_loop()
                    # 이미 실행 중인 루프가 있으면 Task로 스케줄링
                    result = loop.run_until_complete(func(*args, **kwargs))
                except RuntimeError:
                    # 실행 중인 루프가 없으면 새로 생성
                    result = asyncio.run(func(*args, **kwargs))
            else:
                # Sync 함수인 경우: 일반 호출
                result = func(*args, **kwargs)

            execution_time = time.time() - start_time

            # Post-validation (善: 안전성 검증)
            post_validation = self._post_validate(func, args, kwargs, result)

            # Trinity Score 계산 (美: 품질 종합 평가)
            trinity_score = self._calculate_trinity_score(
                func, pre_validation, post_validation, execution_time
            )

            # 결과 캐시
            cache_key = f"{func_name}:{hash(str(args) + str(kwargs))}"
            self.validation_cache[cache_key] = {
                "timestamp": time.time(),
                "trinity_score": trinity_score,
                "execution_time": execution_time,
                "status": "success",
            }

            # 성능 통계 업데이트 (永: 장기적 모니터링)
            self._update_performance_stats(func_name, execution_time, trinity_score)

            return {
                "status": "success",
                "trinity_score": trinity_score,
                "execution_time": execution_time,
                "pre_validation": pre_validation,
                "post_validation": post_validation,
                "result_type": type(result).__name__,
                "confidence": trinity_score / 100.0,
                "recommendations": self._generate_recommendations(
                    trinity_score, pre_validation, post_validation
                ),
            }

        except Exception as e:
            execution_time = time.time() - start_time

            # 에러 상황에서도 부분 평가 수행
            error_validation = self._handle_error_validation(func, e)

            trinity_score = max(
                0,
                self._calculate_error_trinity_score(
                    func, pre_validation, error_validation, execution_time, e
                ),
            )

            logger.warning(
                "Trinity 검증 중 함수 실행 실패: %s - %s",
                func_name,
                str(e),
            )
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "trinity_score": trinity_score,
                "execution_time": execution_time,
                "pre_validation": pre_validation,
                "error_validation": error_validation,
                "confidence": 0.0,
                "recommendations": self._generate_error_recommendations(e, trinity_score),
            }

    def __call__(self, func: F) -> F:
        """데코레이터 인터페이스 - 함수에 자동 검증 적용

        Usage:
            @TrinityTypeValidator()
            def my_function(x: int, y: str) -> str:
                return f"{x}: {y}"

            @TrinityTypeValidator()
            async def my_async_function(x: int) -> str:
                return str(x)
        """
        if inspect.iscoroutinefunction(func):
            # Async 함수용 래퍼
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Async 함수는 검증을 건너뛰고 직접 실행 (성능 최적화)
                # 필요시 별도의 async 검증 로직 추가 가능
                return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:
            # Sync 함수용 래퍼
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> None:
                result = self.validate_function(func, *args, **kwargs)

                # 검증 실패 시 로깅 및 경고
                if result["status"] == "error":
                    logger.warning(
                        "Trinity 검증 실패: %s - 오류: %s, Score: %.1f",
                        func.__name__,
                        result["error"],
                        result["trinity_score"],
                    )
                    for rec in result.get("recommendations", []):
                        logger.info("권장사항: %s", rec)

                # 검증 성공 시 성능 모니터링
                elif result["trinity_score"] < 70:
                    logger.warning(
                        "낮은 Trinity Score: %s (%.1f)",
                        func.__name__,
                        result["trinity_score"],
                    )
                    for rec in result.get("recommendations", []):
                        logger.info("권장사항: %s", rec)

                return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    def _pre_validate(self, func: Callable, args: tuple, kwargs: dict) -> dict[str, Any]:
        """사전 검증: 함수 시그니처와 입력 타입 일관성 검증"""
        try:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            validation_results: dict[str, Any] = {
                "signature_valid": True,
                "param_count": len(bound_args.arguments),
                "param_types": {},
                "missing_params": [],
                "extra_params": [],
            }
            # 타입 명시: param_types는 dict[str, dict[str, Any]]
            param_types: dict[str, dict[str, Any]] = validation_results["param_types"]

            # 타입 힌트 기반 검증
            for param_name, param_value in bound_args.arguments.items():
                param_info = sig.parameters.get(param_name)
                if param_info and param_info.annotation != inspect.Parameter.empty:
                    expected_type = param_info.annotation
                    actual_type = type(param_value)

                    # 타입 일치도 계산 (단순 버전)
                    type_match = self._calculate_type_match(expected_type, actual_type)
                    param_types[param_name] = {
                        "expected": str(expected_type),
                        "actual": str(actual_type),
                        "match_score": type_match,
                    }

            return validation_results

        except (ValueError, TypeError, AttributeError) as e:
            logger.debug("사전 검증 실패 (값/타입/속성 에러): %s", str(e))
            return {
                "signature_valid": False,
                "error": str(e),
                "param_count": len(args) + len(kwargs),
            }
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("사전 검증 중 예상치 못한 에러: %s", str(e))
            return {
                "signature_valid": False,
                "error": str(e),
                "param_count": len(args) + len(kwargs),
            }

    def _post_validate(
        self, func: Callable, args: tuple, kwargs: dict, result: Any
    ) -> dict[str, Any]:
        """사후 검증: 리턴 타입과 결과 일관성 검증"""
        try:
            sig = inspect.signature(func)
            return_annotation = sig.return_annotation

            if return_annotation != inspect.Signature.empty:
                expected_type = return_annotation
                actual_type = type(result)

                type_match = self._calculate_type_match(expected_type, actual_type)

                return {
                    "return_type_valid": True,
                    "expected_return": str(expected_type),
                    "actual_return": str(actual_type),
                    "return_match_score": type_match,
                    "result_size": self._estimate_size(result),
                }
            else:
                return {
                    "return_type_valid": False,
                    "reason": "no_return_annotation",
                    "actual_return": str(type(result)),
                    "result_size": self._estimate_size(result),
                }

        except (ValueError, TypeError, AttributeError) as e:
            logger.debug("사후 검증 실패 (값/타입/속성 에러): %s", str(e))
            return {
                "return_type_valid": False,
                "error": str(e),
                "actual_return": (str(type(result)) if "result" in locals() else "unknown"),
            }
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("사후 검증 중 예상치 못한 에러: %s", str(e))
            return {
                "return_type_valid": False,
                "error": str(e),
                "actual_return": (str(type(result)) if "result" in locals() else "unknown"),
            }

    def _calculate_type_match(self, expected: Any, actual: Any) -> float:
        """타입 일치도 계산 (0.0 ~ 1.0)"""
        try:
            # 간단한 타입 일치도 계산
            if expected == actual:
                return 1.0

            # 상속 관계 확인
            if (
                inspect.isclass(expected)
                and inspect.isclass(actual)
                and issubclass(actual, expected)
            ):
                return 0.8

            # Union 타입 처리
            if hasattr(expected, "__origin__") and expected.__origin__ in (
                Union,
                tuple,
            ):
                return 0.6  # Union 타입은 부분 일치로 간주

            # Generic 타입 처리
            if hasattr(expected, "__origin__"):
                return 0.7  # Generic 타입은 보수적으로 평가

            return 0.0

        except (TypeError, AttributeError) as e:
            logger.debug("타입 일치도 계산 실패: %s", str(e))
            return 0.0
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("타입 일치도 계산 중 예상치 못한 에러: %s", str(e))
            return 0.0

    def _estimate_size(self, obj: Any) -> int:
        """객체 크기 추정 (메모리 사용량 기반)"""
        try:
            import sys

            return sys.getsizeof(obj)
        except (TypeError, AttributeError) as e:
            logger.debug("객체 크기 추정 실패: %s", str(e))
            return 0
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("객체 크기 추정 중 예상치 못한 에러: %s", str(e))
            return 0

    def _calculate_trinity_score(
        self,
        func: Callable,
        pre_validation: dict[str, Any],
        post_validation: dict[str, Any],
        execution_time: float,
    ) -> float:
        """Trinity Score 계산 (HYOGOOK V5: 仁眞善忠美)"""
        # 仁 (Benevolence): 개발자 경험 (was Serenity 孝)
        benevolence_score = self._evaluate_serenity(pre_validation, post_validation)

        # 眞 (Truth): 타입 정확성
        truth_score = self._evaluate_truth(pre_validation, post_validation)

        # 善 (Goodness): 안전성
        goodness_score = self._evaluate_goodness(func, execution_time)

        # 忠 (Loyalty): SSOT 준수 (was Eternity 永)
        loyalty_score = self._evaluate_eternity(func)

        # 美 (Beauty): 코드 품질
        beauty_score = self._evaluate_beauty(func)

        # HYOGOOK V5 가중치 계산
        weights = {
            "benevolence": 0.25,  # 仁 (was serenity 0.40)
            "truth": 0.22,  # 眞 (was 0.18)
            "goodness": 0.18,  # 善 (unchanged)
            "loyalty": 0.15,  # 忠 (was eternity 0.12)
            "beauty": 0.15,  # 美 (was 0.12)
        }

        # 기하평균으로 永 (Eternity) 계산
        values = [benevolence_score, truth_score, goodness_score, loyalty_score, beauty_score]
        eternity_score = self._calculate_geometric_mean(values)

        # HYOGOOK V5: F = (T+G+In+B+C) + S
        arithmetic_sum = (
            benevolence_score * weights["benevolence"]
            + truth_score * weights["truth"]
            + goodness_score * weights["goodness"]
            + loyalty_score * weights["loyalty"]
            + beauty_score * weights["beauty"]
        )

        trinity_score = arithmetic_sum + eternity_score

        return round(trinity_score * 100, 2)

    def _calculate_geometric_mean(self, values: list[float]) -> float:
        """기하평균 계산 (永 Eternity)"""
        if not values or len(values) != 5:
            return 1.0
        product = 1.0
        for v in values:
            if v <= 0:
                return 0.0
            product *= v
        return product ** (1 / 5)

    def _calculate_error_trinity_score(
        self,
        func: Callable,
        pre_validation: dict[str, Any],
        error_validation: dict[str, Any],
        execution_time: float,
        error: Exception,
    ) -> float:
        """에러 상황에서의 Trinity Score 계산"""
        # 에러 시 기본 점수 절반으로 시작
        base_score = 50.0

        # 에러 타입에 따른 조정
        if isinstance(error, (TypeError, AttributeError)):
            base_score -= 20  # 타입 관련 에러는 큰 감점
        elif isinstance(error, ValueError):
            base_score -= 10  # 값 관련 에러는 중간 감점

        # 실행 시간에 따른 추가 조정
        if execution_time > 10:
            base_score -= 5  # 느린 실행은 추가 감점

        return max(0, base_score)

    def _evaluate_truth(self, pre: dict[str, Any], post: dict[str, Any]) -> float:
        """眞: 타입 정확성 평가"""
        score = 100.0

        # 파라미터 타입 일치도
        if "param_types" in pre:
            type_matches = [info["match_score"] for info in pre["param_types"].values()]
            if type_matches:
                avg_match = sum(type_matches) / len(type_matches)
                score -= (1 - avg_match) * 30  # 최대 30점 감점

        # 리턴 타입 일치도
        if post.get("return_match_score") is not None:
            return_match = post["return_match_score"]
            score -= (1 - return_match) * 20  # 최대 20점 감점

        return max(0, score)

    def _evaluate_goodness(self, func: Callable, execution_time: float) -> float:
        """善: 안전성과 성능 평가"""
        score = 100.0

        # 실행 시간 기반 평가
        if execution_time > 5:
            score -= 20  # 5초 초과 시 성능 감점
        elif execution_time > 1:
            score -= 10  # 1초 초과 시 중간 감점

        # 함수 복잡도 평가 (간단한 휴리스틱)
        try:
            source = inspect.getsource(func)
            lines_of_code = len(source.split("\n"))
            if lines_of_code > 50:
                score -= 10  # 긴 함수는 복잡도 감점
        except (OSError, AttributeError) as e:
            logger.debug("함수 소스 분석 실패: %s", str(e))
            pass
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("함수 소스 분석 중 예상치 못한 에러: %s", str(e))
            pass

        return max(0, score)

    def _evaluate_beauty(self, func: Callable) -> float:
        """美: 코드 품질 평가"""
        score = 100.0

        try:
            source = inspect.getsource(func)

            # 타입 힌트 사용도 평가
            has_type_hints = "->" in source or ": " in source
            if not has_type_hints:
                score -= 20

            # 독스트링 존재 여부
            has_docstring = '"""' in source or "'''" in source
            if not has_docstring:
                score -= 10

        except (OSError, AttributeError) as e:
            logger.debug("코드 품질 평가 실패: %s", str(e))
            score -= 15  # 소스 분석 실패 시 감점
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("코드 품질 평가 중 예상치 못한 에러: %s", str(e))
            score -= 15  # 소스 분석 실패 시 감점

        return max(0, score)

    def _evaluate_serenity(self, pre: dict[str, Any], post: dict[str, Any]) -> float:
        """孝: 안정성과 일관성 평가"""
        score = 100.0

        # 검증 성공률
        if not pre.get("signature_valid", True):
            score -= 25

        if not post.get("return_type_valid", True):
            score -= 20

        return max(0, score)

    def _evaluate_eternity(self, func: Callable) -> float:
        """永: 유지보수성과 확장성 평가"""
        score = 100.0

        try:
            # 함수 메트릭 분석
            sig = inspect.signature(func)
            param_count = len(sig.parameters)

            if param_count > 10:
                score -= 20  # 너무 많은 파라미터
            elif param_count > 5:
                score -= 10  # 파라미터가 많은 편

            # 함수 길이 평가
            source = inspect.getsource(func)
            lines_of_code = len(source.split("\n"))
            if lines_of_code > 100:
                score -= 15  # 너무 긴 함수

        except (OSError, AttributeError) as e:
            logger.debug("유지보수성 평가 실패: %s", str(e))
            score -= 10
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("유지보수성 평가 중 예상치 못한 에러: %s", str(e))
            score -= 10

        return max(0, score)

    def _generate_recommendations(
        self,
        trinity_score: float,
        pre_validation: dict[str, Any],
        post_validation: dict[str, Any],
    ) -> list[str]:
        """개선 권장사항 생성"""
        recommendations = []

        if trinity_score < 70:
            recommendations.append("Trinity Score 향상이 필요합니다")

        if "param_types" in pre_validation:
            for param_name, type_info in pre_validation["param_types"].items():
                if type_info["match_score"] < 0.8:
                    recommendations.append(
                        f"'{param_name}' 파라미터 타입 힌트 개선 고려 ({type_info['expected']} ↔ {type_info['actual']})"
                    )

        if post_validation.get("return_match_score", 1.0) < 0.8:
            recommendations.append("리턴 타입 힌트 정확성 검토 필요")

        return recommendations

    def _generate_error_recommendations(self, error: Exception, trinity_score: float) -> list[str]:
        """에러 상황 개선 권장사항"""
        recommendations = []

        if isinstance(error, TypeError):
            recommendations.append("타입 힌트 추가 또는 수정 고려")
        elif isinstance(error, AttributeError):
            recommendations.append("객체 속성 접근 검증 강화")
        elif isinstance(error, ValueError):
            recommendations.append("입력 값 검증 로직 추가")

        if trinity_score < 30:
            recommendations.append("함수 로직 전반적 검토 필요")

        return recommendations

    def _handle_error_validation(self, func: Callable, error: Exception) -> dict[str, Any]:
        """에러 상황에서의 검증 정보 생성"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "validation_possible": False,
        }

    def _update_performance_stats(
        self, func_name: str, execution_time: float, trinity_score: float
    ) -> None:
        """성능 통계 업데이트"""
        if func_name not in self.performance_stats:
            self.performance_stats[func_name] = {
                "call_count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "avg_trinity_score": 0.0,
                "last_updated": time.time(),
            }

        stats = self.performance_stats[func_name]
        stats["call_count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["call_count"]
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)

        # 이동 평균으로 Trinity Score 업데이트
        alpha = 0.1  # 학습률
        stats["avg_trinity_score"] = (
            stats["avg_trinity_score"] * (1 - alpha) + trinity_score * alpha
        )

        stats["last_updated"] = time.time()

    def get_performance_report(self, func_name: str | None = None) -> dict[str, Any]:
        """성능 보고서 생성"""
        if func_name:
            return self.performance_stats.get(func_name, {})

        return {
            "functions": list(self.performance_stats.keys()),
            "summary": {
                "total_functions": len(self.performance_stats),
                "total_calls": sum(
                    stats["call_count"] for stats in self.performance_stats.values()
                ),
                "avg_trinity_score": (
                    sum(stats["avg_trinity_score"] for stats in self.performance_stats.values())
                    / len(self.performance_stats)
                    if self.performance_stats
                    else 0
                ),
            },
            "details": self.performance_stats,
        }


# 글로벌 인스턴스
trinity_validator = TrinityTypeValidator()


def validate_with_trinity[TF: Callable[..., Any]](func: TF) -> TF:
    """Trinity 검증 데코레이터 (async 함수 지원)

    Usage:
        @validate_with_trinity
        def my_function(x: int) -> str:
            return str(x)

        @validate_with_trinity
        async def my_async_function(x: int) -> str:
            return str(x)
    """
    if inspect.iscoroutinefunction(func):
        # Async 함수는 검증을 건너뛰고 직접 반환 (성능 최적화)
        # 필요시 별도의 async 검증 로직 추가 가능
        return func
    else:
        return trinity_validator(func)


# 예시 함수들 (테스트용)
@validate_with_trinity
def example_function(x: int, y: str = "default") -> str:
    """Trinity 검증 예시 함수"""
    return f"{x}: {y}"


@validate_with_trinity
def risky_function(value: Any) -> int:
    """위험한 함수 예시"""
    if not isinstance(value, (int, str)):
        raise TypeError("Invalid type")
    return len(str(value))


if __name__ == "__main__":
    # 테스트 실행
    print("🔍 Trinity Type Validator 테스트")

    # 정상 케이스
    result1 = trinity_validator.validate_function(example_function, 42, "test")
    print(f"✅ 정상 케이스: Trinity Score {result1['trinity_score']:.1f}")

    # 에러 케이스
    try:
        result2 = trinity_validator.validate_function(risky_function, [1, 2, 3])  # 잘못된 타입
    except Exception:
        result2 = trinity_validator.validate_function(risky_function, "valid_string")
        print(f"✅ 에러 복구 케이스: Trinity Score {result2['trinity_score']:.1f}")

    # 성능 보고서
    report = trinity_validator.get_performance_report()
    print(f"📊 모니터링된 함수: {report['summary']['total_functions']}개")
    print(f"📈 평균 Trinity Score: {report['summary']['avg_trinity_score']:.1f}")
