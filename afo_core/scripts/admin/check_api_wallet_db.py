# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
import os

"""API Wallet PostgreSQL DB 확인 스크립트"""

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("⚠️  psycopg2 모듈 없음 - PostgreSQL 확인 불가")


def check_postgres() -> None:
    """PostgreSQL DB에서 키 확인"""
    if not PSYCOPG2_AVAILABLE:
        return

    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            host="localhost",
            port=15432,
            database="postgres",
            user="postgres",
            password=os.getenv("DB_PASSWORD", "postgres"),  # nosec
        )

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 테이블 존재 확인
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'api_keys';
            """
            )

            if not cur.fetchone():
                print("❌ api_keys 테이블 없음")
                conn.close()
                return

            # 전체 키 수
            cur.execute("SELECT COUNT(*) as count FROM api_keys;")
            total = cur.fetchone()["count"]
            print(f"✅ PostgreSQL DB에 총 {total}개 키 저장됨")
            print()

            if total == 0:
                print("  (저장된 키 없음)")
                conn.close()
                return

            # 모든 키 목록
            cur.execute(
                """
                SELECT name, service, key_type, created_at, access_count
                FROM api_keys
                ORDER BY created_at DESC;
            """
            )

            keys = cur.fetchall()
            print("📋 저장된 키 목록:")
            print()

            for i, k in enumerate(keys, 1):
                print(f"  {i}. {k['name']}")
                print(f"     서비스: {k.get('service', '없음')}")
                print(f"     타입: {k.get('key_type', '없음')}")
                print(f"     생성일: {k.get('created_at', '없음')}")
                print(f"     접근 횟수: {k.get('access_count', 0)}")
                print()

            # OpenAI 키 검색
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
            print("🔍 OpenAI 관련 키:")
            if openai_keys:
                for k in openai_keys:
                    print(f"  ✅ {k['name']} (service: {k.get('service', '없음')})")
            else:
                print("  ❌ OpenAI 관련 키 없음")

        conn.close()

    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        print("💡 환경 변수나 연결 정보 확인 필요")


if __name__ == "__main__":
    print("=== API Wallet PostgreSQL DB 확인 ===\n")
    check_postgres()
