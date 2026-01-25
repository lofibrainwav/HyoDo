# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""사용자 시스템 DB 마이그레이션 실행 스크립트
Phase 5: DB 스키마 설정 및 사용자 시스템 초기화
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from AFO.services.database_migrations import run_user_system_migration


async def main():
    """메인 마이그레이션 실행 함수"""
    print("🚀 AFO Kingdom - Phase 5: 사용자 시스템 DB 마이그레이션 시작")
    print("=" * 60)

    try:
        result = await run_user_system_migration()

        if result["status"] == "success":
            print("✅ 마이그레이션 성공!")
            print(f"📋 생성된 테이블: {', '.join(result['tables_created'])}")
            print(f"⚙️  생성된 함수: {', '.join(result['functions_created'])}")
            print("\n🎯 다음 단계:")
            print("1. 사용자 생성 테스트: python scripts/test_user_creation.py")
            print("2. 인증 시스템 테스트: python scripts/test_auth_system.py")
            print("3. Phase 6 Antigravity 자동화 구현 시작")
        else:
            print("❌ 마이그레이션 실패!")
            print(f"오류: {result['message']}")
            if "error" in result:
                print(f"상세 오류: {result['error']}")
            return 1

    except Exception as e:
        print(f"💥 예기치 않은 오류: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n🏰 AFO Kingdom - Phase 5 완료!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
