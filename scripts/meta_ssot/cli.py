#!/usr/bin/env python3
"""
Meta-SSOT CLI - Command-line interface for Meta-SSOT Health Monitor

Usage:
    python -m scripts.meta_ssot.cli
    python scripts/meta_ssot_health.py
"""

import argparse
import json
import sys

from scripts.meta_ssot.config import get_repo_root
from scripts.meta_ssot.metacognitive import (
    check_launchd_runtime,
    cross_validate_data,
    self_heal,
)
from scripts.meta_ssot.notifier import send_discord_alert, should_alert
from scripts.meta_ssot.orchestrator import (
    check_launchd_installation,
    run_health_check,
)
from scripts.meta_ssot.reporter import print_metacognitive_report, print_report


def main() -> int:
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Meta-SSOT Health Monitor v2.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    parser.add_argument("--heal", action="store_true", help="자가 치유 실행 (dry-run 아님)")
    parser.add_argument("--dry-run", action="store_true", help="자가 치유 dry-run 모드")
    parser.add_argument("--json", action="store_true", help="JSON 출력만")
    parser.add_argument("--alert", action="store_true", help="Discord 알림 전송 (문제 발생 시)")
    parser.add_argument("--force-alert", action="store_true", help="Discord 알림 강제 전송")
    args = parser.parse_args()

    repo = get_repo_root()
    results = run_health_check()

    # [v2.0] 메타인지 계층 추가
    results["metacognitive"] = {
        "launchd_runtime": check_launchd_runtime(),
        "cross_validation": cross_validate_data(repo),
    }

    # 자가 치유 모드
    if args.heal or args.dry_run:
        heal_result = self_heal(repo, dry_run=args.dry_run)
        results["metacognitive"]["self_heal"] = heal_result

    # JSON 출력 모드
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        return 0

    # 일반 출력
    print_report(results)

    # launchd 설치 상태
    launchd = check_launchd_installation()
    if launchd["missing_count"] > 0:
        print(
            f"\n⚠️  LAUNCHD: {launchd['missing_count']}/{launchd['total_services']} services not loaded"
        )
        if launchd["recommendation"]:
            print(f"    {launchd['recommendation']}")
        print()

    # [v2.0] 메타인지 계층 출력
    print_metacognitive_report(results, verbose=args.verbose)

    # 로그 파일 저장
    log_dir = repo / "artifacts" / "run"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "meta_ssot_health.out"

    xval = results["metacognitive"]["cross_validation"]
    runtime = results["metacognitive"]["launchd_runtime"]

    with open(log_file, "a") as f:
        xval_status = "OK" if xval["all_valid"] else "FAIL"
        f.write(
            f"{results['timestamp']} | {results['overall_status']} | "
            f"H:{results['meta']['healthy']} W:{results['meta']['warning']} "
            f"S:{results['meta']['stale']} M:{results['meta']['missing']} E:{results['meta']['error']} | "
            f"launchd:{runtime['loaded']}/{runtime['total']} xval:{xval_status}\n"
        )

    # JSON 결과 저장
    json_file = repo / "artifacts" / "meta_ssot" / "health_report.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    # 루트에도 저장 (호환성)
    root_json = repo / "artifacts" / "meta_ssot_health.json"
    with open(root_json, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    # [v2.0] Discord 알림
    if args.force_alert or (args.alert and should_alert(results)):
        sent = send_discord_alert(results)
        if sent:
            print("\n📤 Discord alert sent")
        elif args.verbose:
            print("\n⚠️  Discord alert not configured (set DISCORD_WEBHOOK_URL)")

    # 종료 코드
    if results["overall_status"] in ("ERROR", "INCOMPLETE"):
        return 1
    if results["overall_status"] in ("STALE", "WARNING"):
        return 2
    if not xval["all_valid"]:
        return 3  # 교차 검증 실패
    return 0


if __name__ == "__main__":
    sys.exit(main())
