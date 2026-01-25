"""
Vercel Serverless Functions용 AFO Kingdom API 진입점
Phase 88: Vercel 배포를 위한 Serverless Functions 설정

Vercel Python 런타임에서 AFO Kingdom 백엔드를 실행합니다.
모든 API 라우트를 Vercel Serverless Functions로 변환.
"""

import sys
from pathlib import Path

# Python 경로 설정 (Vercel 환경용)
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Trinity OS 경로 추가
trinity_os_path = current_dir.parent / "trinity-os"
if str(trinity_os_path) not in sys.path:
    sys.path.insert(0, str(trinity_os_path))

# 환경 변수 로드 (.env 파일이 Vercel에 업로드되는 경우)
try:
    from dotenv import load_dotenv

    env_path = current_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ .env 파일 로드 성공")
    else:
        print("ℹ️ .env 파일 없음, 환경 변수 사용")
except ImportError:
    print("ℹ️ python-dotenv 없음, 환경 변수 사용")

# AFO Kingdom 서버 초기화
try:
    from AFO.api_server import server

    app = server.app
    print("✅ AFO Kingdom API 서버 초기화 성공")

    # Vercel용 추가 설정
    app.root_path = ""
    print(f"✅ FastAPI 앱 준비 완료 - {len(app.routes)}개 라우트")

except Exception as e:
    print(f"❌ AFO Kingdom 서버 초기화 실패: {e}")
    import traceback

    traceback.print_exc()

    # 폴백: 최소 FastAPI 앱
    from fastapi import FastAPI

    app = FastAPI(title="AFO Kingdom - Vercel Fallback")

    @app.get("/")
    async def root():
        return {"message": "AFO Kingdom Vercel Fallback", "status": "limited"}

    @app.get("/health")
    async def health():
        return {"status": "fallback", "message": "Vercel 배포 폴백 모드"}


# Vercel Serverless Functions에서 ASGI 앱 export
# Vercel은 이 변수를 찾아서 실행합니다
print("🚀 Vercel Serverless Functions 준비 완료")
print(f"📊 API 엔드포인트 수: {len(app.routes) if hasattr(app, 'routes') else 'N/A'}")
