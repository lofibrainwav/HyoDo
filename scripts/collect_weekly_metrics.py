#!/usr/bin/env python3
"""
AFO Kingdom Weekly Metrics Collector

영어 비율, SSOT 위반, Chaos 테스트 메트릭을 주간 단위로 수집하여 저장합니다.
Context7과 통합하여 기존 메트릭 시스템과 연결합니다.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_current_week_info() -> dict[str, str]:
    """현재 주 정보 반환"""
    today = datetime.now()
    # ISO 주 번호 계산 (월요일 시작)
    year, week_num, _ = today.isocalendar()

    # 주 시작일과 종료일 계산 (월요일 ~ 일요일)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return {
        "week": f"{year:04d}-W{week_num:02d}",
        "start": monday.strftime("%Y-%m-%d"),
        "end": sunday.strftime("%Y-%m-%d"),
        "year": str(year),
        "week_num": f"{week_num:02d}",
    }


def collect_english_ratio_metrics() -> dict[str, Any]:
    """영어 비율 메트릭 수집"""
    # CI 로그에서 영어 비율 경고 수집
    english_warnings = []

    # GitHub Actions 로그 디렉토리에서 검색
    logs_dir = project_root / ".github" / "workflows" / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            with Path(log_file).open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "English-heavy report detected" in content:
                    english_warnings.append(log_file.name)

    return {
        "total_warnings": len(english_warnings),
        "warning_files": english_warnings[:10],  # 최근 10개만
        "trend": "monitoring",  # 추세 분석은 다음 버전에서
    }


def collect_ssot_violation_metrics() -> dict[str, Any]:
    """SSOT 위반 메트릭 수집"""
    violations = []

    # CI 로그에서 SSOT 위반 수집
    logs_dir = project_root / ".github" / "workflows" / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            with Path(log_file).open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "SSOT violation detected" in content or "Report gate failed" in content:
                    violations.append(log_file.name)

    return {
        "total_violations": len(violations),
        "violation_files": violations[:10],  # 최근 10개만
        "compliance_rate": max(
            0, 1 - (len(violations) / max(1, len(list(logs_dir.glob("*.log")))))
        ),
        "trend": "monitoring",
    }


def collect_chaos_test_metrics() -> dict[str, Any]:
    """Chaos 테스트 메트릭 수집"""
    chaos_results = []

    # Nightly Chaos Lite 워크플로우 결과 수집
    workflow_dir = project_root / ".github" / "workflows"
    chaos_log_pattern = "nightly-chaos-lite-*"

    for log_file in workflow_dir.glob(f"{chaos_log_pattern}.log"):
        with Path(log_file).open(encoding="utf-8", errors="ignore") as f:
            content = f.read()
            success = (
                "Chaos #1 - kill one pod (expect self-heal)" in content and "SUCCESS" in content
            )
            chaos_results.append(
                {
                    "date": log_file.stat().st_mtime,
                    "success": success,
                    "log_file": log_file.name,
                }
            )

    success_count = sum(1 for r in chaos_results if r["success"])
    total_count = len(chaos_results)

    return {
        "total_runs": total_count,
        "success_count": success_count,
        "success_rate": success_count / max(1, total_count),
        "recent_results": chaos_results[-7:],  # 최근 7일
        "trend": "stable" if success_count >= total_count * 0.8 else "needs_attention",
    }


def generate_weekly_report(week_info: dict[str, str], metrics: dict[str, Any]) -> str:
    """주간 보고서 생성 (Markdown)"""
    return f"""# AFO Kingdom Weekly Metrics Report - {week_info["week"]}

**기간**: {week_info["start"]} ~ {week_info["end"]}

## 📊 메트릭 요약

### 영어 비율 경고
- **총 경고 수**: {metrics["english_ratio"]["total_warnings"]}
- **추세**: {metrics["english_ratio"]["trend"]}

### SSOT 준수율
- **위반 건수**: {metrics["ssot_violations"]["total_violations"]}
- **준수율**: {metrics["ssot_violations"]["compliance_rate"]:.1%}
- **추세**: {metrics["ssot_violations"]["trend"]}

### Chaos 테스트 안정성
- **총 실행 횟수**: {metrics["chaos_tests"]["total_runs"]}
- **성공률**: {metrics["chaos_tests"]["success_rate"]:.1%}
- **추세**: {metrics["chaos_tests"]["trend"]}

## 📈 상세 분석

### 영어 비율 경고 내역
{chr(10).join(f"- {f}" for f in metrics["english_ratio"]["warning_files"]) if metrics["english_ratio"]["warning_files"] else "- 경고 없음"}

### SSOT 위반 내역
{chr(10).join(f"- {f}" for f in metrics["ssot_violations"]["violation_files"]) if metrics["ssot_violations"]["violation_files"] else "- 위반 없음"}

### Chaos 테스트 결과
{chr(10).join(f"- {r['log_file']}: {'✅' if r['success'] else '❌'}" for r in metrics["chaos_tests"]["recent_results"]) if metrics["chaos_tests"]["recent_results"] else "- 테스트 기록 없음"}

---

*자동 생성된 보고서 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""


def save_metrics(week_info: dict[str, str], metrics: dict[str, Any]) -> None:
    """메트릭을 JSON과 Markdown으로 저장"""
    metrics_dir = project_root / "docs" / "reports" / "_metrics"

    # JSON 저장
    json_data = {
        "week": week_info["week"],
        "period": {"start": week_info["start"], "end": week_info["end"]},
        "metrics": metrics,
        "generated_at": datetime.now().isoformat(),
    }

    json_file = metrics_dir / f"weekly_metrics_{week_info['week']}.json"
    with Path(json_file).open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # Markdown 보고서 저장
    md_report = generate_weekly_report(week_info, metrics)
    md_file = metrics_dir / f"weekly_report_{week_info['week']}.md"
    with Path(md_file).open("w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"✅ 메트릭 저장 완료: {json_file}")
    print(f"✅ 보고서 생성 완료: {md_file}")


def main() -> None:
    """메인 실행 함수"""
    print("🚀 AFO Kingdom Weekly Metrics Collector 시작")

    try:
        # 주 정보 수집
        week_info = get_current_week_info()
        print(f"📅 대상 주: {week_info['week']} ({week_info['start']} ~ {week_info['end']})")

        # 메트릭 수집
        metrics = {
            "english_ratio": collect_english_ratio_metrics(),
            "ssot_violations": collect_ssot_violation_metrics(),
            "chaos_tests": collect_chaos_test_metrics(),
        }

        print("📊 메트릭 수집 완료")
        print(f"  - 영어 경고: {metrics['english_ratio']['total_warnings']}건")
        print(f"  - SSOT 위반: {metrics['ssot_violations']['total_violations']}건")
        print(f"  - Chaos 성공률: {metrics['chaos_tests']['success_rate']:.1%}")

        # 저장
        save_metrics(week_info, metrics)

        print("✅ 주간 메트릭 수집 및 저장 완료")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
