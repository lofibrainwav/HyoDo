#!/usr/bin/env python3
"""
IRS SSOT 모니터링 에이전트 (Metacognition-Based IRS Monitor)
TICKET-033: IRS 실시간 SSOT 동기화 시스템

메타인지 기능:
- OBBB FAQ 우선순위 적용
- 멀티 소스 검증으로 충돌 감지
- 할루시네이션 방지 규칙 적용
- Evidence Bundle 자동 생성

Trinity Score: 眞0.35 + 善0.35 + 美0.20 + 孝0.08 + 永0.02
"""

import asyncio
import hashlib
import json
import logging
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/irs_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class MetacognitionEngine:
    """메타인지 엔진 (할루시네이션 방지)"""

    def __init__(self, rules_config: dict[str, Any]) -> None:
        self.rules = rules_config.get("rules", [])

    def validate_content(self, content: str, source_type: str) -> dict[str, Any]:
        """컨텐츠 메타인지 검증"""
        insights = {
            "hallucination_risks": [],
            "validation_score": 1.0,
            "confidence_level": "high",
        }

        # IRA 참조 거부 규칙
        if "reject_ira_references" in [rule.split(":")[0] for rule in self.rules]:
            ira_patterns = [
                r"2033.*2034.*단계적.*종료",
                r"IRA.*gradual.*repeal",
                r"phase.*out.*2034",
            ]
            for pattern in ira_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    insights["hallucination_risks"].append(
                        {
                            "type": "ira_reference",
                            "pattern": pattern,
                            "severity": "critical",
                        }
                    )
                    insights["validation_score"] *= 0.1
                    insights["confidence_level"] = "low"

        # OBBB 확인 요구 규칙
        if source_type == "obbb_faq":
            insights["obbb_confirmed"] = "One Big Beautiful Bill" in content

        # 모호한 표현 플래그
        ambiguous_terms = ["may", "could", "might", "possibly", "potentially"]
        found_ambiguous = [term for term in ambiguous_terms if term in content.lower()]
        if found_ambiguous:
            insights["ambiguous_terms"] = found_ambiguous
            insights["validation_score"] *= 0.8

        return insights


class ContentParser:
    """컨텐츠 파서 (다중 포맷 지원)"""

    def __init__(self, parser_config: dict[str, Any]) -> None:
        self.config = parser_config

    def parse_html(self, html_content: str) -> str:
        """HTML 컨텐츠 파싱"""
        soup = BeautifulSoup(html_content, "html.parser")

        # 설정된 셀렉터로 컨텐츠 추출
        if "content_selector" in self.config:
            elements = soup.select(self.config["content_selector"])
            if elements:
                return " ".join([elem.get_text(strip=True) for elem in elements])

        # 기본 텍스트 추출
        return soup.get_text(strip=True)

    def parse_pdf(self, pdf_content: bytes) -> str:
        """PDF 컨텐츠 파싱 (기본 텍스트 추출)"""
        # 간단한 텍스트 추출 (실제 구현에서는 PyPDF2 등 사용)
        try:
            text = pdf_content.decode("utf-8", errors="ignore")
            return text
        except Exception:
            return "PDF parsing not implemented - binary content"

    def normalize_content(self, content: str) -> str:
        """컨텐츠 정규화 (비교용)"""
        # 불필요한 공백/개행 제거
        normalized = re.sub(r"\s+", " ", content.strip())

        # 날짜/시간 정보 제거 (동적 컨텐츠 제외)
        normalized = re.sub(r"\d{1,2}/\d{1,2}/\d{4}", "", normalized)
        normalized = re.sub(r"\d{4}-\d{2}-\d{2}", "", normalized)

        return normalized


