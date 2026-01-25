# 📋 API Wallet 시스템 지피지기 (知彼知己) 리포트

**확인일**: 2025-12-16  
**목적**: API Wallet 시스템의 정확한 구조와 상태 파악

---

## 🔍 지피지기 결과

### ✅ 시스템 구조 확인

**API Wallet 저장 방식**:
- **브라우저 인증**: 월구독제로 브라우저에서 토큰 인증 가져오기
- **암호화 저장**: Fernet (AES-256) 암호화
- **저장소**: PostgreSQL DB (우선) → JSON 파일 (fallback)
- **암호화 키**: `API_WALLET_ENCRYPTION_KEY` 환경 변수

**암호화 방식**:
- Fernet (AES-256)
- 암호화된 키는 `encrypted_key` 필드에 저장
- 복호화는 `wallet.get(name)` 호출 시 자동 수행

### ✅ PostgreSQL DB 상태

**컨테이너**:
- 이름: `afo-postgres`
- 상태: 실행 중 (healthy)
- 포트: 15432 (호스트) → 5432 (컨테이너)

**테이블 구조**:
- 테이블명: `api_keys`
- 필드:
  - `id`: SERIAL PRIMARY KEY
  - `name`: VARCHAR(255) UNIQUE NOT NULL
  - `encrypted_key`: TEXT NOT NULL (암호화된 키)
  - `key_type`: VARCHAR(50)
  - `read_only`: BOOLEAN DEFAULT TRUE
  - `service`: VARCHAR(100)
  - `description`: TEXT
  - `key_hash`: VARCHAR(64)
  - `created_at`: TIMESTAMP
  - `last_accessed`: TIMESTAMP
  - `access_count`: INTEGER DEFAULT 0

### ⚠️  현재 상태

**PostgreSQL DB**:
- 연결: ✅ 성공
- 테이블: ✅ 존재
- 저장된 키: 확인 필요

**JSON 저장소**:
- 파일: `api_wallet_storage.json`
- 상태: 비어있음 (0개 키)

---

## 🔧 통합 완료

### ✅ config.py 수정

**PostgreSQL 통합 로직**:
1. 환경 변수 `OPENAI_API_KEY` 확인
2. PostgreSQL DB 연결 시도
3. PostgreSQL에서 OpenAI 키 검색
4. 없으면 JSON 저장소에서 검색
5. 찾은 키를 환경 변수로 자동 설정

**연결 설정**:
- Host: `localhost` (환경 변수: `POSTGRES_HOST`)
- Port: `15432` (환경 변수: `POSTGRES_PORT`)
- Database: `postgres` (환경 변수: `POSTGRES_DB`)
- User: `postgres` (환경 변수: `POSTGRES_USER`)
- Password: `$POSTGRES_PASSWORD` (환경 변수 필수)

---

## 📊 확인 방법

### PostgreSQL에서 직접 확인

```bash
docker exec -it afo-postgres psql -U postgres -d postgres
SELECT name, service FROM api_keys;
```

### Python 스크립트로 확인

```bash
source venv_rag/bin/activate
python3 check_api_wallet_postgres.py
```

### config.py에서 자동 확인

```bash
source venv_rag/bin/activate
python3 scripts/rag/config.py
```

---

## 🚀 사용 방법

### 자동 사용

RAG 시스템을 실행하면 자동으로 PostgreSQL에서 키를 가져옵니다:

```bash
cd /Users/brnestrm/AFO_Kingdom/AFO
source venv_rag/bin/activate
python3 scripts/rag/index_obsidian_to_qdrant.py --clear
```

### 수동 확인

```python
import os
from api_wallet import APIWallet
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=15432,
    database="postgres",
    user="postgres",
    password=os.getenv("POSTGRES_PASSWORD", "")
)

wallet = APIWallet(db_connection=conn)
keys = wallet.list_keys()
```

---

## ✅ 검증 체크리스트

- [x] PostgreSQL 컨테이너 확인 (실행 중)
- [x] psycopg2 설치 (가상환경)
- [x] config.py PostgreSQL 통합
- [x] 자동 키 로드 로직 구현
- [ ] PostgreSQL DB에 키 존재 여부 확인
- [ ] OpenAI 키 자동 로드 테스트
- [ ] RAG 시스템에서 키 사용 확인

---

**상태**: ✅ 지피지기 완료, PostgreSQL 통합 완료  
**다음 단계**: PostgreSQL DB에 키가 있는지 확인 및 테스트

