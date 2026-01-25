# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""API Wallet PostgreSQL DB 지피지기 (정확한 상태 파악)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    print("=== API Wallet 시스템 지피지기 (知彼知己) ===\n")

    # 1. PostgreSQL 연결 확인
    print("1️⃣ PostgreSQL 연결 확인:")
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # 실제 PostgreSQL 설정 확인
        from AFO.config.settings import get_settings

        settings = get_settings()
        conn = psycopg2.connect(
            # 중앙 설정 사용 (Phase 1 리팩토링)
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )
        print("   ✅ PostgreSQL 연결 성공")

        # 테이블 확인
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'api_keys';
            """
            )
            if cur.fetchone():
                print("   ✅ api_keys 테이블 존재")
            else:
                print("   ❌ api_keys 테이블 없음")
                conn.close()
                return

        # 키 개수 확인
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM api_keys;")
            total = cur.fetchone()[0]
            print(f"   📊 총 {total}개 키 저장됨")

        if total == 0:
            print("\n   ⚠️  저장된 키 없음")
            conn.close()
            return

        # 모든 키 목록
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, service, key_type, created_at, access_count
                FROM api_keys
                ORDER BY created_at DESC;
            """
            )
            keys = cur.fetchall()

            print(f"\n2️⃣ 저장된 키 목록 ({len(keys)}개):")
            for i, k in enumerate(keys, 1):
                print(f"\n   {i}. {k['name']}")
                print(f"      서비스: {k.get('service', '없음')}")
                print(f"      타입: {k.get('key_type', '없음')}")
                print(f"      생성일: {k.get('created_at', '없음')}")
                print(f"      접근 횟수: {k.get('access_count', 0)}")

        # OpenAI 키 검색
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, service
                FROM api_keys
                WHERE service ILIKE '%openai%'
                   OR service ILIKE '%gpt%'
                   OR name ILIKE '%openai%'
                   OR name ILIKE '%gpt%';
            """
            )
            openai_keys = cur.fetchall()

            print("\n3️⃣ OpenAI 관련 키 검색:")
            if openai_keys:
                print(f"   ✅ {len(openai_keys)}개 발견")
                for k in openai_keys:
                    print(f"      • {k['name']} (service: {k.get('service', '없음')})")

                # API Wallet으로 키 가져오기 테스트
                print("\n4️⃣ API Wallet으로 키 가져오기 테스트:")
                from api_wallet import APIWallet

                wallet = APIWallet(db_connection=conn)

                for k in openai_keys:
                    key = wallet.get(k["name"])
                    if key:
                        print(f"   ✅ {k['name']}: {len(key)} 문자")
                        print(f"      앞 10자: {key[:10]}...")
                        break
            else:
                print("   ❌ OpenAI 관련 키 없음")

        conn.close()

    except ImportError:
        print("   ❌ psycopg2 모듈 없음")
        print("   💡 설치: pip install psycopg2-binary")
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")

    print("\n=== 지피지기 완료 ===")


if __name__ == "__main__":
    main()
