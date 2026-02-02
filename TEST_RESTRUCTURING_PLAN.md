# HyoDo Test Restructuring Plan

**목표**: 테스트 구조 표준화 (Python best practices)
**버전**: v3.1.0

---

## 현재 문제점

```
tests/                          # 100+ 파일, 혼란스러운 구조
├── test_*.py                   # 루트에 테스트 산재
├── conftest.py                 # 설정 파일
├── llm/                        # 일부는 디렉토리로 구성
├── services/
├── api/
├── functional/
├── infrastructure/
├── filial_gate/
├── irs/
├── health/
├── strategists/
├── schema/
├── trinity_score_sharing/
├── utils/
├── validation/
├── ai/
├── application/
└── ...                         # 너무 많은 하위 디렉토리
```

**문제**:
- 테스트 유형별 분리 없음 (unit/integration/e2e)
- 디렉토리가 너무 많고 중복됨
- `scripts/archive/`에 obsolete 테스트 존재

---

## 개선된 구조

```
tests/
├── README.md                   # 테스트 가이드
├── conftest.py                 # 전체 공통 설정
├── pytest.ini                  # pytest 설정
├── unit/                       # 단위 테스트 (빠름, 격리)
│   ├── __init__.py
│   ├── conftest.py
│   ├── core/                   # 핵심 로직
│   │   ├── test_trinity.py
│   │   ├── test_calculator.py
│   │   └── test_weights.py
│   ├── services/               # 서비스 레이어
│   │   ├── test_log_analysis.py
│   │   └── test_plugin_manager.py
│   └── utils/                  # 유틸리티
│       └── test_helpers.py
├── integration/                # 통합 테스트 (DB, API)
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/                    # API 엔드포인트
│   │   ├── test_health.py
│   │   ├── test_routes.py
│   │   └── test_wallet.py
│   ├── services/               # 서비스 통합
│   │   ├── test_rag_pipeline.py
│   │   └── test_llm_router.py
│   └── db/                     # 데이터베이스
│       └── test_postgres.py
├── e2e/                        # E2E 테스트 (전체 워크플로우)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_chancellor_workflow.py
│   ├── test_quality_gates.py
│   └── test_full_pipeline.py
├── fixtures/                   # 테스트 데이터
│   ├── __init__.py
│   ├── sample_logs/
│   ├── sample_configs/
│   └── mock_responses/
└── legacy/                     # 레거시/deprecated
    ├── README.md
    └── archive/                # obsolete 테스트
```

---

## 파일 이동 계획

### 1. Unit Tests (단위 테스트)

| 현재 위치 | 새 위치 | 이유 |
|----------|--------|------|
| `test_trinity_engine.py` | `unit/core/test_trinity.py` | 핵심 로직 |
| `test_goodness_serenity.py` | `unit/core/test_error_handling.py` | 유틸리티 |
| `test_utils.py` | `unit/utils/test_helpers.py` | 유틸리티 |
| `test_crag.py` | `unit/services/test_crag.py` | 서비스 |
| `test_wallet_models.py` | `unit/core/test_models.py` | 모델 |

### 2. Integration Tests (통합 테스트)

| 현재 위치 | 새 위치 | 이유 |
|----------|--------|------|
| `test_api_health.py` | `integration/api/test_health.py` | API |
| `test_api_routes.py` | `integration/api/test_routes.py` | API |
| `test_api_wallet*.py` | `integration/api/test_wallet.py` | API |
| `services/test_*.py` | `integration/services/` | 서비스 |
| `llm/test_*.py` | `integration/llm/` | LLM |

### 3. E2E Tests (종단간 테스트)

| 현재 위치 | 새 위치 | 이유 |
|----------|--------|------|
| `test_chancellor_v3_phase2.py` | `e2e/test_chancellor_hooks.py` | 워크플로우 |
| `test_chancellor_v3_phase3.py` | `e2e/test_background_tasks.py` | 워크플로우 |
| `test_tigers_orchestrator.py` | `e2e/test_orchestration.py` | 워크플로우 |
| `test_phase80_integration.py` | `e2e/test_full_integration.py` | 전체 통합 |

### 4. Legacy (아카이브)

| 현재 위치 | 새 위치 | 조치 |
|----------|--------|------|
| `scripts/archive/test_*.py` | `tests/legacy/archive/` | 검토 후 삭제 또는 보관 |
| `test_coverage_sweep.py` | `tests/legacy/` | 특수 목적 (1.4MB) |
| `stress_test.py` | `tests/legacy/` | 부하 테스트 |
| `manual_test_*.py` | `tests/legacy/` | 수동 테스트 |

---

## conftest.py 구조

### 루트 conftest.py
```python
# tests/conftest.py
import pytest

# 전체 테스트 공통 설정

@pytest.fixture(scope="session")
def event_loop():
    """Async 테스트용 이벤트 루프"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### unit/conftest.py
```python
# tests/unit/conftest.py
import pytest

# 단위 테스트용 Mock, Stub

@pytest.fixture
def mock_trinity_calculator():
    """Mock Trinity calculator"""
    pass
```

### integration/conftest.py
```python
# tests/integration/conftest.py
import pytest

# 통합 테스트용 DB, API 클라이언트

@pytest.fixture(scope="module")
def test_db():
    """테스트용 임시 DB"""
    pass
```

---

## pytest.ini 설정

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (DB, API)
    e2e: End-to-end tests (slow)
    slow: Slow tests
    skip_ci: Skip in CI
```

---

## 실행 방법

```bash
# 전체 테스트
pytest

# 단위 테스트만 (빠름)
pytest -m unit

# 통합 테스트만
pytest -m integration

# E2E 테스트만 (느림)
pytest -m e2e

# 특정 디렉토리
pytest tests/unit/
pytest tests/integration/api/

# 병렬 실행
pytest -n auto
```

---

## 마이그레이션 단계

### Phase 1: 준비
1. [ ] 새 디렉토리 구조 생성
2. [ ] `pytest.ini` 작성
3. [ ] 루트 `conftest.py` 업데이트

### Phase 2: 이동
1. [ ] Unit tests 이동
2. [ ] Integration tests 이동
3. [ ] E2E tests 이동

### Phase 3: 정리
1. [ ] Legacy tests 정리
2. [ ] Import 경로 수정
3. [ ] CI 파이프라인 업데이트

### Phase 4: 검증
1. [ ] 전체 테스트 실행
2. [ ] CI 통과 확인
3. [ ] 문서 업데이트

---

## 기대 효과

| 지표 | 개선 전 | 개선 후 |
|------|--------|--------|
| 테스트 찾기 | 어려움 | 쉬움 (유형별 분리) |
| 실행 시간 | 전체 실행만 | 선택적 실행 가능 |
| 유지보수 | 복잡 | 단순 |
| 신규 기여 | 진입 장벽 | 명확한 구조 |

---

**계획 작성**: 2026-02-01  
**목표 버전**: v3.2.0
