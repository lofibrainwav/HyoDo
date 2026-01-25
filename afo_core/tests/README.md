# AFO Core 테스트 가이드

**작성일**: 2025-12-25  
**상태**: ✅ 테스트 구조 정리 완료

---

## 테스트 구조

### 테스트 마커

테스트는 다음 3가지 카테고리로 분류됩니다:

1. **단위 테스트** (기본): 빠른 실행, 외부 의존성 없음
2. **통합 테스트** (`@pytest.mark.integration`): PostgreSQL, Redis 등 인프라 필요
3. **외부 테스트** (`@pytest.mark.external`): 외부 API 호출 필요

---

## 테스트 실행 방법

### Makefile 사용 (권장)

```bash
# 단위 테스트만 실행 (기본)
make test

# 통합 테스트 실행 (PostgreSQL, Redis 필요)
make test-integration

# 외부 API 테스트 실행
make test-external
```

### 직접 실행

```bash
cd packages/afo-core

# 단위 테스트만
pytest -q -m "not integration and not external"

# 통합 테스트만
pytest -q -m integration

# 외부 테스트만
pytest -q -m external

# 모든 테스트
pytest -q
```

---

## 통합 테스트 사전 요구사항

### PostgreSQL
```bash
# Docker로 실행
docker-compose up -d postgres

# 또는 직접 실행 (포트 15432)
# 설정: packages/afo-core/.env
POSTGRES_HOST=localhost
POSTGRES_PORT=15432
POSTGRES_DB=afo_memory
POSTGRES_USER=afo
POSTGRES_PASSWORD=afo_secret_change_me
```

### Redis
```bash
# Docker로 실행
docker-compose up -d redis

# 또는 직접 실행 (포트 6379)
redis-server
```

---

## 최근 변경사항 (2025-12-25)

### 삭제된 테스트 (5개)
- Flaky 테스트 제거로 신뢰성 향상
- 기능은 이미 구현되어 있음
- 자세한 내용: [SKIP_TEST_ANALYSIS.md](./SKIP_TEST_ANALYSIS.md)

### 통합 테스트로 분리 (3개)
- PostgreSQL 영속성 테스트
- Redis 캐시 테스트 (2개)
- 모두 `@pytest.mark.integration` 마커 추가

### 외부 테스트로 분리 (1개)
- Gemini API 재시도 테스트
- `@pytest.mark.external` 마커 추가

---

## 테스트 작성 가이드

### 단위 테스트
- 외부 의존성 없이 실행 가능해야 함
- Mock 사용 권장
- 빠른 실행 (수 초 이내)

### 통합 테스트
- `@pytest.mark.integration` 마커 필수
- 실제 인프라(PostgreSQL, Redis) 필요
- 테스트 전후 정리 로직 포함

### 외부 테스트
- `@pytest.mark.external` 마커 필수
- 실제 API 키 또는 Mock 사용
- 네트워크 의존성 명시

---

## 문제 해결

### 테스트가 스킵되는 경우

1. **통합 테스트 스킵**: PostgreSQL/Redis가 실행 중인지 확인
2. **외부 테스트 스킵**: API 키 설정 확인 또는 Mock 사용

### Flaky 테스트

- Flaky 테스트는 삭제되었습니다
- 기능은 이미 구현되어 있으며 다른 테스트로 검증됨
- 자세한 내용: [SKIP_TEST_ANALYSIS.md](./SKIP_TEST_ANALYSIS.md)

---

**참고**: 테스트 구조 변경 이력은 [SKIP_TEST_ANALYSIS.md](./SKIP_TEST_ANALYSIS.md)에 상세히 기록되어 있습니다.

