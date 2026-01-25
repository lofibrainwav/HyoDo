# 📋 Phase 2-5: 환경별 설정 분리

**문서일**: 2025-12-17  
**상태**: ✅ 완료  
**목적**: 개발, 프로덕션, 테스트 환경별 설정 분리

---

## 📊 구현 구조

### 설정 파일 구조

```
config/
├── settings.py          # 기본 설정 (AFOSettings)
├── settings_dev.py      # Development 환경 (AFOSettingsDev)
├── settings_prod.py     # Production 환경 (AFOSettingsProd)
└── settings_test.py     # Test 환경 (AFOSettingsTest)
```

### 환경별 설정 클래스

모든 환경별 설정 클래스는 `AFOSettings`를 상속받아 기본 설정을 확장/오버라이드합니다.

#### 1. Development 환경 (`AFOSettingsDev`)

- **파일**: `config/settings_dev.py`
- **환경 변수**: `AFO_ENV=dev` (기본값)
- **특징**:
  - `MOCK_MODE=True` - 개발 시 Mock 모드 활성화
  - `LOG_LEVEL=DEBUG` - 상세한 로깅
  - 모든 서비스가 `localhost`에서 실행
  - `.env.dev` 파일 지원

#### 2. Production 환경 (`AFOSettingsProd`)

- **파일**: `config/settings_prod.py`
- **환경 변수**: `AFO_ENV=prod` 또는 `AFO_ENV=production`
- **특징**:
  - `MOCK_MODE=False` - 프로덕션에서는 Mock 모드 비활성화
  - `LOG_LEVEL=INFO` - 프로덕션 로깅
  - 모든 설정은 환경 변수에서 필수로 로드
  - `.env.prod` 파일 지원

#### 3. Test 환경 (`AFOSettingsTest`)

- **파일**: `config/settings_test.py`
- **환경 변수**: `AFO_ENV=test` 또는 `AFO_ENV=testing`
- **특징**:
  - `MOCK_MODE=True` - 테스트 시 Mock 모드 활성화
  - `LOG_LEVEL=WARNING` - 최소 로깅
  - 테스트용 포트 사용 (프로덕션과 분리)
  - `.env.test` 파일 지원

---

## 🚀 사용 방법

### 환경 변수 설정

```bash
# Development 환경 (기본값)
export AFO_ENV=dev

# Production 환경
export AFO_ENV=prod

# Test 환경
export AFO_ENV=test
```

### 코드에서 사용

```python
from AFO.config.settings import get_settings

# 환경 변수에 따라 자동으로 적절한 설정 로드
settings = get_settings()

# 또는 명시적으로 환경 지정
settings = get_settings(env="prod")
```

### 환경별 .env 파일

각 환경별로 별도의 `.env` 파일을 사용할 수 있습니다:

- `.env.dev` - Development 환경
- `.env.prod` - Production 환경
- `.env.test` - Test 환경

---

## 📝 환경별 설정 차이점

| 설정 항목 | Development | Production | Test |
|----------|------------|------------|------|
| MOCK_MODE | `True` | `False` | `True` |
| LOG_LEVEL | `DEBUG` | `INFO` | `WARNING` |
| POSTGRES_PORT | `15432` | 환경 변수 | `15433` |
| REDIS_PORT | `6379` | 환경 변수 | `6380` |
| OLLAMA_BASE_URL | `localhost:11434` | 환경 변수 | `localhost:11435` |

---

## ✅ Phase 2-5 완료 사항

1. ✅ `config/settings_dev.py` 생성
2. ✅ `config/settings_prod.py` 생성
3. ✅ `config/settings_test.py` 생성
4. ✅ `get_settings()` 함수에 환경별 로드 로직 추가
5. ✅ 환경별 설정 문서화

---

## 📋 다음 단계

- Phase 3: 코드 품질 개선 (타입 힌팅, 에러 처리, 로깅)

---

**상태**: ✅ Phase 2-5 완료