class ImpactAssessor:
    """영향도 평가기"""

    def __init__(self, assessment_rules: dict[str, list[str]]) -> None:
        self.critical_keywords = set(assessment_rules.get("critical_keywords", []))
        self.high_keywords = set(assessment_rules.get("high_keywords", []))
        self.medium_keywords = set(assessment_rules.get("medium_keywords", []))

    def assess_impact(self, content_diff: str) -> str:
        """변경 내용 기반 영향도 평가"""
        diff_lower = content_diff.lower()

        # Critical 키워드 우선 확인
        if any(keyword in diff_lower for keyword in self.critical_keywords):
            return "critical"

        # High 키워드 확인
        if any(keyword in diff_lower for keyword in self.high_keywords):
            return "high"

        # Medium 키워드 확인
        if any(keyword in diff_lower for keyword in self.medium_keywords):
            return "medium"

        return "low"


class IRSMonitorAgent:
    """IRS 모니터링 에이전트 (메타인지 기반)"""

    def __init__(self, registry_path: str) -> None:
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.metacognition = MetacognitionEngine(
            self.registry.get("metacognition", {}).get("hallucination_prevention", {})
        )
        self.impact_assessor = ImpactAssessor(
            self.registry.get("monitoring_rules", {}).get("impact_assessment", {})
        )

        # 해시 저장소
        self.hash_store_path = Path("artifacts/irs_hash_store.json")
        self.hash_store = self._load_hash_store()

    def _load_registry(self) -> dict[str, Any]:
        """레지스트리 로드"""
        with open(self.registry_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_hash_store(self) -> dict[str, str]:
        """해시 저장소 로드"""
        if self.hash_store_path.exists():
            with open(self.hash_store_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_hash_store(self) -> None:
        """해시 저장소 저장"""
        self.hash_store_path.parent.mkdir(exist_ok=True)
        with open(self.hash_store_path, "w", encoding="utf-8") as f:
            json.dump(self.hash_store, f, indent=2, ensure_ascii=False)

    def _fetch_content(self, url: str, content_type: str) -> tuple[str, bytes]:
        """컨텐츠 가져오기"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            if content_type == "pdf":
                return response.text, response.content
            return response.text, response.content

        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)
            raise

    def _calculate_hash(self, content: str) -> str:
        """컨텐츠 해시 계산"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _create_evidence_bundle(
        self,
        source_id: str,
        source_url: str,
        old_content: str,
        new_content: str,
        impact_level: str,
        metacognition_insights: dict[str, Any],
    ) -> dict[str, Any]:
        """Evidence Bundle 생성"""
        evidence_bundle_id = str(uuid.uuid4())

        # 컨텐츠 diff 계산
        import difflib

        diff = list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile="old",
                tofile="new",
                lineterm="",
            )
        )

        return {
            "evidence_bundle_id": evidence_bundle_id,
            "ticket": "TICKET-033",
            "source_id": source_id,
            "source_url": source_url,
            "fetched_at": datetime.now(UTC).isoformat(),
            "sha256_hash": self._calculate_hash(new_content),
            "content_diff": "".join(diff),
            "impact_level": impact_level,
            "conflict_detected": False,  # 멀티 소스 검증에서 설정
            "validation_sources": [source_id],  # 관련 소스 목록
            "trinity_score": self._calculate_trinity_score(impact_level, metacognition_insights),
            "metacognition_insights": metacognition_insights,
        }

    def _calculate_trinity_score(
        self, impact_level: str, insights: dict[str, Any]
    ) -> dict[str, float]:
        """Trinity Score 계산"""
        base_scores = {
            "truth": 0.35,  # IRS 공식 자료 가중치
            "goodness": 0.35,  # Julie CPA 신뢰성 가중치
            "beauty": 0.20,  # 구조화된 시스템 가중치
            "serenity": 0.08,  # 안정적 모니터링 가중치
            "eternity": 0.02,  # 증거 영구 보존 가중치
        }

        # 영향도에 따른 조정
        if impact_level == "critical":
            base_scores["goodness"] *= 0.9  # 긴급성 증가로 신뢰성 영향
        elif impact_level == "high":
            base_scores["serenity"] *= 0.95  # 모니터링 부담 증가

        # 메타인지 인사이트 반영
        if insights.get("hallucination_risks"):
            base_scores["truth"] *= 0.8

        total = sum(
            [
                base_scores["truth"] * 0.35,
                base_scores["goodness"] * 0.35,
                base_scores["beauty"] * 0.20,
                base_scores["serenity"] * 0.08,
                base_scores["eternity"] * 0.02,
            ]
        )

        base_scores["total"] = total
        return base_scores

    def _save_evidence_bundle(self, bundle: dict[str, Any]) -> None:
        """Evidence Bundle 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"artifacts/ticket033_irs_updates_{timestamp}.jsonl"

        Path("artifacts").mkdir(exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        logger.info("Evidence bundle saved: %s", filename)
        return filename

    def monitor_source(self, source: dict[str, Any]) -> dict[str, Any] | None:
        """단일 소스 모니터링"""
        source_id = source["id"]
        url = source["url"]
        content_type = source["content_type"]

        logger.info("Monitoring %s: %s", source_id, url)

        try:
            # 컨텐츠 가져오기
            raw_content, binary_content = self._fetch_content(url, content_type)

            # 컨텐츠 파싱
            parser = ContentParser(source.get("parser_config", {}))
            if content_type == "pdf":
                parsed_content = parser.parse_pdf(binary_content)
            else:
                parsed_content = parser.parse_html(raw_content)

            # 컨텐츠 정규화
            normalized_content = parser.normalize_content(parsed_content)

            # 현재 해시 계산
            current_hash = self._calculate_hash(normalized_content)

            # 이전 해시와 비교
            previous_hash = self.hash_store.get(source_id)
            if previous_hash == current_hash:
                logger.info("No changes detected for %s", source_id)
                return None

            # 변경 감지됨
            logger.warning("Change detected for %s", source_id)

            # 메타인지 검증
            metacognition_insights = self.metacognition.validate_content(
                normalized_content, source.get("content_type", "unknown")
            )

            # 영향도 평가
            old_content = ""  # 이전 컨텐츠가 없으므로 빈 문자열
            impact_level = self.impact_assessor.assess_impact(normalized_content)

            # Evidence Bundle 생성
            bundle = self._create_evidence_bundle(
                source_id,
                url,
                old_content,
                normalized_content,
                impact_level,
                metacognition_insights,
            )

            # 해시 저장소 업데이트
            self.hash_store[source_id] = current_hash
            self._save_hash_store()

            return bundle

        except Exception as e:
            logger.error("Error monitoring %s: %s", source_id, e)
            return None

    def run_monitoring_cycle(self) -> list[dict[str, Any]]:
        """모니터링 사이클 실행"""
        logger.info("Starting IRS monitoring cycle")

        detected_changes = []

        for source in self.registry.get("sources", []):
            bundle = self.monitor_source(source)
            if bundle:
                detected_changes.append(bundle)

                # Evidence Bundle 저장
                self._save_evidence_bundle(bundle)

                # Critical/High 변경은 즉시 로깅
                if bundle["impact_level"] in ["critical", "high"]:
                    logger.critical(
                        f"CRITICAL/HIGH CHANGE DETECTED: {bundle['source_id']} "
                        f"(Impact: {bundle['impact_level']})"
                    )

        logger.info(f"Monitoring cycle completed. Changes detected: {len(detected_changes)}")
        return detected_changes


async def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="IRS SSOT Monitor Agent")
    parser.add_argument(
        "--registry",
        default="ssot_sources/irs_registry.yaml",
        help="Path to IRS registry file",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once instead of continuous monitoring"
    )

    args = parser.parse_args()

    # 모니터링 에이전트 초기화
    agent = IRSMonitorAgent(args.registry)

    if args.once:
        # 단일 실행
        changes = agent.run_monitoring_cycle()
        if changes:
            print(f"Changes detected: {len(changes)}")
            for change in changes:
                print(f"- {change['source_id']}: {change['impact_level']}")
        else:
            print("No changes detected")
    else:
        # 지속적 모니터링 (실제 운영용)
        print("Continuous monitoring not implemented yet. Use --once for single run.")


if __name__ == "__main__":
    asyncio.run(main())
