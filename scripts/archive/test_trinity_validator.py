#!/usr/bin/env python3
"""
Trinity Type Validator 테스트
AFO Kingdom 방식으로 단계적 실행
"""

import os
import pathlib
import sys

# 경로 추가
sys.path.insert(0, os.path.join(pathlib.Path(__file__).parent, "..", "packages", "afo-core"))


def test_trinity_validator() -> None:
    """
    Trinity 검증 데코레이터 테스트
    """
    print("🔍 Trinity Type Validator 테스트")
    print("=" * 50)

    try:
        from AFO.utils.trinity_type_validator import validate_with_trinity

        print("✅ Trinity Validator 임포트 성공")

        # 테스트 함수들
        @validate_with_trinity
        def safe_function(x: int, y: str = "default") -> str:
            """안전한 함수"""
            return f"{x}: {y}"

        @validate_with_trinity
        def risky_function(value) -> int:
            """위험한 함수 - 타입 힌트 없음"""
            if not isinstance(value, (int, str)):
                msg = "Invalid type"
                raise TypeError(msg)
            return len(str(value))

        print("\n🧪 함수 실행 테스트:")

        # 안전한 함수 테스트
        print("\n1. 안전한 함수 테스트:")
        try:
            result1 = safe_function(42, "test")
            print(f"   ✅ 결과: {result1}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")

        # 위험한 함수 테스트
        print("\n2. 위험한 함수 테스트 (정상 케이스):")
        try:
            result2 = risky_function("hello")
            print(f"   ✅ 결과: {result2}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")

        print("\n3. 위험한 함수 테스트 (에러 케이스):")
        try:
            result3 = risky_function([1, 2, 3])  # 잘못된 타입
            print(f"   ✅ 결과: {result3}")
        except Exception as e:
            print(f"   ⚠️  예상된 오류: {e}")

        print("\n📊 성능 리포트:")
        from AFO.utils.trinity_type_validator import trinity_validator

        report = trinity_validator.get_performance_report()
        print(f"   모니터링된 함수: {report['summary']['total_functions']}개")
        print(".1f")
        print("\n✅ Trinity Validator 테스트 완료!")

    except ImportError as e:
        print(f"❌ 임포트 실패: {e}")
        print("💡 AFO Kingdom 패키지가 설치되어 있는지 확인해주세요")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_trinity_validator()
