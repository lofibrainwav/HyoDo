#!/usr/bin/env python3
"""
보고 에이전트 SSOT 규칙 검증 스크립트
완료 선언 금지 표현이 사용되지 않았는지 확인
"""

import re
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

# 금지 표현 패턴 (실제 실행 코드에서만 검사)
FORBIDDEN_PATTERNS = [
    r"\bresolved\b",  # 영어 완료 선언
    r"\bcompleted\b",
    r"\bimplemented\b",
    r"\bI have successfully\b",
    r"\bSystem Optimization Complete\b",
    r"\bKey Achievements\b",
    r"\.generate_completion_report\(",  # 완료 보고 메서드 호출
]

# 허용 표현 (컨텍스트에 따라)
ALLOWED_IN_CONTEXT = [
    r"분석 완료",  # "완료"가 포함되어도 "분석 완료"는 허용
    r"검토 완료",
    r"완료 선언 금지",  # 규칙 설명은 허용
    r"완료 기준",  # Definition of Done은 허용
]


def check_forbidden_expressions(file_path: Path) -> list[tuple[int, str]]:
    """파일에서 금지 표현 검색"""
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        in_docstring = False
        for line_num, line in enumerate(lines, 1):
            # docstring 시작/종료 감지
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                continue

            # 주석/문서 문자열은 제외 (설명 목적)
            stripped = line.strip()
            if in_docstring or stripped.startswith(("#", '"""', "'''")):
                continue

            # 허용 컨텍스트 체크
            is_allowed = any(
                re.search(pattern, line, re.IGNORECASE) for pattern in ALLOWED_IN_CONTEXT
            )
            if is_allowed:
                continue

            # 금지 표현 체크 (주석 제외)
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append((line_num, line.strip()))
                    break  # 한 줄에 여러 금지 표현이 있어도 한 번만 기록

    except Exception as e:
        print(f"   ❌ 파일 읽기 실패: {e}")
        return violations

    return violations


def verify_reporting_agent_ssot() -> None:
    """보고 에이전트 SSOT 규칙 검증"""
    print("🔍 [보고 에이전트 SSOT 규칙 검증]")
    print("=" * 60)

    # 검증 대상 파일
    target_files = [
        project_root / "packages" / "afo-core" / "services" / "antigravity_engine.py",
    ]

    all_violations = []

    for file_path in target_files:
        if not file_path.exists():
            print(f"\n⚠️  파일 없음: {file_path}")
            continue

        print(f"\n📄 검증 중: {file_path.name}")
        violations = check_forbidden_expressions(file_path)

        if violations:
            print(f"   ❌ {len(violations)}개 금지 표현 발견:")
            for line_num, line in violations[:5]:  # 최대 5개만 표시
                print(f"      Line {line_num}: {line[:80]}...")
            all_violations.extend([(file_path, line_num, line) for line_num, line in violations])
        else:
            print("   ✅ 금지 표현 없음")

    # AGENTS.md 규칙 확인
    agents_md_path = project_root / "AGENTS.md"
    if agents_md_path.exists():
        print("\n📄 AGENTS.md 규칙 확인:")
        content = agents_md_path.read_text(encoding="utf-8")

        has_separation = "보고 에이전트와 서비스 LLM 경로 분리" in content
        has_forbidden = "완료 선언 금지" in content
        has_conditions = "완료 선언 조건" in content

        print(f"   {'✅' if has_separation else '❌'} 경로 분리 선언")
        print(f"   {'✅' if has_forbidden else '❌'} 완료 선언 금지 규칙")
        print(f"   {'✅' if has_conditions else '❌'} 완료 선언 조건")

        if not (has_separation and has_forbidden and has_conditions):
            print("   ⚠️  AGENTS.md에 SSOT 규칙이 완전하지 않습니다!")
            return False

    print("\n" + "=" * 60)
    if all_violations:
        print(f"❌ {len(all_violations)}개 SSOT 위반 발견!")
        print("=" * 60)
        return False
    print("✅ 모든 보고 에이전트 SSOT 규칙 검증 통과!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = verify_reporting_agent_ssot()
    sys.exit(0 if success else 1)
