#!/usr/bin/env python3
"""
SSOT Sync - 왕국 문서 자동 동기화 (永 Pillar)

이 스크립트는 주요 메트릭을 자동으로 수집하고 문서에 반영합니다:
- Phase 상태
- 테스트 결과
- 스킬 수
- CVE 취약점 수
- 버전 정보

Usage:
    python scripts/ssot_sync.py          # 드라이런 (변경 미적용)
    python scripts/ssot_sync.py --apply  # 실제 적용
    python scripts/ssot_sync.py --check  # 드리프트만 체크
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
PACKAGES = ROOT / "packages"


def get_test_count() -> tuple[int, int]:
    """pytest 결과에서 테스트 수 추출."""
    report_path = ROOT / "artifacts/ci/pytest_report.txt"
    if report_path.exists():
        content = report_path.read_text()
        # "1220 passed, 82 skipped" 패턴 찾기
        match = re.search(r"(\d+)\s+passed.*?(\d+)\s+skipped", content)
        if match:
            return int(match.group(1)), int(match.group(2))
    return 0, 0


def get_skill_count() -> int:
    """스킬 파일 수 카운트."""
    skills_dir = ROOT / ".claude/commands"
    if skills_dir.exists():
        return len(list(skills_dir.glob("*.md")))
    return 0


def get_phase() -> str:
    """현재 Phase 추출 (Evolution Log 및 Phase 파일 기반)."""
    phases = []

    # 1. Evolution Log에서 최신 Phase 추출
    evolution_log = ROOT / "docs/AFO_EVOLUTION_LOG.md"
    if evolution_log.exists():
        content = evolution_log.read_text()
        # "Phase 23", "Phase 24", "Phase 25" 패턴 찾기
        matches = re.findall(r"Phase\s+(\d+)", content)
        phases.extend(int(m) for m in matches)

    # 2. PHASE*_COMPLETION_REPORT.md 파일에서 Phase 추출
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        for f in docs_dir.glob("PHASE*_*.md"):
            match = re.search(r"PHASE[_]?(\d+)", f.name, re.IGNORECASE)
            if match:
                phases.append(int(match.group(1)))

    if phases:
        return f"{max(phases)}+"
    return "unknown"


def get_cve_count() -> int:
    """CVE 취약점 수 (pip-audit 기반, 실패 시 캐시 확인)."""
    import json
    import os

    # 1. 최근 보안 스캔 캐시 확인
    cache_file = ROOT / "artifacts/ci/security_scan.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            if "cve_count" in data:
                return data["cve_count"]
        except Exception:
            pass

    # 2. pip-audit 직접 실행 시도
    try:
        env = os.environ.copy()
        env["PIPAPI_PYTHON_LOCATION"] = str(ROOT / ".venv/bin/python")
        result = subprocess.run(
            ["uv", "run", "pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=PACKAGES / "afo-core",
            env=env,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            vulns = [d for d in data.get("dependencies", []) if d.get("vulns")]
            return len(vulns)
    except Exception:
        pass

    # 3. .cursorrules에서 마지막 알려진 값 추출
    cursorrules = ROOT / ".cursorrules"
    if cursorrules.exists():
        content = cursorrules.read_text()
        match = re.search(r"\*\*보안 취약점\*\*:\s*(\d+)개\s*CVE", content)
        if match:
            return int(match.group(1))

    return 0  # 기본값 0 (알 수 없음 대신)


def get_current_date() -> str:
    """현재 날짜."""
    return datetime.now().strftime("%Y-%m-%d")


def collect_metrics() -> dict:
    """모든 메트릭 수집."""
    passed, skipped = get_test_count()
    return {
        "date": get_current_date(),
        "phase": get_phase(),
        "tests_passed": passed,
        "tests_skipped": skipped,
        "skills": get_skill_count(),
        "cves": get_cve_count(),
    }


def update_cursorrules(metrics: dict, dry_run: bool = True) -> list[str]:
    """root .cursorrules 업데이트."""
    changes = []
    file_path = ROOT / ".cursorrules"
    if not file_path.exists():
        return changes

    content = file_path.read_text()
    original = content

    # 날짜 업데이트
    content = re.sub(
        r"### 현재 상태 \(\d{4}-\d{2}-\d{2}\)",
        f"### 현재 상태 ({metrics['date']})",
        content,
    )

    # Phase 업데이트
    content = re.sub(
        r"\*\*Phase\*\*: .+",
        f"**Phase**: {metrics['phase']} 진행 중",
        content,
    )

    # 테스트 수 업데이트
    content = re.sub(
        r"\*\*테스트\*\*: \d+ passed, \d+ skipped",
        f"**테스트**: {metrics['tests_passed']} passed, {metrics['tests_skipped']} skipped",
        content,
    )

    # Skills 수 업데이트
    content = re.sub(
        r"\*\*Skills\*\*: \d+개",
        f"**Skills**: {metrics['skills']}개",
        content,
    )

    # CVE 업데이트
    if metrics["cves"] >= 0:
        content = re.sub(
            r"\*\*보안 취약점\*\*: \d+개 CVE",
            f"**보안 취약점**: {metrics['cves']}개 CVE",
            content,
        )

    if content != original:
        changes.append(f".cursorrules: 상태 업데이트 ({metrics['date']})")
        if not dry_run:
            file_path.write_text(content)

    return changes


def update_claude_md(_metrics: dict, _dry_run: bool = True) -> list[str]:
    """CLAUDE.md 스킬 수 업데이트 (필요시)."""
    changes: list[str] = []
    # CLAUDE.md는 스킬 목록이 있으므로 수동 관리 권장
    # TODO: 향후 스킬 테이블 자동 생성 기능 추가 가능
    return changes


def check_drift(metrics: dict) -> list[str]:
    """SSOT 드리프트 체크."""
    drifts = []

    # .cursorrules 체크
    cursorrules = ROOT / ".cursorrules"
    if cursorrules.exists():
        content = cursorrules.read_text()

        # 테스트 수 드리프트
        match = re.search(r"\*\*테스트\*\*: (\d+) passed", content)
        if match:
            doc_tests = int(match.group(1))
            if abs(doc_tests - metrics["tests_passed"]) > 50:  # 50개 이상 차이
                drifts.append(
                    f"테스트 수 드리프트: 문서({doc_tests}) vs 실제({metrics['tests_passed']})"
                )

        # 스킬 수 드리프트
        match = re.search(r"\*\*Skills\*\*: (\d+)개", content)
        if match:
            doc_skills = int(match.group(1))
            if doc_skills != metrics["skills"]:
                drifts.append(f"스킬 수 드리프트: 문서({doc_skills}) vs 실제({metrics['skills']})")

    return drifts


def main() -> None:
    parser = argparse.ArgumentParser(description="SSOT 자동 동기화")
    parser.add_argument("--apply", action="store_true", help="변경 적용")
    parser.add_argument("--check", action="store_true", help="드리프트만 체크")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    # 메트릭 수집
    metrics = collect_metrics()

    if args.json:
        import json

        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        return 0

    print("📊 SSOT 메트릭 수집 완료:")
    print(f"   날짜: {metrics['date']}")
    print(f"   Phase: {metrics['phase']}")
    print(f"   테스트: {metrics['tests_passed']} passed, {metrics['tests_skipped']} skipped")
    print(f"   스킬: {metrics['skills']}개")
    print(f"   CVE: {metrics['cves']}개")
    print()

    if args.check:
        drifts = check_drift(metrics)
        if drifts:
            print("⚠️  SSOT 드리프트 감지:")
            for drift in drifts:
                print(f"   - {drift}")
            return 1
        print("✅ SSOT 동기화 상태 양호")
        return 0

    # 업데이트
    dry_run = not args.apply
    all_changes = []

    changes = update_cursorrules(metrics, dry_run)
    all_changes.extend(changes)

    changes = update_claude_md(metrics, dry_run)
    all_changes.extend(changes)

    if all_changes:
        mode = "DRY_RUN" if dry_run else "APPLIED"
        print(f"📝 변경 사항 ({mode}):")
        for change in all_changes:
            print(f"   - {change}")
        if dry_run:
            print()
            print("💡 실제 적용하려면: python scripts/ssot_sync.py --apply")
    else:
        print("✅ 변경 사항 없음 - SSOT 동기화 상태 양호")

    return 0


if __name__ == "__main__":
    sys.exit(main())
