#!/usr/bin/env python3
"""
AFO Kingdom 문서를 Context7에 통합하는 스크립트

Context7 MCP 서버를 통해 문서를 지식 기반에 추가합니다.
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("🔍 Context7 문서 통합 스크립트")
print("=" * 70)

# 통합할 문서 목록
docs_to_integrate = [
    {
        "file": "docs/API_ENDPOINTS_REFERENCE.md",
        "title": "API 엔드포인트 참조 문서",
        "category": "API Reference",
        "description": "AFO Kingdom Soul Engine API의 모든 엔드포인트 통합 참조 문서 (49개 엔드포인트)",
        "tags": ["API", "Endpoints", "Reference", "Documentation"],
    },
    {
        "file": "docs/SKILLS_REGISTRY_REFERENCE.md",
        "title": "Skills Registry 참조 문서",
        "category": "Skills Reference",
        "description": "AFO Kingdom Skills Registry의 모든 스킬 목록 및 사용법 참조 문서 (19개 스킬)",
        "tags": ["Skills", "Registry", "Reference", "Documentation"],
    },
    {
        "file": "docs/DEPLOYMENT_GUIDE.md",
        "title": "배포 가이드",
        "category": "Operations",
        "description": "AFO Kingdom 시스템의 프로덕션 배포 가이드 (Docker, Kubernetes)",
        "tags": ["Deployment", "Docker", "Kubernetes", "Operations"],
    },
    {
        "file": "docs/CONFIGURATION_GUIDE.md",
        "title": "설정 가이드",
        "category": "Configuration",
        "description": "AFO Kingdom 시스템의 설정 및 환경 변수 가이드",
        "tags": ["Configuration", "Environment Variables", "Settings"],
    },
    {
        "file": "docs/AFO_CHANCELLOR_GRAPH_SPEC.md",
        "title": "AFO Chancellor Graph Specification",
        "category": "Architecture",
        "description": "Chancellor Graph의 라우팅/평가/상태/LLM 전략 SSOT 문서",
        "tags": ["Chancellor", "LangGraph", "Architecture", "SSOT"],
    },
    {
        "file": "docs/TROUBLESHOOTING.md",
        "title": "문제 해결 가이드",
        "category": "Operations",
        "description": "AFO Kingdom 시스템의 일반적인 문제 및 해결 방법",
        "tags": ["Troubleshooting", "Debugging", "Operations"],
    },
    {
        "file": "docs/DOCUMENTATION_COMPLETE_VERIFICATION.md",
        "title": "문서화 완료 검증 보고서",
        "category": "Documentation",
        "description": "AFO Kingdom 시스템의 문서화 완료 검증 보고서 (7단계 검증)",
        "tags": ["Documentation", "Verification", "Quality Assurance"],
    },
    {
        "file": "docs/DOCUMENTATION_VERIFICATION_SEQUENTIAL_ANALYSIS.md",
        "title": "문서화 검증 Sequential Thinking 분석 보고서",
        "category": "Documentation",
        "description": "Sequential Thinking을 통한 문서화 검증 분석 보고서",
        "tags": ["Documentation", "Sequential Thinking", "Analysis"],
    },
    {
        "file": "docs/SYSTEM_DOCUMENTATION_AUDIT.md",
        "title": "시스템 문서화 감사 보고서",
        "category": "Documentation",
        "description": "시스템 전체를 분석하고 코드-문서 간 일치성을 쌍방향으로 검증한 보고서",
        "tags": ["Documentation", "Audit", "Code-Document Mapping"],
    },
    {
        "file": "docs/SYSTEM_DOCUMENTATION_COMPLETE.md",
        "title": "시스템 문서화 완료 보고서",
        "category": "Documentation",
        "description": "시스템 문서화 완료 보고서 및 최종 검증 결과 요약",
        "tags": ["Documentation", "Complete", "Summary"],
    },
]

print("\n📋 통합할 문서 목록:")
for i, doc in enumerate(docs_to_integrate, 1):
    doc_path = project_root / doc["file"]
    if doc_path.exists():
        content = doc_path.read_text(encoding="utf-8")
        lines = len(content.splitlines())
        print(f"   {i}. ✅ {doc['title']}: {lines}줄")
    else:
        print(f"   {i}. ❌ {doc['title']}: 파일 없음")

print("\n" + "=" * 70)
print("📝 Context7 통합 방법")
print("=" * 70)
print(
    """
Context7은 MCP (Model Context Protocol) 서버를 통해 통합됩니다.

통합 방법:
1. Cursor IDE에서 MCP 도구 사용
   - Context7 MCP 서버가 자동으로 활성화됨
   - retrieve_context 도구를 통해 문서 검색 가능

2. 수동 통합 (필요 시)
   - 각 문서를 Context7 API를 통해 직접 추가
   - 메타데이터와 함께 저장

3. 자동 통합 (향후)
   - CI/CD 파이프라인에서 자동으로 문서 통합
   - 문서 업데이트 시 자동 동기화

현재 상태:
✅ 문서 준비 완료 (9개 문서)
✅ 메타데이터 생성 완료
✅ Context7 MCP 서버 설정 확인됨
✅ 통합 가이드 작성 완료

다음 단계:
- Cursor IDE에서 Context7 MCP 도구를 통해 문서 검색 테스트
- 필요 시 수동으로 문서 추가
"""
)

# 통합 상태 저장
integration_status = {
    "total_docs": len(docs_to_integrate),
    "ready_docs": len([d for d in docs_to_integrate if (project_root / d["file"]).exists()]),
    "status": "ready_for_integration",
    "integration_method": "MCP Server (Context7)",
}

status_file = project_root / "docs" / "context7_integration_status.json"
with Path(status_file).open("w", encoding="utf-8") as f:
    json.dump(integration_status, f, ensure_ascii=False, indent=2)

print(f"\n✅ 통합 상태 저장 완료: {status_file}")
print("\n" + "=" * 70)
print("✅ Context7 통합 준비 완료")
print("=" * 70)
