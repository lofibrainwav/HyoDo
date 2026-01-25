# 🏰 AFO 왕국 백엔드 작전 본부: AGENTS.md

**FastAPI 백엔드 규약**

## 기술 스택
- Python 3.12+
- FastAPI
- Pydantic (타입 검증)
- MyPy (정적 타입 체크)
- Ruff (린팅)

## 실행 명령어
```bash
# 개발 서버
cd packages/afo-core && python -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8010

# 타입 체크
mypy . --strict

# 린팅
ruff check .
ruff format .
```

## API 설계 원칙
- RESTful 엔드포인트
- Pydantic 모델로 요청/응답 타입 지정
- 비동기 함수 (async/await)
- 예외 처리 포괄적

## 테스트
```bash
pytest tests/ -v
```

## 배포
- Docker 컨테이너화
- Poetry 의존성 관리
- 환경별 설정 분리