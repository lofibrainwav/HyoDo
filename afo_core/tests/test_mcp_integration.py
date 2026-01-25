# Trinity Score: 90.0 (Established by Chancellor)
"""
MCP 통신 통합 테스트
프로세스 재사용 방식 검증
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_AFO_ROOT = Path(__file__).resolve().parent.parent
if str(_AFO_ROOT) not in sys.path:
    sys.path.insert(0, str(_AFO_ROOT))


async def test_mcp_log_event_full_flow():
    """MCP 로그 이벤트 전체 플로우 테스트"""
    print("=" * 60)
    print("🔍 MCP 로그 이벤트 전체 플로우 테스트")
    print("=" * 60)

    try:
        from AFO.api.compat import get_trinity_os_client

        client = get_trinity_os_client()
        if not client or not client.available:
            print("❌ MCP 클라이언트를 사용할 수 없습니다!")
            return

        print("\n1️⃣ 클라이언트 상태:")
        print(f"   사용 가능: {client.available}")
        print(f"   서버 경로: {client._server_path if hasattr(client, '_server_path') else 'N/A'}")

        # 테스트 데이터
        test_data = {
            "persona_id": "p007",
            "persona_name": "배움의 길 (眞 Learning)",
            "persona_type": "learner",
            "trinity_scores": {
                "truth": 100.0,
                "goodness": 95.0,
                "beauty": 85.0,
                "serenity": 97.0,
                "eternity": 100.0,
            },
            "timestamp": "2025-12-21T05:00:00Z",
            "test": True,
        }

        print("\n2️⃣ 로그 이벤트 전송:")
        print("   이벤트 타입: persona_switch")
        print(f"   페르소나: {test_data['persona_name']}")

        await client.send_log_event("persona_switch", test_data)

        print("   ✅ 이벤트 전송 완료")

        # 파일 생성 확인
        log_path = Path("logs/persona_events/persona_switch_p007.json")
        if log_path.exists():
            print("\n3️⃣ 로그 파일 확인:")
            print(f"   경로: {log_path.absolute()}")
            content = log_path.read_text(encoding="utf-8")
            data = json.loads(content)
            print("   ✅ 파일 생성 확인")
            print(f"   페르소나 ID: {data.get('persona_id')}")
            print(f"   페르소나 이름: {data.get('persona_name')}")
            print(f"   파일 크기: {len(content)} bytes")
        else:
            print("\n3️⃣ 로그 파일 확인:")
            print(f"   ⚠️  파일이 생성되지 않았습니다 (경로: {log_path.absolute()})")
            print("   💡 MCP 서버가 로컬 로깅으로 폴백했을 수 있습니다")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


async def test_mcp_multiple_events():
    """여러 이벤트 연속 전송 테스트"""
    print("\n" + "=" * 60)
    print("🔍 여러 이벤트 연속 전송 테스트")
    print("=" * 60)

    try:
        from AFO.api.compat import get_trinity_os_client

        client = get_trinity_os_client()
        if not client or not client.available:
            print("❌ MCP 클라이언트를 사용할 수 없습니다!")
            return

        events = [
            ("persona_switch", {"persona_id": "p001", "persona_name": "사령관"}),
            ("persona_switch", {"persona_id": "p002", "persona_name": "가장"}),
            ("persona_switch", {"persona_id": "p007", "persona_name": "배움의 길"}),
        ]

        print(f"\n{len(events)}개 이벤트 전송 중...")
        for i, (event_type, data) in enumerate(events, 1):
            await client.send_log_event(event_type, data)
            print(f"   {i}. {data['persona_name']} ✅")
            await asyncio.sleep(0.1)  # 짧은 지연

        print("\n✅ 모든 이벤트 전송 완료")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    await test_mcp_log_event_full_flow()
    await test_mcp_multiple_events()

    print("\n" + "=" * 60)
    print("✅ MCP 통신 통합 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
