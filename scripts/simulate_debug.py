import time
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:8010/api/debugging"


def emit(event_type, message, level="INFO") -> None:
    payload = {
        "source": "SUPER_AGENT",
        "type": event_type,
        "message": message,
        "level": level,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        requests.post(f"{BASE_URL}/emit", json=payload)
    except Exception as e:
        print(f"Error emitting: {e}")


def simulate_debugging() -> None:
    print("🚀 Starting Simulated Debugging Session...")

    emit("session_start", "🏰 자동화 디버깅 세션 시작 (眞·善·美 정렬 체크)")
    time.sleep(1)

    emit("scan", "🔍 1,291개 파일 스캔 중... (TypeScript 80%, Python 20%)")
    time.sleep(1.5)

    emit(
        "error_found",
        "❌ [眞] api/compat.py:722 - ChancellorInvokeResponse 스키마 불일치 감지",
        level="ERROR",
    )
    time.sleep(2)

    emit(
        "reasoning",
        "🧠 [제갈량] 분석: engine_used 필드 누락으로 인한 Pydantic Validation Error 발생",
    )
    time.sleep(1)

    emit("auto_fix", "🩹 [사마휘] 자동 패치 시도: Default engine_used 추가 중...")
    time.sleep(2)

    emit("verification", "🛡️ [사마의] 검증 프로세스 가동... API 호출 결과: 200 OK")
    time.sleep(1.5)

    emit("trinity_update", "✨ Trinity Score 업데이트: 88.5 -> 92.5 (Goodness +4.0)")
    time.sleep(1)

    emit("session_end", "✅ 자동화 디버깅 완료. 왕국이 평온을 되찾았습니다 (孝).")


if __name__ == "__main__":
    # First, trigger the real endpoint (stub)
    print("Calling /api/debugging/run...")
    try:
        requests.post(f"{BASE_URL}/run")
    except:
        pass

    # Then simulate progress
    simulate_debugging()
