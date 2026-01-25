# Trinity Score: 90.0 (Established by Chancellor)
"""
MCP 클라이언트 디버깅 테스트
실패 원인 진단을 위한 단계별 테스트
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_AFO_ROOT = Path(__file__).resolve().parent.parent
if str(_AFO_ROOT) not in sys.path:
    sys.path.insert(0, str(_AFO_ROOT))


async def test_mcp_server_direct():
    """MCP 서버 직접 실행 테스트"""
    print("=" * 60)
    print("🔍 MCP 서버 직접 실행 테스트")
    print("=" * 60)

    mcp_server_path = (
        Path(__file__).parent.parent.parent
        / "trinity-os"
        / "trinity_os"
        / "servers"
        / "afo_ultimate_mcp_server.py"
    )

    print("\n1️⃣ 서버 경로 확인:")
    print(f"   경로: {mcp_server_path}")
    print(f"   존재: {mcp_server_path.exists()}")

    if not mcp_server_path.exists():
        print("   ❌ MCP 서버 파일을 찾을 수 없습니다!")
        return

    print("\n2️⃣ 서버 프로세스 시작 테스트:")
    try:
        process = await asyncio.create_subprocess_exec(
            "python3",
            str(mcp_server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        print(f"   ✅ 프로세스 시작 성공 (PID: {process.pid})")

        # Initialize 요청 전송
        print("\n3️⃣ Initialize 요청 전송:")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "TestClient", "version": "1.0"},
            },
        }

        if process.stdin:
            request_json = json.dumps(init_request) + "\n"
            print(f"   전송: {request_json.strip()}")
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

        # 응답 수신
        print("\n4️⃣ 응답 수신 대기:")
        try:
            if process.stdout:
                response_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
                if response_line:
                    response = json.loads(response_line.decode())
                    print(f"   ✅ 응답 수신: {json.dumps(response, indent=2, ensure_ascii=False)}")
                else:
                    print("   ❌ 응답 없음")
        except TimeoutError:
            print("   ❌ 타임아웃 (5초)")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 파싱 오류: {e}")
            if process.stdout:
                raw = await process.stdout.read(1024)
                print(f"   원본 응답: {raw.decode()}")

        # 프로세스 종료
        if process.returncode is None:
            process.terminate()
            await process.wait()
            print("\n5️⃣ 프로세스 종료 완료")

    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()


async def test_mcp_client_wrapper():
    """MCP 클라이언트 래퍼 테스트"""
    print("\n" + "=" * 60)
    print("🔍 MCP 클라이언트 래퍼 테스트")
    print("=" * 60)

    try:
        from AFO.api.compat import get_trinity_os_client

        client = get_trinity_os_client()
        print("\n1️⃣ 클라이언트 생성:")
        print(f"   클라이언트: {client}")
        print(f"   사용 가능: {client.available if client else False}")

        if not client or not client.available:
            print("   ❌ 클라이언트를 사용할 수 없습니다!")
            return

        print("\n2️⃣ 로그 이벤트 전송 테스트:")
        test_data = {
            "persona_id": "p001",
            "persona_name": "테스트 페르소나",
            "event": "test",
        }

        try:
            await client.send_log_event("test_event", test_data)
            print("   ✅ 이벤트 전송 성공")
        except Exception as e:
            print(f"   ❌ 이벤트 전송 실패: {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"   ❌ 클라이언트 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    await test_mcp_server_direct()
    await test_mcp_client_wrapper()

    print("\n" + "=" * 60)
    print("✅ 디버깅 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
