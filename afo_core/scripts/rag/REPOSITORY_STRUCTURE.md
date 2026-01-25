# 📁 리포지토리 구조 및 경로 설정

**목적**: 리포지토리 분리 후 경로 자동 감지 및 설정

---

## 🔧 경로 자동 감지

RAG 시스템은 `config.py`를 통해 경로를 자동으로 감지합니다:

1. **리포지토리 루트**: `scripts/rag/config.py` 기준 상위 3단계
2. **옵시디언 vault**: `{repo_root}/docs`
3. **동기화 상태 파일**: `{repo_root}/.obsidian_sync_state.json`

---

## 📋 환경 변수 오버라이드

다음 환경 변수로 경로를 오버라이드할 수 있습니다:

```bash
# 리포지토리 루트
export AFO_REPO_ROOT="/path/to/repo"

# 옵시디언 vault 경로
export OBSIDIAN_VAULT_PATH="/path/to/vault"

# Qdrant URL
export QDRANT_URL="http://localhost:6333"
```

---

## 🔄 리포지토리 분리 대응

### AFO 리포지토리

- **위치**: `/Users/brnestrm/AFO` 또는 `AFO_Kingdom/AFO`
- **옵시디언 vault**: `{repo_root}/docs`
- **RAG 스크립트**: `{repo_root}/scripts/rag/`

### SixXon 리포지토리

- **위치**: `AFO_Kingdom/SixXon` 또는 별도 위치
- **옵시디언 vault**: 필요 시 환경 변수로 설정

---

## ✅ 검증

```bash
# 설정 확인
python config.py

# 전체 시스템 테스트
python test_rag_system.py

# 연결 상태 검증
python verify_rag_connection.py
```

---

**상태**: ✅ 경로 자동 감지 구현 완료

