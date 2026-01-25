#!/usr/bin/env python3
"""
AFO 왕국 500줄 규칙 모니터링 스크립트
眞善美孝永 - 美(Beauty) 기둥: 코드 단순성 및 구조화 강제

CLAUDE.md 규칙: "Files should stay under 500 lines"
"""

import argparse
import json
import sys
from pathlib import Path

# 제외 패턴 (venv, node_modules, 빌드 산출물, vendored, legacy 등)
EXCLUDE_PATTERNS = [
    ".venv",
    "venv",
    "venv_",
    "node_modules",
    ".git",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".ignored",
    ".pnpm",
    # Vendored/Upstream 외부 코드
    "upstream",
    "vendor",
    "third_party",
    # Legacy/Archived 코드 (별도 관리)
    "legacy",
    "archived",
    # Auto-generated test files (coverage sweep)
    "test_coverage_sweep.py",
    # External git submodules (별도 레포지토리)
    "packages/external",
]

# 심각도 임계값
THRESHOLD_CRITICAL = 1000  # 긴급 리팩토링 필요
THRESHOLD_WARNING = 700  # 주의 필요
THRESHOLD_INFO = 500  # 기본 규칙


def should_exclude(path: Path) -> bool:
    """제외 대상 경로인지 확인"""
    path_str = str(path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)


def count_lines(file_path: Path) -> int:
    """파일 줄 수 계산"""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def scan_files(root: Path, extensions: list[str]) -> list[dict]:
    """파일 스캔 및 줄 수 계산"""
    violations = []

    for ext in extensions:
        for file_path in root.rglob(f"*{ext}"):
            if should_exclude(file_path):
                continue

            lines = count_lines(file_path)
            if lines > THRESHOLD_INFO:
                severity = (
                    "CRITICAL"
                    if lines > THRESHOLD_CRITICAL
                    else "WARNING"
                    if lines > THRESHOLD_WARNING
                    else "INFO"
                )
                violations.append(
                    {
                        "path": str(file_path.relative_to(root)),
                        "lines": lines,
                        "severity": severity,
                        "excess": lines - THRESHOLD_INFO,
                    }
                )

    return sorted(violations, key=lambda x: x["lines"], reverse=True)


def print_report(violations: list[dict], output_format: str = "text") -> None:
    """결과 리포트 출력"""
    if output_format == "json":
        print(json.dumps({"violations": violations, "total": len(violations)}, indent=2))
        return

    # 텍스트 형식 출력
    print("\n" + "=" * 70)
    print("  AFO 왕국 500줄 규칙 검사 리포트 (美 - Beauty)")
    print("=" * 70)

    if not violations:
        print("\n  모든 파일이 500줄 규칙을 준수합니다.")
        print("=" * 70)
        return

    # 심각도별 분류
    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    warning = [v for v in violations if v["severity"] == "WARNING"]
    info = [v for v in violations if v["severity"] == "INFO"]

    print(f"\n  총 위반 파일: {len(violations)}개")
    print(f"    - CRITICAL (>1000줄): {len(critical)}개")
    print(f"    - WARNING  (>700줄):  {len(warning)}개")
    print(f"    - INFO     (>500줄):  {len(info)}개")
    print("-" * 70)

    # CRITICAL 파일
    if critical:
        print("\n  [CRITICAL] 긴급 리팩토링 필요:")
        for v in critical:
            print(f"    {v['lines']:>6}줄 | {v['path']}")

    # WARNING 파일
    if warning:
        print("\n  [WARNING] 주의 필요:")
        for v in warning[:10]:  # 상위 10개만
            print(f"    {v['lines']:>6}줄 | {v['path']}")
        if len(warning) > 10:
            print(f"    ... 외 {len(warning) - 10}개 파일")

    # INFO 파일 (요약만)
    if info:
        print(f"\n  [INFO] 500줄 초과: {len(info)}개 파일")
        for v in info[:5]:
            print(f"    {v['lines']:>6}줄 | {v['path']}")
        if len(info) > 5:
            print(f"    ... 외 {len(info) - 5}개 파일")

    print("\n" + "=" * 70)

    # 권장 액션
    if critical:
        print("\n  [권장 액션]")
        print("  1. CRITICAL 파일부터 모듈 분리 진행")
        print("  2. 클래스/함수 단위로 별도 파일 추출")
        print("  3. 테스트 파일은 테스트 케이스별 분할 고려")
        print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="AFO 500줄 규칙 검사기")
    parser.add_argument("--path", default=".", help="검사할 루트 경로")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="출력 형식")
    parser.add_argument("--extensions", default=".py,.ts,.tsx", help="검사할 확장자 (쉼표 구분)")
    parser.add_argument("--ci", action="store_true", help="CI 모드 (위반 시 exit 1)")

    args = parser.parse_args()

    root = Path(args.path).resolve()
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    violations = scan_files(root, extensions)
    print_report(violations, args.format)

    # CI 모드: CRITICAL 위반 시 실패
    if args.ci:
        critical_count = sum(1 for v in violations if v["severity"] == "CRITICAL")
        if critical_count > 0:
            print(f"\n  CI FAILED: {critical_count}개 CRITICAL 위반")
            sys.exit(1)

    return len(violations)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 0)  # 기본은 성공 (CI 모드만 실패)
