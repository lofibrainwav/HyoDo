# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""API Wallet 상태 확인 스크립트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api_wallet import APIWallet


def main() -> None:
    print("=== API Wallet 시스템 상태 확인 ===\n")

    # Wallet 초기화
    wallet = APIWallet()

    # 저장소 경로 확인
    print("1️⃣ 저장소 정보:")
    if hasattr(wallet, "storage_path"):
        print(f"   JSON 파일: {wallet.storage_path}")
        if wallet.storage_path.exists():
            size = wallet.storage_path.stat().st_size
            print(f"   파일 크기: {size} bytes")
        else:
            print("   ⚠️  파일 없음")

    if hasattr(wallet, "use_db"):
        print(f"   DB 사용: {wallet.use_db}")

    print()

    # 키 목록 확인
    print("2️⃣ 저장된 키 목록:")
    keys = wallet.list_keys()
    print(f"   총 {len(keys)}개 키")
    print()

    if keys:
        for i, k in enumerate(keys, 1):
            print(f"   {i}. {k['name']}")
            print(f"      서비스: {k.get('service', '없음')}")
            print(f"      타입: {k.get('key_type', '없음')}")
            print(f"      읽기 전용: {k.get('read_only', False)}")
            print(f"      생성일: {k.get('created_at', '없음')}")
            print(f"      접근 횟수: {k.get('access_count', 0)}")
            print()
    else:
        print("   (저장된 키 없음)")
        print()

    # OpenAI 키 검색
    print("3️⃣ OpenAI 키 검색:")
    possible_names = [
        "openai",
        "OPENAI",
        "OpenAI",
        "gpt",
        "GPT",
        "openai_api_key",
        "OPENAI_API_KEY",
    ]
    found = False

    for name in possible_names:
        key = wallet.get(name)
        if key:
            print(f"   ✅ 키 발견: {name}")
            print(f"      길이: {len(key)} 문자")
            print(f"      앞 10자: {key[:10]}...")
            found = True
            break

    if not found:
        print("   ❌ 직접 이름으로 찾지 못함")
        print()
        print("   service 필드로 검색:")
        openai_services = [
            k
            for k in keys
            if "openai" in k.get("service", "").lower() or "gpt" in k.get("service", "").lower()
        ]

        if openai_services:
            for k in openai_services:
                key = wallet.get(k["name"])
                if key:
                    print(f"   ✅ {k['name']}: {len(key)} 문자")
                    found = True
        else:
            print("   ❌ OpenAI 관련 키 없음")

    print()

    # Audit 로그 확인
    print("4️⃣ Audit 로그:")
    if hasattr(wallet, "audit_log_path"):
        print(f"   경로: {wallet.audit_log_path}")
        if wallet.audit_log_path.exists():
            lines = wallet.audit_log_path.read_text().strip().split("\n")
            print(f"   총 {len(lines)}개 로그 항목")
            if lines:
                print("   최근 5개 항목:")
                for line in lines[-5:]:
                    print(f"      {line}")
        else:
            print("   ⚠️  로그 파일 없음")

    print()
    print("=== 확인 완료 ===")


if __name__ == "__main__":
    main()
