# 🧠 AFO 왕국 시스템 이해도 리포트

**작성일**: 2025-12-17  
**목적**: 시스템 이해도 확인 및 핵심 아키텍처 정리

---

## 📋 시스템 개요

### 핵심 철학: 眞善美孝永 (5기둥)

1. **眞 (Truth)** - 기술적 확실성
   - 정확한 문제 감지
   - 진실된 데이터
   - 증거 기반 판단

2. **善 (Goodness)** - 윤리·안정성
   - 인간 중심 설계
   - 안전한 자동화
   - 윤리적 운영

3. **美 (Beauty)** - 단순함·우아함
   - 간결한 인터페이스
   - 우아한 코드
   - 몰입 지원

4. **孝 (Serenity)** - 평온·연속성
   - 형님의 평온 최우선
   - 마찰 제거
   - 자원 보존

5. **永 (Eternity)** - 영속성
   - 지속 가능한 아키텍처
   - 영구성 보장
   - 재현 가능성

---

## 🏗️ 시스템 아키텍처

### 3대 저장소 구조

```
AFO_Kingdom/
├── AFO/              # 메인 API 서버
│   ├── FastAPI 기반
│   ├── PostgreSQL, Redis, Qdrant
│   ├── LangChain/LangGraph RAG
│   └── 코드 품질 도구 통합
│
├── TRINITY-OS/       # 통합 자동화 운영체제
│   ├── 철학 엔진
│   ├── Personas 시스템
│   ├── Bridge 로깅
│   └── 자동 실행 시스템
│
└── SixXon/          # Auth Broker & CLI
    ├── 인증 브로커
    ├── CLI 도구
    └── 문서 중심
```

---

## 🔧 기술 스택

### Backend
- **FastAPI**: API 서버 프레임워크
- **PostgreSQL**: 메인 데이터베이스 (포트: 15432)
- **Redis**: 캐시 및 세션 관리 (포트: 6379)
- **Qdrant**: 벡터 데이터베이스 (포트: 6333)

### AI/ML
- **LangChain**: LLM 프레임워크
- **LangGraph**: 워크플로우 관리
- **OpenAI**: GPT 모델
- **Anthropic**: Claude 모델
- **Ollama**: 로컬 LLM (포트: 11434)

### 코드 품질
- **Ruff**: 린터 및 포매터
- **MyPy**: 타입 체커
- **Pytest**: 테스트 프레임워크

---

## ⚙️ 설정 관리

### 중앙 설정 시스템

```
config/
├── settings.py          # 기본 설정
├── settings_dev.py      # 개발 환경
├── settings_prod.py     # 프로덕션 환경
├── settings_test.py     # 테스트 환경
└── antigravity.py       # AntiGravity 설정
```

### 설정 우선순위
1. 환경 변수 (`.env`)
2. 환경별 설정 파일
3. 기본값 (`settings.py`)

---

## 🎯 핵심 기능

### AFO 저장소
1. **API 서버** (`api_server.py`)
   - FastAPI 기반
   - 11-오장육부 건강 모니터링
   - 다양한 엔드포인트

2. **RAG 시스템** (`scripts/rag/`)
   - 옵시디언 vault 연결
   - Qdrant 벡터 DB
   - LangGraph 파이프라인

3. **코드 품질** (`scripts/run_quality_checks.sh`)
   - Ruff, MyPy, Pytest 병렬 실행
   - CI/CD 통합

4. **AntiGravity** (`config/antigravity.py`)
   - 코드 품질 자동화
   - 성능 최적화
   - 모니터링

### TRINITY-OS 저장소
1. **철학 엔진** (`scripts/philosophy_engine.py`)
2. **Personas 시스템** (`docs/personas/`)
3. **Bridge 로깅** (`docs/bridge/`)
4. **자동 실행** (`scripts/kingdom_unified_autorun.sh`)

### SixXon 저장소
1. **Auth Broker** (문서)
2. **CLI 도구** (`scripts/sixxon`)
3. **MCP 통합** (문서)

---

## 🔄 워크플로우

### 개발 워크플로우
1. 코드 작성
2. 저장 시 자동 포맷팅 (Cursor IDE)
3. 커밋 전 품질 체크
4. CI/CD 자동 검증

### 설정 동기화
1. `scripts/export_keys.py` - API 키 추출
2. `scripts/sync_workflow.sh` - 워크플로우 동기화
3. 환경 변수 설정

---

## 📊 현재 상태

### 완료된 작업
- ✅ 하드코딩 제거 및 중앙 설정 통합
- ✅ 코드 품질 도구 통합 (Ruff, MyPy, Pytest)
- ✅ Cursor IDE 설정
- ✅ AntiGravity 설정
- ✅ Phase 1, 2 리팩토링 완료
- ✅ 세 저장소 분석 (지피지기)

### 진행 중
- ⏳ 타입 힌트 추가 (Phase 3)
- ⏳ 테스트 커버리지 향상
- ⏳ Docstring 보완

### 남은 작업
- ⏳ TRINITY-OS `.env` 파일 생성
- ⏳ SixXon 기본 설정 파일 생성
- ⏳ 세 저장소 간 설정 통일

---

## 🎯 시스템 이해도 체크리스트

### 아키텍처 이해
- ✅ 3대 저장소 구조 파악
- ✅ 각 저장소의 역할 이해
- ✅ 기술 스택 파악

### 철학 이해
- ✅ 眞善美孝永 5기둥 이해
- ✅ 형님의 평온 최우선 원칙
- ✅ 메타인지 및 지피지기 접근

### 설정 관리 이해
- ✅ 중앙 설정 시스템 구조
- ✅ 환경별 설정 분리
- ✅ AntiGravity 통합

### 코드 품질 이해
- ✅ Ruff, MyPy, Pytest 역할
- ✅ 병렬 실행 구조
- ✅ CI/CD 통합

---

## 💡 핵심 인사이트

### 시스템의 목적
> **"형님의 창의력과 선한 마음만 전면에 남도록 돕는다"**

- 기술은 투명한 물처럼 배경으로
- 마찰 제거로 평온 유지
- 자원 보존으로 효율성 향상

### 설계 원칙
1. **중앙 집중식 설정**: 모든 설정을 한 곳에서 관리
2. **환경별 분리**: dev, prod, test 환경 분리
3. **자동화 우선**: 수동 작업 최소화
4. **코드 품질**: 지속적인 품질 관리
5. **문서화**: 모든 변경사항 문서화

---

## 🔍 이해도 점수

### 아키텍처: 95%
- 3대 저장소 구조 완전 이해
- 기술 스택 파악 완료
- 설정 관리 시스템 이해

### 철학: 100%
- 眞善美孝永 완전 이해
- 형님의 평온 최우선 원칙 이해
- 메타인지 접근 이해

### 구현: 90%
- 주요 기능 파악
- 워크플로우 이해
- 설정 통합 이해

### 개선점: 85%
- 일부 세부 구현 확인 필요
- TRINITY-OS와 SixXon의 구체적 통합 방식 확인 필요

---

**상태**: ✅ 시스템 이해도 높음  
**다음 단계**: 세부 구현 확인 및 통합 방식 파악

