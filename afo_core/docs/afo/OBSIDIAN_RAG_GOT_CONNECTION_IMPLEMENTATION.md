# ✅ 옵시디언 vault → RAG GoT 연결 구현 완료

**구현일**: 2025-12-16  
**상태**: ✅ 구현 완료  
**목적**: LangGraph를 사용한 옵시디언 vault와 RAG GoT 연결 시스템

---

## 📊 구현 완료 항목

### ✅ 생성된 스크립트 (4개)

1. **obsidian_loader.py** - 옵시디언 문서 로더
   - Markdown 파일 로드
   - Frontmatter 파싱
   - 링크/태그 추출
   - 카테고리 분류

2. **index_obsidian_to_qdrant.py** - 벡터 DB 인덱싱
   - Qdrant 연결
   - 텍스트 청킹
   - 임베딩 생성
   - 벡터 저장

3. **rag_graph.py** - LangGraph RAG 파이프라인
   - 문서 검색
   - 답변 생성
   - 워크플로우 구성

4. **sync_obsidian_vault.py** - 자동 동기화
   - 파일 변경 감지
   - 자동 재인덱싱
   - 상태 관리

### ✅ 설정 파일

- `requirements.txt` - 의존성 목록
- `README.md` - 사용 가이드

---

## 🔧 시스템 아키텍처

```
옵시디언 Vault (docs/)
    ↓
ObsidianLoader
    ├─ Frontmatter 파싱
    ├─ 링크 추출 [[링크]]
    ├─ 태그 추출 #태그
    └─ 카테고리 분류
    ↓
텍스트 분할 (RecursiveCharacterTextSplitter)
    ├─ chunk_size: 1000
    └─ chunk_overlap: 200
    ↓
OpenAI Embeddings (text-embedding-3-small)
    ↓
Qdrant Vector DB
    ├─ 컬렉션: obsidian_vault
    └─ 벡터 차원: 1536
    ↓
LangGraph RAG Pipeline
    ├─ retrieve: 문서 검색
    └─ generate: 답변 생성
    ↓
질의응답 결과
```

---

## 🚀 사용 방법

### 1. 의존성 설치

```bash
cd ${HOME}/AFO/scripts/rag
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
export OPENAI_API_KEY="your-api-key"
export QDRANT_URL="http://localhost:6333"
```

### 3. 초기 인덱싱

```bash
python index_obsidian_to_qdrant.py --clear
```

### 4. RAG 질의 테스트

```bash
python rag_graph.py
```

### 5. 자동 동기화 시작

```bash
python sync_obsidian_vault.py --initial-sync
```

---

## 📋 주요 기능

### 문서 로더 기능

- ✅ Markdown 파일 로드
- ✅ Frontmatter 메타데이터 파싱
- ✅ 옵시디언 링크 추출 (`[[링크]]`)
- ✅ 태그 추출 (`#태그`)
- ✅ 카테고리 자동 분류
- ✅ 제외 패턴 지원 (`.obsidian`, `templates` 등)

### 벡터 DB 인덱싱

- ✅ Qdrant 연결 및 컬렉션 관리
- ✅ 텍스트 청킹 (재귀적 분할)
- ✅ OpenAI 임베딩 생성
- ✅ 메타데이터 저장
- ✅ 증분 업데이트 지원

### RAG 파이프라인

- ✅ LangGraph 워크플로우
- ✅ 유사도 기반 문서 검색
- ✅ 컨텍스트 기반 답변 생성
- ✅ 메타데이터 반환

### 자동 동기화

- ✅ 실시간 파일 변경 감지
- ✅ MD5 해시 기반 변경 추적
- ✅ 주기적 재인덱싱 (60초)
- ✅ 상태 파일 관리

---

## 🔧 설정 옵션

### 환경 변수

- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `QDRANT_URL`: Qdrant 서버 URL (기본: http://localhost:6333)

### 스크립트 파라미터

#### 인덱싱
- `--vault-path`: vault 경로
- `--qdrant-url`: Qdrant URL
- `--collection`: 컬렉션 이름
- `--clear`: 기존 데이터 삭제
- `--chunk-size`: 청크 크기 (기본: 1000)
- `--chunk-overlap`: 청크 오버랩 (기본: 200)

#### 동기화
- `--vault-path`: vault 경로
- `--state-file`: 상태 파일 경로
- `--initial-sync`: 초기 동기화 실행

---

## 📊 예상 성능

### 인덱싱

- **문서 수**: 약 100개 기준
- **처리 시간**: 약 2-5분
- **청크 수**: 약 500-1000개 (문서당 평균 5-10개)

### 검색

- **검색 속도**: < 1초
- **반환 문서**: 상위 5개
- **정확도**: 유사도 기반

---

## ✅ 검증 체크리스트

### 설치 확인

- [ ] 의존성 설치 완료
- [ ] 환경 변수 설정 완료
- [ ] Qdrant 서버 실행 중

### 기능 확인

- [ ] 문서 로더 테스트 통과
- [ ] 인덱싱 성공
- [ ] RAG 질의 응답 확인
- [ ] 자동 동기화 작동 확인

---

## 📝 다음 단계

### 즉시 실행

1. **의존성 설치**
   ```bash
   cd ${HOME}/AFO/scripts/rag
   pip install -r requirements.txt
   ```

2. **초기 인덱싱**
   ```bash
   python index_obsidian_to_qdrant.py --clear
   ```

3. **테스트**
   ```bash
   python rag_graph.py
   ```

### 운영 설정

1. **자동 동기화 서비스화**
   - systemd 서비스 등록
   - 백그라운드 실행

2. **모니터링**
   - 동기화 로그 확인
   - 인덱싱 상태 모니터링

---

**상태**: ✅ 구현 완료  
**다음 단계**: 의존성 설치 및 초기 인덱싱 실행

