from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import Union

import httpx
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant

from AFO.config.settings import get_settings

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.

#!/usr/bin/env python3
"""
n8n 워크플로우 정보를 AFO RAG 시스템에 추가하는 스크립트

사용법:
    python add_n8n_workflow_to_rag.py
"""


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# 환경 변수 로드
load_dotenv(ENV_FILE)

# LangChain 및 Qdrant 임포트 (ChromaDB → Qdrant 마이그레이션)
try:
    pass  # Placeholder
except ImportError:
    print("❌ 필수 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install langchain-qdrant langchain-openai")
    sys.exit(1)

# OpenAI API 키 확인
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

# Qdrant 설정 (ChromaDB → Qdrant 마이그레이션) - 중앙 설정 사용 (Phase 1 리팩토링)
try:
    QDRANT_URL = get_settings().QDRANT_URL
except ImportError:
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = "afo_workflows"


def create_workflow_document() -> None:
    """워크플로우 정보를 문서로 변환"""

    workflow_info = """
# Daily Notion Report 워크플로우

## 워크플로우 개요
- **이름**: Daily Notion Report
- **ID**: ySdajIsal2qX42ws
- **목적**: 매일 오전 8시에 vibecodehub Notion 데이터베이스에서 최신 항목을 조회하여 이메일로 리포트 발송
- **상태**: 활성 (active)

## 워크플로우 구조

### 노드 구성
1. **Cron 트리거** (n8n-nodes-base.cron)
   - 매일 오전 8시 실행
   - ID: ae8048d1-a3ca-4a05-b87b-237bb0fcf665

2. **Notion 노드** (n8n-nodes-base.notion)
   - 이름: Notion Query Vibecodehub
   - ID: f28a3b3b-016c-41bd-8c65-fc530adfab02
   - Resource: database
   - Operation: query
   - Database ID: `={{ $env.NOTION_DATABASE_ID }}` (환경변수 사용)
   - Filter: Status가 "ready"인 항목만
   - Sort: Detected At 내림차순
   - Limit: 10개
   - Credentials: Notion account (cMos2WhTNziGYmtC)

3. **Email 노드** (n8n-nodes-base.emailSend)
   - ID: 610b35f7-1a87-452e-b7c6-20fa742689fb
   - From: report@yourdomain.com
   - To: team@yourdomain.com
   - Subject: Daily Notion Report - {{ $now.toISODate() }}
   - Body: {{ $Union[json, json] }}

## 연결 구조
Cron → Notion → Email

## 주요 설정

### Notion 노드 설정 (vibecodehub 연결)
```json
{
  "resource": "database",
  "operation": "query",
  "databaseId": "={{ $env.NOTION_DATABASE_ID }}",
  "filter": {
    "property": "Status",
    "select": {"equals": "ready"}
  },
  "sort": [{"property": "Detected At", "direction": "descending"}],
  "limit": 10
}
```

### 환경변수 필요
- `NOTION_DATABASE_ID`: vibecodehub 데이터베이스 ID

## API 업데이트 방법

### Python으로 업데이트
```python

N8N_URL = os.getenv('N8N_URL')
API_KEY = os.getenv('API_YUNGDEOK')
headers = {'X-N8N-API-KEY': API_KEY, 'Accept': 'application/json'}

# 워크플로우 가져오기
response = httpx.get(f'{N8N_URL}/api/v1/workflows/ySdajIsal2qX42ws', headers=headers)
workflow = response.json()

# Notion 노드 수정
for node in workflow['nodes']:
    if node['id'] == 'f28a3b3b-016c-41bd-8c65-fc530adfab02':
        node['parameters'] = {
            'resource': 'database',
            'operation': 'query',
            'databaseId': '={{ $env.NOTION_DATABASE_ID }}',
            # ... 필터 및 정렬 설정
        }
        break

# 업데이트 (active 필드 제외)
payload = {
    'name': workflow['name'],
    'nodes': workflow['nodes'],
    'connections': workflow['connections'],
    'settings': workflow.get('settings', {})
}

response = httpx.put(
    f'{N8N_URL}/api/v1/workflows/ySdajIsal2qX42ws',
    headers={**headers, 'Content-Type': 'application/json'},
    json=payload
)
```

## Playwright 브라우저 자동화

### 로그인 및 워크플로우 접근
1. n8n URL로 이동: https://n8n.brnestrm.com
2. 이메일/비밀번호로 로그인
3. 워크플로우 편집 페이지로 이동

### 노드 설정 변경
- 노드를 클릭하면 오른쪽에 설정 패널이 열림
- Resource를 "Database"로 변경
- Operation을 "Query"로 변경
- Database ID 필드를 Expression 모드로 전환하여 환경변수 입력

### 주의사항
- 브라우저 자동화보다 API 업데이트가 더 안정적
- API는 read-only 필드(`active`, `id`, `versionId` 등) 제외 필요
- 설정 패널이 자동으로 열리지 않으면 JavaScript로 직접 조작 시도

## 모듈화 계획

### Sub-workflow 후보
1. **Input Validation**: 입력 데이터 검증 및 정규화
2. **Retry Handler**: 에러 발생 시 재시도 로직
3. **Documentation**: 워크플로우 문서화

## 참고 자료
- 워크플로우 백업: `n8n_workflows/modularized/Daily_Notion_Report_ySdajIsal2qX42ws_backup.json`
- 모듈화 버전: `n8n_workflows/modularized/Daily_Notion_Report_With_Vibecodehub.json`
- 업데이트 가이드: `n8n_workflows/modularized/Daily_Notion_Report_Vibecodehub_Update.md`
"""

    return Document(
        page_content=workflow_info,
        metadata={
            "source": "n8n_workflow",
            "workflow_id": "ySdajIsal2qX42ws",
            "workflow_name": "Daily Notion Report",
            "type": "workflow_documentation",
            "category": "automation",
            "tags": ["n8n", "notion", "vibecodehub", "daily-report", "automation"],
            "created_at": "2025-01-11",
            "updated_at": "2025-01-11",
        },
    )


