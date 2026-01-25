#!/usr/bin/env python3
"""
언어 정책 검증 스크립트
SSOT 언어 정책이 모든 LLM 호출에 적용되는지 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))


def verify_language_policy() -> None:
    """언어 정책 검증"""
    print("🔍 [SSOT 언어 정책 검증]")
    print("=" * 60)

    # 1. antigravity 설정 확인
    try:
        from AFO.config.antigravity import antigravity

        report_language = getattr(antigravity, "REPORT_LANGUAGE", None)
        use_protocol_officer = getattr(antigravity, "USE_PROTOCOL_OFFICER", None)

        print("\n1. Antigravity 설정:")
        print(f"   ✅ REPORT_LANGUAGE: {report_language}")
        print(f"   ✅ USE_PROTOCOL_OFFICER: {use_protocol_officer}")

        if report_language != "ko":
            print("   ⚠️  경고: REPORT_LANGUAGE가 'ko'가 아닙니다!")
            return False

        if not use_protocol_officer:
            print("   ⚠️  경고: USE_PROTOCOL_OFFICER가 False입니다!")
            return False

    except Exception as e:
        print(f"   ❌ Antigravity 설정 확인 실패: {e}")
        return False

    # 2. llm_router.py에서 언어 강제 로직 확인
    try:
        llm_router_path = project_root / "packages" / "afo-core" / "llm_router.py"
        if not llm_router_path.exists():
            print("\n2. llm_router.py 확인:")
            print(f"   ❌ 파일을 찾을 수 없습니다: {llm_router_path}")
            return False

        content = llm_router_path.read_text(encoding="utf-8")

        # 언어 강제 로직 확인
        has_language_policy = "Output language: Korean" in content
        has_antigravity_import = "from AFO.config.antigravity import antigravity" in content
        has_language_check = "REPORT_LANGUAGE" in content

        print("\n2. llm_router.py 언어 강제 로직:")
        print(f"   {'✅' if has_language_policy else '❌'} 'Output language: Korean' 포함")
        print(f"   {'✅' if has_antigravity_import else '❌'} antigravity import")
        print(f"   {'✅' if has_language_check else '❌'} REPORT_LANGUAGE 체크")

        if not (has_language_policy and has_antigravity_import and has_language_check):
            print("   ⚠️  경고: 언어 강제 로직이 완전하지 않습니다!")
            return False

    except Exception as e:
        print(f"   ❌ llm_router.py 확인 실패: {e}")
        return False

    # 3. Protocol Officer 통합 확인
    try:
        protocol_officer_path = (
            project_root / "packages" / "afo-core" / "services" / "protocol_officer.py"
        )
        if not protocol_officer_path.exists():
            print("\n3. Protocol Officer 확인:")
            print(f"   ❌ 파일을 찾을 수 없습니다: {protocol_officer_path}")
            return False

        content = protocol_officer_path.read_text(encoding="utf-8")

        has_commander_format = "형님! 승상입니다" in content
        has_korean_suffix = "영(永)을 이룹시다" in content

        print("\n3. Protocol Officer 통합:")
        print(f"   {'✅' if has_commander_format else '❌'} Commander 형식 (형님! 승상입니다)")
        print(f"   {'✅' if has_korean_suffix else '❌'} 한국어 suffix (영(永)을 이룹시다)")

        if not (has_commander_format and has_korean_suffix):
            print("   ⚠️  경고: Protocol Officer 한국어 형식이 완전하지 않습니다!")
            return False

    except Exception as e:
        print(f"   ❌ Protocol Officer 확인 실패: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 모든 언어 정책 검증 통과!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = verify_language_policy()
    sys.exit(0 if success else 1)
