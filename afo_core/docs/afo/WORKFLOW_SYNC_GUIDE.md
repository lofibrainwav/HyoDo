# 🔄 AFO 왕국 워크플로우 동기화 가이드

**최종 업데이트**: 2025-12-16
**목적**: 지갑 시스템과 학자 시스템 간의 완벽한 동기화

---

## 🚀 빠른 시작

### 원클릭 동기화
```bash
cd /Users/brnestrm/AFO_Kingdom/AFO
./scripts/sync_workflow.sh
```

이 명령 하나로 다음이 자동으로 수행됩니다:
1. 지갑에서 API 키 추출
2. 환경 변수 자동 설정
3. 시스템 검증 (API 서버, OpenAI, PostgreSQL)

---

## 📋 수동 동기화

### Step 1: 키 추출
```bash
cd /Users/brnestrm/AFO_Kingdom/AFO
python3 scripts/export_keys.py > /tmp/afo_env_keys.sh
```

### Step 2: 환경 변수 로드
```bash
source /tmp/afo_env_keys.sh
```

### Step 3: 검증
```bash
# OpenAI API 키 확인
python3 -c "from langchain_openai import OpenAIEmbeddings; e = OpenAIEmbeddings(); print('✅ OK')"

# PostgreSQL 연결 확인
psql -h localhost -p 15432 -U afo -d afo_memory -c "SELECT 1;"

# API 서버 건강 상태
curl http://localhost:8010/health
```

---

## 🔧 환경 변수 관리

### 현재 설정된 키
- `OPENAI_API_KEY`: OpenAI API 키
- `ANTHROPIC_API_KEY`: Anthropic API 키

### 키 갱신
지갑에서 키를 변경한 경우:
```bash
./scripts/sync_workflow.sh
```

---

## 📊 시스템 상태 확인

### API 서버 건강 상태
```bash
curl http://localhost:8010/health | python3 -m json.tool
```

**정상 상태**:
- `health_percentage`: 100%
- `status`: "balanced"
- 모든 장기: "healthy"

### 지갑 상태
```bash
curl http://localhost:8010/api/wallet/keys | python3 -m json.tool
```

---

## 🎯 사용 시나리오

### 시나리오 1: 매일 아침 시작
```bash
cd /Users/brnestrm/AFO_Kingdom/AFO
./scripts/sync_workflow.sh
source /tmp/afo_env_keys_clean.sh
```

### 시나리오 2: 새로운 터미널 세션
```bash
source /tmp/afo_env_keys_clean.sh
```

### 시나리오 3: RAG 시스템 사용
```bash
cd /Users/brnestrm/AFO/scripts/rag
source /tmp/afo_env_keys_clean.sh
python3 rag_graph.py
```

---

## ⚠️ 문제 해결

### 환경 변수가 설정되지 않음
```bash
# 키 재추출
python3 scripts/export_keys.py > /tmp/afo_env_keys.sh
source /tmp/afo_env_keys.sh

# 확인
echo $OPENAI_API_KEY
```

### API 서버 연결 실패
```bash
# 서버 재시작
cd /Users/brnestrm/AFO_Kingdom
python3 -m AFO.api_server > AFO/api_server.log 2>&1 &
```

### PostgreSQL 연결 실패
```bash
# Docker 컨테이너 확인
docker ps | grep postgres

# 포트 확인
lsof -i :15432
```

---

## 📝 참고 문서

- [하이브리드 전략 완료](./HYBRID_STRATEGY_COMPLETE.md)
- [문서 인덱스](./DOCUMENTATION_INDEX.md)
- [스크립트 가이드](../scripts/README.md)

---

**상태**: ✅ 워크플로우 가이드 생성 완료
