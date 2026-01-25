"""AI Prompt Builder for Diagram Generation (PH-SE-09.01)

Advanced AI prompt generation with context awareness and domain optimization.

Trinity Score: 眞 95% | 善 90% | 美 95%
- 眞 (Truth): Context-aware prompt construction
- 善 (Goodness): Quality requirements enforcement
- 美 (Beauty): Domain-specific templates
"""

from __future__ import annotations

from typing import Any


class AIPromptBuilder:
    """AI 프롬프트 빌더.

    다이어그램 생성을 위한 고급 AI 프롬프트를 구성합니다.
    """

    def build_prompt(self, description: str, diagram_type: str) -> str:
        """고급 AI 프롬프트 생성 (PH-SE-09.01).

        컨텍스트 인식, 도메인별 최적화, 품질 검증 포함.

        Args:
            description: 사용자 설명
            diagram_type: 다이어그램 유형

        Returns:
            고급 AI 프롬프트
        """
        # 컨텍스트 분석
        context = self.analyze_description_context(description)

        # 도메인별 프롬프트 템플릿 선택
        domain_template = self.get_domain_specific_template(context["domain"], diagram_type)

        # 품질 요구사항 설정
        quality_requirements = self.get_quality_requirements(diagram_type, context)

        # 메인 프롬프트 구성
        prompt_parts = [
            self.get_system_prompt(),
            self.get_task_prompt(description, diagram_type, context),
            self.get_format_specification(),
            self.get_quality_guidelines(quality_requirements),
            domain_template,
            self.get_examples_section(diagram_type, context),
        ]

        return "\n\n".join(filter(None, prompt_parts))

    def analyze_description_context(self, description: str) -> dict[str, Any]:
        """설명 텍스트의 컨텍스트 분석.

        Args:
            description: 사용자 설명

        Returns:
            컨텍스트 정보 딕셔너리
        """
        context = {
            "domain": "general",
            "complexity": "simple",
            "pillars": [],
            "keywords": [],
            "language": "ko",  # 기본 한국어
            "technical_level": "intermediate",
        }

        desc_lower = description.lower()

        # 도메인 감지
        domain_keywords = {
            "software": [
                "api",
                "database",
                "server",
                "client",
                "microservice",
                "frontend",
                "backend",
            ],
            "business": ["process", "workflow", "customer", "order", "payment", "inventory"],
            "system": ["architecture", "infrastructure", "network", "security", "deployment"],
            "data": ["entity", "relationship", "table", "schema", "model"],
        }

        for domain, keywords in domain_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                context["domain"] = domain
                break

        # 복잡성 분석
        if len(description.split()) > 100 or "complex" in desc_lower or "advanced" in desc_lower:
            context["complexity"] = "complex"
        elif len(description.split()) < 20:
            context["complexity"] = "simple"
        else:
            context["complexity"] = "intermediate"

        # 5기둥 키워드 감지
        pillar_keywords = {
            "truth": ["accuracy", "validation", "verification", "truth", "眞", "진실"],
            "goodness": ["security", "reliability", "stability", "ethics", "善", "선"],
            "beauty": ["design", "ux", "ui", "aesthetics", "美", "미"],
            "serenity": ["calm", "peace", "harmony", "孝", "효"],
            "eternity": ["sustainability", "longevity", "future", "永", "영"],
        }

        for pillar, keywords in pillar_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                context["pillars"].append(pillar)

        # 기술 수준 감지
        if any(word in desc_lower for word in ["beginner", "basic", "simple"]):
            context["technical_level"] = "beginner"
        elif any(word in desc_lower for word in ["expert", "advanced", "complex"]):
            context["technical_level"] = "expert"

        return context

    def get_system_prompt(self) -> str:
        """시스템 프롬프트."""
        return """당신은 AFO 왕국의 전문 다이어그램 아키텍트입니다.

眞善美孝永 철학에 기반하여 다이어그램을 설계합니다:
- 眞 (Truth): 정확성과 기술적 타당성
- 善 (Goodness): 안정성과 윤리적 고려
- 美 (Beauty): 심미성과 사용자 경험
- 孝 (Serenity): 평온함과 조화
- 永 (Eternity): 지속가능성과 미래 지향성

최고 품질의 다이어그램을 생성하는 것을 목표로 합니다."""

    def get_task_prompt(self, description: str, diagram_type: str, context: dict[str, Any]) -> str:
        """작업별 프롬프트."""
        complexity_instruction = {
            "simple": "간단하고 명확한 구조로 유지하세요.",
            "intermediate": "적절한 세부 수준으로 균형을 맞추세요.",
            "complex": "상세한 구조를 유지하면서도 이해하기 쉽게 정리하세요.",
        }

        domain_instruction = {
            "software": "소프트웨어 엔지니어링 모범 사례를 따르세요.",
            "business": "비즈니스 프로세스 표준을 고려하세요.",
            "system": "시스템 아키텍처 원칙을 적용하세요.",
            "data": "데이터 모델링 표준을 준수하세요.",
            "general": "일반적인 다이어그램 설계 원칙을 따르세요.",
        }

        return f"""다음 설명을 분석하여 {diagram_type} 다이어그램을 생성하세요:

설명: {description}

컨텍스트 분석:
- 도메인: {context["domain"]}
- 복잡성: {context["complexity"]}
- 감지된 기둥: {", ".join(context["pillars"]) if context["pillars"] else "없음"}

지침:
- {complexity_instruction[context["complexity"]]}
- {domain_instruction[context["domain"]]}
- 감지된 5기둥을 적절히 반영하세요.
- 기술 수준 ({context["technical_level"]})에 맞는 용어를 사용하세요."""

    def get_format_specification(self) -> str:
        """출력 형식 명세."""
        return """다음 JSON 형식으로 정확히 응답하세요:

{
  "title": "다이어그램 제목",
  "description": "다이어그램에 대한 간단한 설명",
  "domain": "도메인 분류",
  "complexity": "simple|intermediate|complex",
  "pillars": ["감지된 5기둥 배열"],
  "confidence": 0.0-1.0,
  "nodes": [
    {
      "id": "고유_식별자",
      "label": "노드 라벨",
      "type": "process|decision|data|actor|database|start|end|connector",
      "pillar": "眞|善|美|孝|永" (선택적),
      "description": "노드에 대한 상세 설명",
      "metadata": {
        "domain_specific": "도메인별 추가 정보"
      }
    }
  ],
  "connections": [
    {
      "id": "연결_고유_ID",
      "from": "출발_노드_ID",
      "to": "도착_노드_ID",
      "label": "연결 라벨",
      "type": "flow|dependency|inheritance|association|composition",
      "description": "연결에 대한 설명"
    }
  ],
  "layout": {
    "type": "hierarchical|circular|grid|organic",
    "direction": "top-bottom|left-right|radial",
    "rankSeparation": 100,
    "nodeSeparation": 50
  },
  "quality_metrics": {
    "completeness": 0.0-1.0,
    "consistency": 0.0-1.0,
    "clarity": 0.0-1.0
  }
}"""

    def get_quality_guidelines(self, requirements: dict[str, Any]) -> str:
        """품질 가이드라인."""
        return f"""품질 요구사항 준수:
- 완전성: {requirements.get("completeness", 0.8)} 이상
- 일관성: {requirements.get("consistency", 0.8)} 이상
- 명확성: {requirements.get("clarity", 0.8)} 이상
- 최대 노드 수: {requirements.get("max_nodes", 15)}개
- 최대 연결 수: {requirements.get("max_connections", 20)}개

품질 검증 항목:
1. 모든 노드에 고유 ID 부여
2. 연결이 유효한 노드를 참조
3. 레이블이 명확하고 간결
4. 5기둥이 논리적으로 배치
5. 레이아웃이 가독성 좋음"""

    def get_domain_specific_template(self, domain: str, diagram_type: str) -> str:
        """도메인별 특화 템플릿."""
        templates = {
            "software": {
                "flow": """
소프트웨어 플로우 다이어그램 특화:
- API 호출은 별도 노드로 표현
- 데이터베이스 상호작용 명시
- 에러 처리 경로 포함
- 비동기 작업 표시""",
                "architecture": """
소프트웨어 아키텍처 특화:
- 마이크로서비스 경계 명확히 구분
- 데이터 흐름 방향 표시
- 확장성 고려한 구조
- 보안 컴포넌트 포함""",
            },
            "business": {
                "flow": """
비즈니스 프로세스 특화:
- 역할별 책임 구분 (담당자, 시스템, 외부)
- 의사결정 포인트 명확히 표시
- SLA 및 품질 요구사항 반영
- 예외 처리 시나리오 포함""",
            },
            "data": {
                "erd": """
데이터 모델링 특화:
- 엔티티 관계 정확히 표현
- 카디널리티 표준 준수 (1:1, 1:N, N:M)
- 정규화 원칙 적용
- 비즈니스 규칙 반영""",
            },
        }

        return templates.get(domain, {}).get(diagram_type, "")

    def get_quality_requirements(
        self, diagram_type: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """품질 요구사항 설정."""
        base_requirements = {
            "completeness": 0.8,
            "consistency": 0.8,
            "clarity": 0.8,
            "max_nodes": 15,
            "max_connections": 20,
        }

        # 복잡성에 따른 조정
        if context["complexity"] == "simple":
            base_requirements.update({"max_nodes": 8, "max_connections": 10})
        elif context["complexity"] == "complex":
            base_requirements.update({"max_nodes": 20, "max_connections": 30})

        # 도메인별 조정
        domain_adjustments = {
            "software": {"completeness": 0.9, "consistency": 0.9},
            "data": {"consistency": 0.95, "clarity": 0.9},
            "business": {"clarity": 0.9, "completeness": 0.85},
        }

        if context["domain"] in domain_adjustments:
            base_requirements.update(domain_adjustments[context["domain"]])

        return base_requirements

    def get_examples_section(self, diagram_type: str, context: dict[str, Any]) -> str:
        """예제 섹션."""
        examples = {
            "flow": """
예시 구조:
단순 플로우: 시작 → 처리 → 종료
조건부 플로우: 시작 → 조건 → (예/아니오) → 각기 다른 종료
반복 플로우: 시작 → 처리 → 조건 → (반복/종료)""",
            "architecture": """
예시 구조:
웹 앱: 사용자 → 웹서버 → API → 데이터베이스
마이크로서비스: 게이트웨이 → 서비스A/B/C → 공유 데이터베이스""",
        }

        example = examples.get(diagram_type, "")
        if example:
            return f"참고 예시:\n{example}"

        return ""
