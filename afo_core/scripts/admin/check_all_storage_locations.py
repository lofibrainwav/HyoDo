# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""모든 저장소 위치에서 키 확인"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    print("=== 모든 저장소 위치에서 키 확인 ===\n")

    # 1. JSON 저장소
    print("1️⃣ JSON 저장소:")
    try:
        from api_wallet import APIWallet

        wallet_json = APIWallet()
        keys_json = wallet_json.list_keys()
        print(f"   총 {len(keys_json)}개 키")
        if keys_json:
            for k in keys_json:
                print(f"   • {k['name']} (service: {k.get('service', '없음')})")
        else:
            print("   (저장된 키 없음)")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    print()

    # 2. PostgreSQL DB
    print("2️⃣ PostgreSQL DB:")
    try:
        import psycopg2

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
        wallet_pg = APIWallet(db_connection=conn)
        keys_pg = wallet_pg.list_keys()
        print(f"   총 {len(keys_pg)}개 키")
        if keys_pg:
            for k in keys_pg:
                print(f"   • {k['name']} (service: {k.get('service', '없음')})")
                # OpenAI 키 확인
                if (
                    "openai" in k.get("service", "").lower()
                    or "openai" in k.get("name", "").lower()
                ):
                    key = wallet_pg.get(k["name"])
                    if key:
                        print(f"     ✅ 키 확인: {len(key)} 문자")
        else:
            print("   (저장된 키 없음)")
        conn.close()
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    print()

    # 3. 환경 변수
    import os

    print("3️⃣ 환경 변수:")
    openai_env = os.getenv("OPENAI_API_KEY")
    if openai_env:
        print(f"   ✅ OPENAI_API_KEY: {len(openai_env)} 문자")
    else:
        print("   (설정되지 않음)")

    print()
    print("=== 확인 완료 ===")


if __name__ == "__main__":
    main()
