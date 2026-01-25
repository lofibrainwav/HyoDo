#!/usr/bin/env python3
"""
AFO 왕국 자동화 디버깅 시스템 실행 스크립트
CLI 인터페이스

眞善美孝永 철학에 기반한 자동화 디버깅
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

from AFO.services.automated_debugging_system import (
    AutomatedDebuggingSystem,
)  # noqa: E402


async def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 자동화 디버깅 시스템")
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="프로젝트 루트 경로 (기본값: 현재 디렉토리)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="결과를 저장할 JSON 파일 경로",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 형식으로 출력",
    )

    args = parser.parse_args()

    project_root_path = Path(args.project_root) if args.project_root else project_root

    print("=" * 70)
    print("🏰 AFO 왕국 자동화 디버깅 시스템")
    print("=" * 70)
    print(f"\n프로젝트 루트: {project_root_path}")
    print("\n디버깅 시작...\n")

    system = AutomatedDebuggingSystem(project_root_path)
    report = await system.run_full_debugging_cycle()

    # 결과 출력
    if args.json:
        output = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "total_errors": report.total_errors,
            "errors_by_severity": report.errors_by_severity,
            "errors_by_category": report.errors_by_category,
            "auto_fixed": report.auto_fixed,
            "manual_required": report.manual_required,
            "trinity_score": report.trinity_score,
            "recommendations": report.recommendations,
            "execution_time": report.execution_time,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 70)
        print("📊 디버깅 결과 요약")
        print("=" * 70)
        print(f"\n총 에러: {report.total_errors}개")
        print(f"자동 수정: {report.auto_fixed}개")
        print(f"수동 필요: {report.manual_required}개")

        print("\n심각도별 분류:")
        for severity, count in report.errors_by_severity.items():
            print(f"  • {severity}: {count}개")

        print("\n카테고리별 분류:")
        for category, count in report.errors_by_category.items():
            print(f"  • {category}: {count}개")

        print("\n🏆 Trinity Score:")
        trinity = report.trinity_score
        print(f"  • Overall: {trinity:.1f}/100")
        pillars = report.pillar_scores
        print(f"  • Truth: {pillars.get('truth', 0):.1f}/100")
        print(f"  • Goodness: {pillars.get('goodness', 0):.1f}/100")
        print(f"  • Beauty: {pillars.get('beauty', 0):.1f}/100")
        print(f"  • Serenity: {pillars.get('serenity', 0):.1f}/100")
        print(f"  • Eternity: {pillars.get('eternity', 0):.1f}/100")

        if report.recommendations:
            print("\n💡 권장사항:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print(f"\n⏱️  실행 시간: {report.execution_time:.2f}초")

    # 파일 저장
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "total_errors": report.total_errors,
            "errors_by_severity": report.errors_by_severity,
            "errors_by_category": report.errors_by_category,
            "auto_fixed": report.auto_fixed,
            "manual_required": report.manual_required,
            "trinity_score": report.trinity_score,
            "recommendations": report.recommendations,
            "execution_time": report.execution_time,
        }

        with Path(output_path).open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 결과 저장: {output_path}")

    print("\n" + "=" * 70)
    print("✅ 자동화 디버깅 시스템 완료")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
