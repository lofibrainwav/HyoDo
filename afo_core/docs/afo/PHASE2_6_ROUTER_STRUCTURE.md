# 📋 Phase 2-6: 라우터 구조 문서화

**문서일**: 2025-12-17  
**상태**: ✅ 완료  
**목적**: AFO API 라우터 구조 정리 및 문서화

---

## 📊 현재 라우터 구조

### api/routers/ (Phase 2 분리된 라우터)

Phase 2 리팩토링을 통해 `api_server.py`에서 분리된 라우터들:

1. **root.py** - Root 엔드포인트
   - `GET /` - API 메타데이터 반환
   - Phase 2-4: settings 통합 완료

2. **health.py** - Health Check 엔드포인트
   - `GET /health` - Trinity Score 기반 건강도 체크
   - Phase 2-4: settings 통합 완료

3. **chancellor_router.py** - Chancellor 관련 엔드포인트

### api/routes/ (기존 라우터)

동적 라우터 자동 등록 시스템을 통해 자동으로 포함되는 라우터들:

1. **crag.py** - Corrective RAG 엔드포인트
2. **pillars.py** - 眞善美孝 Pillars 엔드포인트
3. **ragas.py** - Ragas 평가 엔드포인트
4. **skills.py** - Skills Registry 엔드포인트
5. **system_health.py** - 시스템 건강도 엔드포인트
6. **wallet/** - API Wallet 관련 엔드포인트
   - `billing.py`
   - `browser_bridge.py`
   - `keys.py`
   - `models.py`
   - `session.py`
   - `setup.py`

---

## 🔄 동적 라우터 자동 등록

`api_server.py`에는 Strangler Fig Pattern을 사용한 동적 라우터 자동 등록 시스템이 있습니다:

```python
from afo_soul_engine.api.fig_overlay.auto_inject import auto_include_all_routers
auto_include_all_routers(app)
```

이 시스템은 `api/routers/` 및 `api/routes/` 디렉토리의 모든 라우터를 자동으로 등록합니다.

---

## 📝 api_server.py의 Legacy 엔드포인트

Phase 2-6 완료 후 `api_server.py`에 남아있는 엔드포인트:

1. **GET /** (legacy)
   - `include_in_schema=False`
   - `root_router`로 위임
   - 하위 호환성 유지

2. **GET /health** (legacy)
   - `include_in_schema=False`
   - `health_router`로 위임
   - 하위 호환성 유지

3. **GET /health_old** (legacy)
   - `include_in_schema=False`
   - 구버전 health check

---

## ✅ Phase 2-6 완료 사항

1. ✅ Root 엔드포인트 분리 (`api/routers/root.py`)
2. ✅ Health 엔드포인트 분리 (`api/routers/health.py`)
3. ✅ Legacy 엔드포인트 정리 (하위 호환성 유지)
4. ✅ 라우터 구조 문서화

---

## 📋 다음 단계

- Phase 2-5: 환경별 설정 분리 (dev/prod/test)
- Phase 3: 코드 품질 개선 (타입 힌팅, 에러 처리, 로깅)

---

**상태**: ✅ Phase 2-6 완료

