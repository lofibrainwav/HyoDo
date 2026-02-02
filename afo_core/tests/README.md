# HyoDo Test Suite

> **"眞善美孝永의 검증"** - 5기둥 철학이 적용된 테스트 구조

---

## 🎯 테스트 철학

HyoDo의 테스트는 5기둥 철학을 따릅니다:

| 기둥 | 테스트 원칙 | 적용 |
|------|------------|------|
| 眞 Truth | 정확한 검증 | 명확한 assertion, 타입 체크 |
| 善 Goodness | 안전한 테스트 | 격리, 독립성, no side effects |
| 美 Beauty | 깔끔한 구조 | 일관된 패턴, 명확한 이름 |
| 孝 Serenity | 편리한 실행 | 빠른 피드백, 선택적 실행 |
| 永 Eternity | 지속 가능성 | 문서화, 유지보수 용이 |

---

## 📁 디렉토리 구조

```
tests/
├── unit/           # 단위 테스트 (빠름, 격리)
├── integration/    # 통합 테스트 (DB, API)
├── e2e/            # E2E 테스트 (전체 워크플로우)
├── fixtures/       # 테스트 데이터
└── legacy/         # 레거시/deprecated
```

---

## 🚀 빠른 시작

```bash
# 전체 테스트
pytest

# 단위 테스트만 (빠름: ~30초)
pytest tests/unit/ -v

# 통합 테스트만 (~2분)
pytest tests/integration/ -v

# E2E 테스트만 (~5분)
pytest tests/e2e/ -v

# 병렬 실행 (빠름)
pytest -n auto
```

---

## 📝 테스트 작성 가이드

### Unit Test 예시

```python
# tests/unit/core/test_trinity.py
import pytest
from hyodo import calculate_trinity_score

def test_trinity_score_calculation():
    """Trinity Score 계산 검증"""
    score = calculate_trinity_score(
        truth=1.0,
        goodness=1.0,
        beauty=1.0,
        serenity=1.0,
        eternity=1.0
    )
    assert score == 100.0

def test_trinity_score_weighted():
    """가중치 적용 검증"""
    score = calculate_trinity_score(
        truth=0.5,      # 35% weight
        goodness=0.5,   # 35% weight
        beauty=0.5,     # 20% weight
        serenity=0.5,   # 8% weight
        eternity=0.5    # 2% weight
    )
    assert score == 50.0
```

### Integration Test 예시

```python
# tests/integration/api/test_health.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)

def test_health_endpoint(client):
    """Health check API 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### E2E Test 예시

```python
# tests/e2e/test_quality_gates.py
import pytest

@pytest.mark.e2e
@pytest.mark.slow
def test_full_quality_pipeline():
    """전체 품질 게이트 파이프라인 테스트"""
    # 1. 코드 분석
    # 2. 품질 검사
    # 3. 리포트 생성
    pass
```

---

## 🏷️ 마커 (Markers)

```python
import pytest

@pytest.mark.unit           # 단위 테스트
@pytest.mark.integration    # 통합 테스트
@pytest.mark.e2e           # E2E 테스트
@pytest.mark.slow          # 느린 테스트
@pytest.mark.skip_ci       # CI에서 제외
```

실행:
```bash
pytest -m unit             # 단위 테스트만
pytest -m "not slow"       # 느린 테스트 제외
pytest -m "unit or integration"  # 둘 다
```

---

## 🔧 Fixtures

### 공통 Fixture

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def event_loop():
    """Async 테스트용 이벤트 루프"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_trinity_data():
    """테스트용 Trinity 데이터"""
    return {
        "truth": 0.9,
        "goodness": 0.85,
        "beauty": 0.8,
        "serenity": 0.95,
        "eternity": 0.9
    }
```

---

## 📊 테스트 커버리지

```bash
# 커버리지 리포트 생성
pytest --cov=hyodo --cov-report=html

# 커버리지 확인
pytest --cov=hyodo --cov-report=term-missing
```

목표 커버리지:
- Unit tests: 90%+
- Integration tests: 80%+
- E2E tests: 핵심 워크플로우

---

## 🆘 문제 해결

### 테스트 실패 디버깅

```bash
# 상세 출력
pytest -v --tb=long

# 특정 테스트만
pytest tests/unit/test_specific.py::test_function -v

# PDB 디버거
pytest --pdb

# 실패한 테스트만 재실행
pytest --lf
```

### 일반적인 문제

**ImportError 발생**
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**DB 연결 실패**
```bash
# 테스트 DB 실행
docker-compose -f docker-compose.minimal.yml up -d
```

---

## 📚 참고 문서

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HyoDo CONTRIBUTING.md](../CONTRIBUTING.md)

---

**총 테스트 수**: 100+  
**예상 실행 시간**: Unit (~30s) / Integration (~2m) / E2E (~5m)

*마지막 업데이트: v3.1.0*
