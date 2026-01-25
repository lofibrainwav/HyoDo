# 🚀 RAG 시스템 설치 가이드

**목적**: 옵시디언 vault → RAG GoT 연결 시스템 설치 방법

---

## 📋 사전 요구사항

### 필수

- Python 3.12+
- Qdrant 서버 실행 중
- OpenAI API 키

### 선택적

- Git 저장소 (커밋/푸시용)

---

## 🔧 설치 방법

### 방법 1: 사용자 설치 (권장)

```bash
cd /Users/brnestrm/AFO/scripts/rag
pip install --user -r requirements.txt
```

### 방법 2: 가상환경 사용

```bash
cd /Users/brnestrm/AFO/scripts/rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 방법 3: 시스템 패키지 (주의)

```bash
pip install --break-system-packages -r requirements.txt
```

---

## ✅ 설치 확인

```bash
python3 -c "import frontmatter, langchain, langchain_openai, langchain_qdrant, langgraph, qdrant_client, watchdog; print('✅ 모든 의존성 설치 완료')"
```

---

## 🧪 테스트

```bash
# 전체 시스템 테스트
python test_rag_system.py

# 연결 상태 검증
python verify_rag_connection.py
```

---

## 📝 환경 변수 설정

```bash
export OPENAI_API_KEY="your-api-key"
export QDRANT_URL="http://localhost:6333"
```

---

## 🚀 초기 인덱싱

```bash
python index_obsidian_to_qdrant.py --clear
```

---

**상태**: ✅ 가이드 생성 완료

