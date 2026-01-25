# 🚀 AntiGravity 설정 가이드

**작성일**: 2025-12-17  
**상태**: ✅ 설정 완료  
**목적**: AFO 왕국 AntiGravity 시스템 설정 및 사용 가이드

---

## 📋 AntiGravity란?

AntiGravity는 AFO 왕국의 **코드 품질 및 성능 향상 시스템**입니다.

**주요 기능**:
- 코드 품질 자동화 (포맷팅, 린팅, 타입 체크)
- 성능 최적화 (캐싱, 비동기 처리)
- 모니터링 및 메트릭 수집
- 개발 도구 통합

---

## 🔧 설정 파일

### 1. `AFO/config/antigravity.py`
- AntiGravity 설정 클래스
- Pydantic 기반 설정 관리
- 환경 변수 지원

### 2. `.cursor/antigravity.json`
- Cursor IDE 통합 설정
- 워크플로우 정의
- 도구별 설정

### 3. `AFO/config/settings.py` 통합
- `get_antigravity_config()` 메서드 추가
- 기존 설정과 통합

---

## ⚙️ 주요 설정

### 코드 품질

```python
ENABLE_AUTO_FORMAT: bool = True      # 자동 포맷팅
ENABLE_TYPE_CHECK: bool = True       # 타입 체크
ENABLE_LINT_ON_SAVE: bool = True     # 저장 시 린트
```

### 성능 최적화

```python
ENABLE_CACHE: bool = True            # 캐시 활성화
CACHE_TTL: int = 300                 # 캐시 TTL (초)
ENABLE_ASYNC: bool = True            # 비동기 처리
```

### 모니터링

```python
ENABLE_METRICS: bool = True          # 메트릭 수집
METRICS_INTERVAL: int = 60           # 수집 간격 (초)
```

### 개발 도구

```python
ENABLE_HOT_RELOAD: bool = True       # 핫 리로드
ENABLE_DEBUG_LOGGING: bool = False   # 디버그 로깅
```

---

## 🚀 사용 방법

### 1. 설정 가져오기

```python
from AFO.config.antigravity import get_antigravity_settings

settings = get_antigravity_settings()

# 캐시 설정
cache_config = settings.get_cache_config()

# 메트릭 설정
metrics_config = settings.get_metrics_config()

# 개발 도구 설정
dev_tools = settings.get_dev_tools_config()
```

### 2. 통합 설정 사용

```python
from AFO.config.settings import get_settings

settings = get_settings()

# AntiGravity 설정 포함
ag_config = settings.get_antigravity_config()
```

### 3. 환경 변수 설정

```bash
# .env 파일
ANTIGRAVITY_ENABLE_AUTO_FORMAT=true
ANTIGRAVITY_ENABLE_TYPE_CHECK=true
ANTIGRAVITY_CACHE_TTL=300
ANTIGRAVITY_ENABLE_METRICS=true
```

---

## 🔄 워크플로우

### 저장 시 (on_save)
1. 코드 포맷팅 (Ruff)
2. Import 정렬
3. 린트 이슈 자동 수정

### 커밋 시 (on_commit)
1. 테스트 실행
2. 타입 체크
3. 린트 체크

---

## 📊 모니터링

### 메트릭 수집

```python
from AFO.config.antigravity import get_antigravity_settings

settings = get_antigravity_settings()
if settings.ENABLE_METRICS:
    # 메트릭 수집 로직
    metrics = collect_metrics()
```

### 캐시 사용

```python
from AFO.config.antigravity import get_antigravity_settings

settings = get_antigravity_settings()
cache_config = settings.get_cache_config()

if cache_config["enabled"]:
    # 캐시 사용 로직
    cached_data = get_from_cache(key, ttl=cache_config["ttl"])
```

---

## 🎯 Cursor IDE 통합

### 자동 적용

`.cursor/antigravity.json` 파일이 있으면 Cursor IDE가 자동으로:
- 저장 시 포맷팅
- Import 정렬
- 린트 이슈 수정

### 수동 실행

```bash
# 코드 품질 체크
./scripts/run_quality_checks.sh

# 포맷팅
ruff format .

# 타입 체크
mypy AFO
```

---

## 🔍 문제 해결

### 설정이 적용되지 않는 경우

1. **환경 변수 확인**
   ```bash
   echo $ANTIGRAVITY_ENABLE_AUTO_FORMAT
   ```

2. **설정 파일 확인**
   ```python
   from AFO.config.antigravity import get_antigravity_settings
   settings = get_antigravity_settings()
   print(settings.ENABLE_AUTO_FORMAT)
   ```

3. **Cursor IDE 재시작**
   - 설정 파일 변경 후 재시작 필요

### 성능 이슈

- 캐시 TTL 조정: `CACHE_TTL` 값 변경
- 비동기 처리 비활성화: `ENABLE_ASYNC = False`
- 메트릭 수집 간격 조정: `METRICS_INTERVAL` 값 변경

---

## 📝 참고 사항

- 모든 설정은 환경 변수로 오버라이드 가능
- 기본값은 개발 환경에 최적화됨
- 프로덕션 환경에서는 메트릭 수집 활성화 권장

---

## 🎯 眞善美孝 관점

### 眞 (Truth) - 기술적 확실성
- ✅ Pydantic 기반 타입 안전 설정
- ✅ 환경 변수 검증

### 善 (Goodness) - 윤리·안정성
- ✅ 기본값은 안전한 설정
- ✅ 성능 최적화 옵션 제공

### 美 (Beauty) - 단순함·우아함
- ✅ 간단한 API
- ✅ 명확한 설정 구조

### 孝 (Serenity) - 평온·연속성
- ✅ 자동화로 마찰 제거
- ✅ 개발자 경험 향상

---

**상태**: ✅ AntiGravity 설정 완료  
**효과**: 코드 품질 자동화 및 성능 최적화

