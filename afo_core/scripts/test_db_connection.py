# Trinity Score: 90.0 (Established by Chancellor)
"""
PostgreSQL 연결 테스트 스크립트
Phase 1: PostgreSQL 연결 문제 해결 검증
Copyright (c) 2025 AFO Kingdom. All rights reserved.
"""

import asyncio
import sys
from pathlib import Path

# AFO 패키지 경로 추가
_CORE_ROOT = Path(__file__).resolve().parent.parent
if str(_CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CORE_ROOT))

from AFO.config.settings import get_settings
from AFO.services.database import get_db_connection


async def test_connection():
    """PostgreSQL 연결 테스트"""
    print("🔍 PostgreSQL 연결 테스트 시작...\n")

    # 설정 확인
    settings = get_settings()
    params = settings.get_postgres_connection_params()

    print("📊 연결 설정:")
    for key, value in params.items():
        if key == "password":
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    print()

    # 연결 테스트
    try:
        print("🔌 연결 시도 중...")
        conn = await get_db_connection()

        # 간단한 쿼리 실행
        result = await conn.fetchval("SELECT version();")
        print("✅ 연결 성공!")
        print(f"📋 PostgreSQL 버전: {result}\n")

        # 테이블 확인
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        )

        if tables:
            print("📊 생성된 테이블:")
            for table in tables:
                print(f"  ✅ {table['table_name']}")
        else:
            print("⚠️  테이블이 없습니다. 스키마를 생성하세요.")

        await conn.close()
        print("\n✅ 연결 테스트 완료!")
        return True

    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
