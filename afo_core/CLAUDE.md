# CLAUDE.md — AFO Core Backend (Claude Override)

> afo-core 전용 Claude 지침 (루트 `CLAUDE.md` 상속).  
> 충돌 시 **루트 규칙이 우선**한다.

이 문서는 `packages/afo-core/` 폴더에서 작업하는 Claude 에이전트를 위한 세부 지침입니다.

---

## 0) Scope (이 폴더의 책임)

- FastAPI 기반 API/라우팅, 도메인 로직, 데이터/스키마, 검증(타입/테스트), 에러 처리
- "라우터는 얇게, 도메인 로직은 두껍게"를 원칙으로 한다.

---

## 1) SSOT (이 폴더에서 최우선으로 보는 근거)

에이전트는 작업 전 아래 파일의 **존재 여부를 확인하고** 존재하는 것만 읽는다.

- `./packages/afo-core/README.md`
- `./packages/afo-core/pyproject.toml`
- `./Makefile` (루트)
- `./packages/afo-core/scripts/` (존재 시)
- 루트: `./CLAUDE.md`, `./AGENTS.md`, `./docs/AFO_ROYAL_LIBRARY.md`, `./docs/AFO_CHANCELLOR_GRAPH_SPEC.md`

---

## 2) Setup Commands (이 폴더 전용)

### 설치
- `poetry install` (pyproject.toml 기반)
- 또는 `pip install -e ".[dev]"` (루트에서)

### 실행
- Dev server: `uvicorn AFO.main:app --reload --port 8010`
- 또는 `python -m AFO.api_server` (존재 시)

---

## 3) Quality Gates (이 폴더의 완료 기준)

### Lint / Format
- `make lint` (루트) 또는 `ruff check packages/afo-core --fix`
- `ruff format packages/afo-core`

### Type-check
- `make type-check` (루트) 또는 `poetry run mypy packages/afo-core/AFO`
- MyPy 설정: `pyproject.toml`의 `[tool.mypy]` 섹션 확인

### Tests
- `make test` (루트) 또는 `pytest packages/afo-core/tests -v`
- 테스트 마커: `smoke`, `slow`, `integration`, `api`, `unit` 등

### Build
- Docker: `docker-compose up -d` (전체 스택)
- 또는 개별 서비스: `docker-compose up afo-core`

---

## 4) 핵심 경로 (Core Paths)

- **API 라우터**: `packages/afo-core/AFO/api/` 또는 `packages/afo-core/api/routers/`
- **도메인 로직**: `packages/afo-core/AFO/domain/`
- **서비스**: `packages/afo-core/AFO/services/`
- **스키마**: `packages/afo-core/AFO/schemas/`
- **설정**: `packages/afo-core/config/` (특히 `antigravity.py`)

---

## 5) Backend Golden Rules (API/DB/에러 처리)

### A) API 레이어
- 라우터(HTTP)는 "입력 검증 + 호출 + 응답"만 담당한다.
- 비즈니스 로직은 서비스/도메인 레이어로 이동한다.
- 예외 처리:
  - 4xx/5xx를 명확히 구분한다.
  - 내부 예외를 그대로 노출하지 않는다(민감정보/스택트레이스 금지).

### B) 타입/검증(眞)
- 입력/출력은 가능한 한 명시적 스키마(예: Pydantic)를 사용한다.
- 런타임 검증이 필요한 구간은 "명시적으로" 넣는다(조용히 실패 금지).

### C) DB/데이터(善+孝)
- 데이터 손상/비가역 변경은 **ASK_COMMANDER** 기본.
- 마이그레이션/스키마 변경은:
  - DRY_RUN 가능하면 선행
  - 롤백 전략 필수(되돌리는 방법을 함께 제시)
- 쿼리/트랜잭션은 "일관성" 우선. 성능 최적화는 측정 근거 없으면 금지.

---

## 6) DRY_RUN Policy (위험 작업은 선 시뮬)

다음 중 하나라도 해당하면 반드시 DRY_RUN 선행 + ASK 필요:

- 스키마 변경/데이터 삭제/대량 업데이트
- 인증/권한/보안 관련 변경
- 비용/리소스 사용량이 큰 배치/인덱싱 작업

---

## 7) Logging & Secrets (절대 규칙)

- 토큰/키/비밀번호/쿠키/세션/개인정보를 로그에 남기지 않는다.
- 프롬프트/컨텍스트/에러 로그는 **redaction**(민감정보 마스킹) 원칙.
- 디버그 로그는 "필요 최소"로만.

---

## 8) 금지구역 (추가)

루트 `CLAUDE.md`의 금지구역에 추가:

- `packages/afo-core/config/antigravity.py` 직접 수정 금지
- `packages/afo-core/AFO/chancellor_graph.py` 변경 금지 (명시 지시 없이)
- `packages/afo-core/AFO/api_wallet.py` 핵심 로직 변경 금지

---

## 9) Claude-Specific Tips (이 폴더 작업 시)

- **논리적 단계별 계획**: API 엔드포인트 추가 시 라우터 → 서비스 → 도메인 순서로 계획
- **Tree-of-Thoughts**: 복잡한 비즈니스 로직은 여러 접근 방식을 병렬로 고려
- **타입 안전성 우선**: Pydantic 모델을 먼저 정의하고, 그 다음 구현

---

## 10) Output Contract (보고 포맷)

작업 결과는 반드시 아래 JSON 요약을 포함한다.

```json
{
  "decision": "AUTO_RUN | ASK_COMMANDER | BLOCK",
  "risk_score": 0,
  "trinity_score": 0,
  "evidence": ["..."],
  "files_changed": ["..."],
  "checks_ran": ["..."],
  "rollback_plan": ["..."]
}
```

---

**작성일**: 2025-12-21  
**Claude 팁**: 논리적 단계별 계획 먼저 작성 후 실행. 복잡한 작업은 Tree-of-Thoughts로 여러 가능성을 고려.

---

# End of ./packages/afo-core/CLAUDE.md

