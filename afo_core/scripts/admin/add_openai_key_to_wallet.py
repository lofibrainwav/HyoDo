# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""OpenAI API 키를 API Wallet에 추가하는 스크립트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    print("=== OpenAI API 키를 API Wallet에 추가 ===\n")

    # API 키 입력 받기
    print("OpenAI API 키를 입력하세요:")
    print("(https://platform.openai.com/api-keys 에서 복사)")
    print()
    api_key = input("API Key: ").strip()

    if not api_key:
        print("❌ API 키가 입력되지 않았습니다.")
        return

    if not api_key.startswith("sk-"):
        print("⚠️  OpenAI API 키는 보통 'sk-'로 시작합니다.")
        confirm = input("계속하시겠습니까? (y/n): ").strip().lower()
        if confirm != "y":
            return

    # API Wallet에 추가
    try:
        import psycopg2
        from api_wallet import APIWallet

        # PostgreSQL 연결 (중앙 설정 사용 - Phase 1 리팩토링)
        from AFO.config.settings import get_settings

        settings = get_settings()

        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )

        wallet = APIWallet(db_connection=conn)

        # 키 추가
        key_id = wallet.add(
            name="openai",
            api_key=api_key,
            service="openai",
            description="OpenAI API Key (월구독제 브라우저에서 가져옴)",
        )

        print("\n✅ API 키가 성공적으로 추가되었습니다!")
        print(f"   키 ID: {key_id}")
        print("   이름: openai")
        print("   서비스: openai")

        # 확인
        key = wallet.get("openai")
        if key:
            print(f"   확인: ✅ 키 검증 성공 ({len(key)} 문자)")
            print(f"   앞 10자: {key[:10]}...")

        conn.close()

        print("\n✅ API Wallet에 저장 완료!")
        print("이제 RAG 시스템에서 자동으로 이 키를 사용할 수 있습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
