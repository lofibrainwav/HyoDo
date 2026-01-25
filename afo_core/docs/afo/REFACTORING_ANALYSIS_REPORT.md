# 🔍 AFO 왕국 리팩토링 분석 보고서

**분석일**: 2025-12-16  
**범위**: AFO, TRINITY-OS, SixXon  
**목적**: 리팩토링 필요성 및 개선 방향 분석

---

## 📊 저장소 비교

### 저장소 규모

| 저장소 | Python 파일 | 주요 디렉토리 | 복잡도 |
|--------|------------|--------------|--------|
| **AFO** | 88개 | 15개 | 높음 |
| **TRINITY-OS** | 31개 | 4개 | 중간 |
| **SixXon** | 0개 | 2개 | 낮음 (문서/스크립트) |

---

## 🔴 AFO 저장소 리팩토링 필요 항목

### 1. 하드코딩된 값 (우선순위: 높음)

#### 하드코딩된 URL (16개 발견)
- `http://localhost:8000` - API Wallet URL
- `http://localhost:6333` - Qdrant URL
- `http://localhost:8787` - MCP Server URL
- `http://localhost:11434` - Ollama URL
- `http://localhost:5678` - N8N URL

**영향 파일**:
- `input_server.py`
- `afo_skills_registry.py`
- `llm_router.py`
- `api_server.py`
- `scripts/rag/config.py`
- 기타 여러 파일

#### 하드코딩된 포트 (11개 발견)
- `6379` - Redis
- `6333` - Qdrant
- `11434` - Ollama
- `8000` - API Wallet
- `8787` - MCP Server

### 2. 중복 코드 패턴 (우선순위: 중간)

#### 데이터베이스 연결 중복
- `services/database.py`: `get_db_connection()` 함수
- `api_server.py`: `check_postgres()` 함수 (동일한 로직)
- 여러 파일에서 PostgreSQL 연결 로직 반복

#### Redis 연결 중복
- `utils/cache_utils.py`: Redis 연결
- `api_wallet.py`: Redis 연결 (2곳)
- `api_server.py`: Redis 연결
- `api/routes/ragas.py`: Redis 연결

### 3. 환경 변수 관리 개선 필요 (우선순위: 중간)

**현재 상태**:
- 환경 변수 사용: 131회
- 하지만 기본값으로 `localhost` 하드코딩이 많음

**개선 방향**:
- 중앙 집중식 설정 클래스 생성
- 환경 변수 기본값을 설정 파일로 분리
- 개발/프로덕션 환경별 설정 분리

### 4. 코드 구조 개선 (우선순위: 낮음)

#### 큰 파일
- `api_server.py`: 2,020줄 (분할 고려)
- `afo_skills_registry.py`: 1,049줄

#### 설정 파일 분산
- `scripts/rag/config.py`: RAG 설정
- `api_server.py`: 서버 설정 (Settings 클래스)
- 여러 파일에 설정이 분산됨

---

## 🟡 TRINITY-OS 저장소 분석

### 현재 상태
- Python 파일: 31개
- 주로 문서 및 스크립트 중심
- 하드코딩 패턴 발견 안 됨 (문서 중심)

### 리팩토링 필요성
- **낮음**: 문서 및 스크립트 중심으로 구조가 단순함

---

## 🟢 SixXon 저장소 분석

### 현재 상태
- Python 파일: 0개
- 문서 및 스크립트만 존재
- CLI 스크립트 중심

### 리팩토링 필요성
- **없음**: 문서/스크립트만 존재

---

## 🎯 리팩토링 권장 사항

### Phase 1: 즉시 개선 (우선순위 높음)

1. **중앙 집중식 설정 클래스 생성**
   ```python
   # config/settings.py
   class AFOSettings:
       # 모든 환경 변수와 기본값을 한 곳에서 관리
       POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
       POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "15432"))
       REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
       QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
       # ...
   ```

2. **하드코딩된 URL 제거**
   - 모든 `localhost` URL을 환경 변수로 변경
   - 기본값은 설정 클래스에서 관리

3. **중복 연결 함수 통합**
   - `services/database.py`의 `get_db_connection()` 사용
   - `utils/redis_connection.py` 생성하여 Redis 연결 통합

### Phase 2: 구조 개선 (우선순위 중간)

1. **큰 파일 분할**
   - `api_server.py`를 모듈별로 분할
   - 라우터, 서비스, 설정 분리

2. **설정 파일 통합**
   - 모든 설정을 `config/` 디렉토리로 통합
   - 환경별 설정 파일 분리 (dev, prod, test)

### Phase 3: 코드 품질 개선 (우선순위 낮음)

1. **타입 힌팅 강화**
2. **에러 처리 표준화**
3. **로깅 표준화**

---

## 📋 AntiGravity 리팩토링 상태

### 검색 결과
- **커밋 3343f712e9c97e5139971273351ccbc3bbe646b3**: 발견되지 않음
- 세 저장소 모두에서 검색 결과 없음

### 가능한 원인
1. Git filter-branch로 히스토리 재작성 시 커밋 해시 변경
2. 다른 브랜치나 저장소에만 존재
3. 이미 다른 커밋에 통합됨

### 권장 조치
- 원격 저장소에서 직접 확인 필요
- 다른 AFO 디렉토리 확인 (`/Users/brnestrm/AFO` 등)

---

## ✅ 결론

### 리팩토링 필요성 요약

| 저장소 | 리팩토링 필요성 | 주요 이슈 |
|--------|----------------|----------|
| **AFO** | **높음** | 하드코딩, 중복 코드, 큰 파일 |
| **TRINITY-OS** | 낮음 | 문서 중심, 구조 단순 |
| **SixXon** | 없음 | 문서/스크립트만 존재 |

### 즉시 조치 필요 항목 (AFO)

1. ✅ 하드코딩된 URL/포트 제거 (16개 URL, 11개 포트)
2. ✅ 중복 연결 함수 통합 (PostgreSQL, Redis)
3. ✅ 중앙 집중식 설정 클래스 생성
4. ⚠️ 큰 파일 분할 고려 (`api_server.py`)

---

**상태**: ✅ 분석 완료  
**다음 단계**: Phase 1 리팩토링 실행