def add_to_rag() -> None:
    """워크플로우 문서를 Qdrant에 추가 (ChromaDB → Qdrant 마이그레이션)"""

    print("📚 n8n 워크플로우 정보를 RAG 시스템에 추가 중...")
    print(f"   Qdrant URL: {QDRANT_URL}")
    print(f"   컬렉션: {COLLECTION_NAME}")

    # 임베딩 생성
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # 워크플로우 문서 생성
    workflow_doc = create_workflow_document()

    try:
        # Qdrant에 문서 추가 (기존 컬렉션이 있으면 자동으로 사용)
        vectorstore = Qdrant.from_documents(
            documents=[workflow_doc],
            embedding=embeddings,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            api_key=QDRANT_API_KEY,
            force_recreate=False,  # 기존 컬렉션 유지
        )
        print(f"✅ Qdrant 컬렉션 '{COLLECTION_NAME}' 준비 완료")

        print("✅ 워크플로우 문서 추가 완료!")
        print(f"   컬렉션: {COLLECTION_NAME}")
        print(f"   문서 ID: {workflow_doc.metadata['workflow_id']}")
        print(f"   Qdrant URL: {QDRANT_URL}")

        # 검색 테스트
        print("\n🔍 검색 테스트 중...")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
        test_results = retriever.get_relevant_documents("Daily Notion Report 워크플로우")

        if test_results:
            print(f"✅ 검색 성공: {len(test_results)}개 문서 발견")
            print(f"   첫 번째 결과: {test_results[0].metadata.get('workflow_name', 'N/A')}")
        else:
            print("⚠️ 검색 결과가 없습니다.")

        return vectorstore

    except Exception as e:
        print(f"❌ Qdrant 연결 실패: {e}")
        print("   Qdrant 서비스가 실행 중인지 확인하세요: docker Union[ps, grep] qdrant")
        raise


def main() -> None:
    """메인 함수"""
    try:
        add_to_rag()
        print("\n✅ 완료! 이제 RAG 시스템에서 워크플로우 정보를 검색할 수 있습니다.")
        print("\n사용 예시:")
        print("  - 'Daily Notion Report 워크플로우는 어떻게 구성되어 있나요?'")
        print("  - 'vibecodehub 연결 방법은?'")
        print("  - 'n8n 노드 설정을 Playwright로 자동화하려면?'")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
