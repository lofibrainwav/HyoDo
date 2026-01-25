# 🔗 옵시디언 vault → RAG GoT 연결 시스템

**목적**: 옵시디언 vault를 RAG GoT(Guardians of Truth) 시스템에 연결

---

## 📋 구성 요소

### 1. 문서 로더 (`obsidian_loader.py`)
- 옵시디언 vault에서 Markdown 파일 로드
- Frontmatter 메타데이터 파싱
- 옵시디언 링크 추출 (`[[링크]]`)
- 태그 추출 (`#태그`)
- 카테고리 분류

### 2. 벡터 DB 인덱싱 (`index_obsidian_to_qdrant.py`)
- Qdrant 벡터 DB에 문서 인덱싱
- 텍스트 청킹 (chunk_size=1000, overlap=200)
- OpenAI 임베딩 생성
- 메타데이터 저장

### 3. RAG 파이프라인 (`rag_graph.py`)
- LangGraph를 사용한 RAG 워크플로우
- 문서 검색 → 답변 생성
- Qdrant 유사도 검색
- GPT-4o-mini 답변 생성

### 4. 자동 동기화 (`sync_obsidian_vault.py`)
- 파일 변경 감지 (watchdog)
- 자동 재인덱싱
- 상태 파일 관리

---

## 🚀 설치

### 1. 의존성 설치

```bash
cd /Users/brnestrm/AFO/scripts/rag
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
export OPENAI_API_KEY="your-api-key"
export QDRANT_URL="http://localhost:6333"
```

---

## 📝 사용 방법

### 1. 초기 인덱싱

```bash
python index_obsidian_to_qdrant.py --clear
```

### 2. RAG 질의

```bash
python rag_graph.py
```

### 3. 자동 동기화 시작

```bash
python sync_obsidian_vault.py --initial-sync
```

---

## 🔧 설정

### 환경 변수

- `OPENAI_API_KEY`: OpenAI API 키
- `QDRANT_URL`: Qdrant 서버 URL (기본: http://localhost:6333)

### 스크립트 파라미터

#### `index_obsidian_to_qdrant.py`
- `--vault-path`: 옵시디언 vault 경로
- `--qdrant-url`: Qdrant 서버 URL
- `--collection`: 컬렉션 이름
- `--clear`: 기존 데이터 삭제
- `--chunk-size`: 청크 크기 (기본: 1000)
- `--chunk-overlap`: 청크 오버랩 (기본: 200)

#### `sync_obsidian_vault.py`
- `--vault-path`: 옵시디언 vault 경로
- `--state-file`: 동기화 상태 파일 경로
- `--initial-sync`: 초기 동기화 실행

---

## 📊 아키텍처

```
옵시디언 Vault (docs/)
    ↓
ObsidianLoader
    ↓
텍스트 분할 (RecursiveCharacterTextSplitter)
    ↓
OpenAI Embeddings
    ↓
Qdrant Vector DB
    ↓
LangGraph RAG Pipeline
    ↓
질의응답
```

---

## 🔄 자동 동기화

### 동작 방식

1. **파일 변경 감지**: watchdog으로 실시간 모니터링
2. **변경 파일 추적**: MD5 해시로 변경 감지
3. **주기적 동기화**: 60초마다 변경사항 반영
4. **상태 저장**: `.obsidian_sync_state.json`에 해시 저장

### 동기화 조건

- Markdown 파일 변경/생성/삭제
- 60초 이상 경과
- 변경 파일이 있는 경우

---

## 📚 예시

### 문서 로드

```python
from obsidian_loader import ObsidianLoader

loader = ObsidianLoader("/Users/brnestrm/AFO/docs")
documents = loader.load_documents()
```

### RAG 질의

```python
from rag_graph import query_obsidian_vault

result = query_obsidian_vault("옵시디언 플러그인 최적화 결과는?")
print(result["answer"])
```

---

## ✅ 검증

### 인덱싱 확인

```bash
# Qdrant 컬렉션 확인
curl http://localhost:6333/collections/obsidian_vault
```

### 테스트 실행

```bash
# 문서 로더 테스트
python obsidian_loader.py

# RAG 파이프라인 테스트
python rag_graph.py
```

---

**상태**: ✅ 구현 완료  
**다음 단계**: 초기 인덱싱 실행 및 테스트

