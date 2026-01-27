# 📜 AFO 왕국 스크립트 가이드

**목적**: AFO 왕국에서 사용하는 모든 스크립트의 사용법 및 설명

---

## 🔑 API 키 관리

### `export_keys.py`
지갑에서 API 키를 추출하여 환경 변수로 변환

**사용법**:
```bash
cd ./AFO
python3 scripts/export_keys.py > /tmp/afo_env_keys.sh
source /tmp/afo_env_keys.sh
```

**출력 예시**:
```bash
export OPENAI_API_KEY='...'
export ANTHROPIC_API_KEY='...'
```

---

## 🔄 워크플로우 동기화

### `sync_workflow.sh`
지갑에서 키 추출 → 환경 변수 설정 → 시스템 검증을 한 번에 수행

**사용법**:
```bash
cd ./AFO
./scripts/sync_workflow.sh
```

**기능**:
1. 지갑에서 API 키 추출
2. 환경 변수 자동 설정
3. 시스템 검증 (API 서버, OpenAI, PostgreSQL)

---

## 📚 RAG 시스템

RAG 관련 스크립트는 `scripts/rag/` 디렉토리에 있습니다.

자세한 내용은 `scripts/rag/README.md`를 참고하세요.

---

## 🔐 토큰 관리

### `export_tokens.sh`
세션 토큰 추출 (브라우저 인증용)

### `manual_add_token.py`
수동으로 토큰 추가

---

**상태**: ✅ 스크립트 가이드 생성 완료

