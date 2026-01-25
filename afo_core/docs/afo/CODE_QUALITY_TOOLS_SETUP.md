# 🔍 코드 품질 도구 설정 가이드

**작성일**: 2025-12-17  
**상태**: ✅ 설정 완료  
**목적**: ruff, pytest, mypy 통합 및 사용 가이드

---

## 📋 설정된 도구

### 1. Ruff (Linter & Formatter)
- **용도**: 코드 린팅 및 포맷팅
- **설정 파일**: `pyproject.toml`
- **버전**: >=0.1.0

### 2. Pytest (Testing Framework)
- **용도**: 단위 테스트 및 통합 테스트
- **설정 파일**: `pyproject.toml`
- **버전**: >=7.4.0

### 3. MyPy (Type Checker)
- **용도**: 정적 타입 체크
- **설정 파일**: `pyproject.toml`
- **버전**: >=1.5.0

---

## 🚀 설치 방법

### 방법 1: requirements.txt 사용

```bash
pip install -r requirements.txt
```

### 방법 2: 개발 의존성만 설치

```bash
pip install ruff pytest pytest-asyncio mypy types-redis types-requests
```

### 방법 3: pyproject.toml 사용

```bash
pip install -e ".[dev]"
```

---

## 📝 사용 방법

### 1. Ruff Lint 체크

```bash
# 전체 프로젝트 린트 체크
ruff check .

# 특정 파일/디렉토리 체크
ruff check AFO/

# 자동 수정 가능한 문제 수정
ruff check --fix .
```

### 2. Ruff Format

```bash
# 코드 포맷팅
ruff format .

# 포맷팅 체크만 (변경 없음)
ruff format --check .
```

### 3. MyPy 타입 체크

```bash
# 전체 프로젝트 타입 체크
mypy AFO

# 특정 파일 체크
mypy AFO/config/settings.py

# 더 엄격한 체크
mypy AFO --strict
```

### 4. Pytest 테스트

```bash
# 단위 테스트만 실행 (기본, integration/external 제외)
make test
# 또는
pytest -q -m "not integration and not external"

# 통합 테스트 실행 (PostgreSQL, Redis 필요)
make test-integration
# 또는
pytest -q -m integration

# 외부 API 테스트 실행
make test-external
# 또는
pytest -q -m external

# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_settings.py

# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=AFO
```

#### 테스트 마커 설명

- **단위 테스트** (기본): 빠른 실행, 외부 의존성 없음
- **통합 테스트** (`@pytest.mark.integration`): PostgreSQL, Redis 등 인프라 필요
- **외부 테스트** (`@pytest.mark.external`): 외부 API 호출 필요

---

## 🔧 자동화 스크립트

### 전체 코드 품질 체크

```bash
./scripts/run_quality_checks.sh
```

이 스크립트는 다음을 실행합니다:
1. Ruff Lint 체크
2. Ruff Format 체크
3. MyPy 타입 체크
4. Pytest 테스트

### 코드 자동 포맷팅

```bash
./scripts/format_code.sh
```

---

## 📋 설정 파일

### pyproject.toml

모든 도구 설정이 `pyproject.toml`에 통합되어 있습니다:

- `[tool.ruff]`: Ruff 설정
- `[tool.pytest.ini_options]`: Pytest 설정
- `[tool.mypy]`: MyPy 설정

---

## 🎯 권장 워크플로우

### 1. 코드 작성 전

```bash
# 코드 포맷팅
./scripts/format_code.sh
```

### 2. 코드 작성 후

```bash
# 전체 품질 체크
./scripts/run_quality_checks.sh
```

### 3. Git 커밋 전

```bash
# 자동 포맷팅
ruff format .

# 린트 체크 및 수정
ruff check --fix .

# 타입 체크
mypy AFO

# 테스트 실행
pytest
```

---

## ⚙️ IDE 통합

### VS Code / Cursor

1. **Ruff 확장 설치**
   - Ruff 확장 설치
   - 자동 포맷팅 활성화

2. **MyPy 확장 설치**
   - Pylance 또는 MyPy 확장 설치
   - 타입 체크 활성화

3. **Pytest 확장 설치**
   - Python Test Explorer 설치
   - 테스트 실행 UI 제공

---

## 📊 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install ruff pytest mypy
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy AFO
      - run: pytest
```

---

## 🔍 주요 규칙

### Ruff

- **E, W**: PEP 8 스타일 가이드
- **F**: Pyflakes (미사용 변수 등)
- **I**: Import 정렬
- **B**: Bugbear (버그 가능성)
- **UP**: Python 최신 문법으로 업그레이드

### MyPy

- 타입 힌트 강제하지 않음 (점진적 적용)
- 외부 라이브러리는 `ignore_missing_imports` 사용
- 스크립트는 타입 체크 완화

### Pytest

- `tests/` 디렉토리에 테스트 파일 배치
- `test_*.py` 또는 `*_test.py` 네이밍
- `pytest-asyncio`로 비동기 테스트 지원

---

## 📝 예제 테스트

### 기본 테스트 예제

```python
# tests/test_settings.py
import pytest
from AFO.config.settings import get_settings

def test_get_settings():
    """설정 로드 테스트"""
    settings = get_settings()
    assert settings is not None
```

### 비동기 테스트 예제

```python
# tests/test_async.py
import pytest
from AFO.services.database import get_db_connection

@pytest.mark.asyncio
async def test_db_connection():
    """데이터베이스 연결 테스트"""
    conn = await get_db_connection()
    assert conn is not None
    await conn.close()
```

---

## 🎯 眞善美孝 관점

### 眞 (Truth) - 기술적 확실성
- ✅ 자동화된 코드 품질 체크
- ✅ 타입 안정성 확보

### 善 (Goodness) - 윤리·안정성
- ✅ 일관된 코드 스타일
- ✅ 버그 사전 방지

### 美 (Beauty) - 단순함·우아함
- ✅ 자동 포맷팅으로 가독성 향상
- ✅ 명확한 타입 힌트

### 孝 (Serenity) - 평온·연속성
- ✅ 형님의 시간 절약 (자동화)
- ✅ 마찰 제거 (일관된 스타일)

---

**상태**: ✅ 코드 품질 도구 설정 완료  
**다음 단계**: 테스트 작성 및 CI/CD 통합

