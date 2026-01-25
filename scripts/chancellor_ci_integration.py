#!/usr/bin/env python3
"""
Chancellor Graph CI 연계 스크립트

CI 실패 시 Trinity Score를 업데이트하고,
위험 수준에 따라 ASK 모드 전환을 권장합니다.

眞善美孝永 점수 계산:
- 眞 (Truth): 테스트 통과율
- 善 (Goodness): 보안 스캔 결과
- 美 (Beauty): 린트/포맷 결과
- 孝 (Serenity): 빌드 안정성
- 永 (Eternity): 문서화 상태
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Trinity 가중치 (SSOT)
WEIGHTS = {
    "truth": 0.35,
    "goodness": 0.35,
    "beauty": 0.20,
    "serenity": 0.08,
    "eternity": 0.02,
}


def calculate_trinity_score(ci_results: dict) -> dict:
    """CI 결과로부터 Trinity Score 계산"""

    # 眞 (Truth): 테스트 통과
    truth = 1.0 if ci_results.get("tests_passed") else 0.5

    # 善 (Goodness): 보안 스캔
    security_issues = ci_results.get("security_issues", 0)
    goodness = max(0.0, 1.0 - (security_issues * 0.1))

    # 美 (Beauty): 린트 결과
    lint_errors = ci_results.get("lint_errors", 0)
    beauty = max(0.0, 1.0 - (lint_errors * 0.02))

    # 孝 (Serenity): 빌드 안정성
    build_success = ci_results.get("build_success", False)
    serenity = 1.0 if build_success else 0.3

    # 永 (Eternity): 문서화 (기본값 유지)
    eternity = ci_results.get("doc_coverage", 0.8)

    # 종합 점수
    total = (
        WEIGHTS["truth"] * truth
        + WEIGHTS["goodness"] * goodness
        + WEIGHTS["beauty"] * beauty
        + WEIGHTS["serenity"] * serenity
        + WEIGHTS["eternity"] * eternity
    )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "scores": {
            "truth": round(truth, 2),
            "goodness": round(goodness, 2),
            "beauty": round(beauty, 2),
            "serenity": round(serenity, 2),
            "eternity": round(eternity, 2),
        },
        "total": round(total, 2),
        "weights": WEIGHTS,
    }


def recommend_mode(trinity_score: dict) -> str:
    """Trinity Score에 따른 모드 권장"""
    total = trinity_score["total"]

    if total >= 0.9:
        return "AUTO"  # 자동 실행 가능
    if total >= 0.7:
        return "CONFIRM"  # 확인 후 실행
    return "ASK"  # 사령관 승인 필요


def main() -> None:
    # CI 결과 파싱 (예시)
    ci_results = {
        "tests_passed": "--tests-passed" in sys.argv,
        "security_issues": 0,
        "lint_errors": 0,
        "build_success": "--build-success" in sys.argv,
        "doc_coverage": 0.8,
    }

    # CI 실패 시
    if "--ci-failed" in sys.argv:
        ci_results["tests_passed"] = False
        ci_results["build_success"] = False
        ci_results["security_issues"] = 3

    trinity = calculate_trinity_score(ci_results)
    mode = recommend_mode(trinity)

    print("=" * 50)
    print("📊 Trinity Score 업데이트")
    print("=" * 50)
    print(f"\n眞 (Truth):    {trinity['scores']['truth']}")
    print(f"善 (Goodness): {trinity['scores']['goodness']}")
    print(f"美 (Beauty):   {trinity['scores']['beauty']}")
    print(f"孝 (Serenity): {trinity['scores']['serenity']}")
    print(f"永 (Eternity): {trinity['scores']['eternity']}")
    print(f"\n총점: {trinity['total']}")
    print(f"\n권장 모드: {mode}")

    if mode == "ASK":
        print("\n⚠️  사령관 승인 필요!")
        print("    CI 실패로 인해 Trinity Score가 하락했습니다.")
        print("    다음 작업 전 사령관의 지시를 기다리세요.")

    # 결과 저장
    output_path = Path("trinity_score.json")
    with Path(output_path).open("w", encoding="utf-8") as f:
        json.dump({"trinity": trinity, "mode": mode}, f, indent=2)

    print(f"\n✅ 저장됨: {output_path}")


if __name__ == "__main__":
    main()
