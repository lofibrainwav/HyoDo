"""
Start Server with Logging
서버를 시작하고 등록 로그를 확인하는 스크립트
"""

# #region agent log
import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("./.cursor/debug.log")


def log_debug(
    location: str, message: str, data: dict | None = None, hypothesis_id: str = "A"
) -> None:
    """Debug logging to NDJSON file"""
    try:
        log_entry = {
            "id": f"log_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "start-server-with-logging",
            "runId": "start",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}")


# #endregion agent log

print("\n🏰 서버 시작 및 로그 모니터링\n")
print("=" * 60)

# #region agent log
log_debug("start_server_with_logging.py:main", "Starting server monitoring", {}, "A")
# #endregion agent log

# 서버 시작 명령
server_dir = Path(__file__).parent.parent / "packages" / "afo-core"
server_cmd = [
    "python",
    "-m",
    "uvicorn",
    "api_server:app",
    "--reload",
    "--port",
    "8010",
]

print(f"📂 서버 디렉토리: {server_dir}")
print(f"🚀 서버 시작 명령: {' '.join(server_cmd)}")
print("\n💡 서버를 시작하려면 다음 명령을 실행하세요:")
print(f"   cd {server_dir}")
print(f"   {' '.join(server_cmd)}")
print("\n📋 서버 시작 로그에서 다음 메시지를 확인하세요:")
print("   - '✅ Comprehensive Health Check 라우터 등록 완료 (조기 등록)'")
print("   - '✅ Intake API 라우터 등록 완료 (조기 등록)'")
print("   - '✅ Family Hub API 라우터 등록 완료 - /family and /api/family'")
print("\n⚠️  만약 위 메시지들이 출력되지 않으면, 에러 메시지를 확인하세요.")

# #region agent log
log_debug(
    "start_server_with_logging.py:main",
    "Server start instructions provided",
    {"server_dir": str(server_dir), "command": " ".join(server_cmd)},
    "A",
)
# #endregion agent log
