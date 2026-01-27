# ✅ API Wallet PostgreSQL 통합 완료

**완료일**: 2025-12-16  
**상태**: ✅ PostgreSQL 통합 완료  
**목적**: API Wallet이 PostgreSQL DB에서 키를 자동으로 가져오도록 통합

---

## 📊 시스템 구조

### ✅ 확인된 구조

**API Wallet 저장 방식**:

- 브라우저에서 토큰 인증 가져오기 (월구독제)
- 암호화 저장 (Fernet/AES-256)
- PostgreSQL DB에 저장
- JSON 파일은 fallback

**암호화 방식**:

- Fernet (AES-256)
- 암호화 키: `API_WALLET_ENCRYPTION_KEY` 환경 변수
- 암호화된 키는 `encrypted_key` 필드에 저장

---

## 🔧 통합 완료 항목

### ✅ 1. config.py 수정

**변경 사항**:

- PostgreSQL 연결 로직 추가
- PostgreSQL → JSON 저장소 순서로 키 검색
- 자동으로 환경 변수 설정

**로직**:

1. 환경 변수 `OPENAI_API_KEY` 확인
2. PostgreSQL DB 연결 시도
3. PostgreSQL에서 OpenAI 키 검색
4. 없으면 JSON 저장소에서 검색
5. 찾은 키를 환경 변수로 자동 설정

### ✅ 2. PostgreSQL 연결 설정

**기본 설정**:

- Host: `localhost` (환경 변수: `POSTGRES_HOST`)
- Port: `15432` (환경 변수: `POSTGRES_PORT`)
- Database: `postgres` (환경 변수: `POSTGRES_DB`)
- User: `postgres` (환경 변수: `POSTGRES_USER`)
- Password: `$POSTGRES_PASSWORD` (환경 변수 필수)

---

## 🚀 사용 방법

### 자동 사용

RAG 시스템을 실행하면 자동으로 PostgreSQL에서 키를 가져옵니다:

```bash
cd ./AFO
source venv_rag/bin/activate
python3 scripts/rag/index_obsidian_to_qdrant.py --clear
```

### 환경 변수로 오버라이드

```bash
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="15432"
export POSTGRES_DB="postgres"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="<YOUR_SECURE_PASSWORD>"
```

---

## 📋 현재 상태

### ✅ 완료된 항목

1. **config.py 수정**: PostgreSQL 통합 완료
2. **자동 키 로드**: PostgreSQL → JSON 순서
3. **환경 변수 자동 설정**: 다른 모듈에서도 사용 가능

### ⚠️  확인 필요

1. **PostgreSQL DB에 키 존재 여부**: 확인 필요
2. **연결 정보**: 환경 변수 또는 기본값 사용

---

## 🔍 키 확인 방법

### PostgreSQL에서 직접 확인

```bash
docker exec -it afo-postgres psql -U postgres -d postgres
SELECT name, service FROM api_keys WHERE service ILIKE '%openai%';
```

### Python으로 확인

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

**상태**: ✅ PostgreSQL 통합 완료  
**다음 단계**: PostgreSQL DB에 키가 있는지 확인 및 테스트
