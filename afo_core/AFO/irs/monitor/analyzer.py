import hashlib
import logging
import re
from datetime import datetime
from typing import Any

from AFO.irs.monitor.types import IRSChangeEvent

logger = logging.getLogger(__name__)


class IRSAnalyzer:
    """IRS 변경 콘텐츠 분석 AI"""

    def __init__(self) -> None:
        self.change_patterns = {
            "tax_rate_change": [
                r"tax rate.*changed?",
                r"rate.*increased?",
                r"rate.*decreased?",
                r"percentage.*changed?",
                r"\d+%.*tax",
            ],
            "deduction_change": [
                r"deduction.*changed?",
                r"deduction.*increased?",
                r"deduction.*decreased?",
                r"standard deduction.*\$\d+",
                r"deduction limit",
            ],
            "credit_change": [
                r"tax credit.*changed?",
                r"credit.*increased?",
                r"credit.*decreased?",
                r"credit amount.*\$\d+",
                r"credit limit",
            ],
            "filing_requirement": [
                r"filing requirement",
                r"reporting requirement",
                r"information return",
                r"schedule.*required",
                r"form.*required",
            ],
            "deadline_change": [
                r"deadline.*changed?",
                r"due date.*changed?",
                r"extension.*deadline",
                r"filing date.*changed?",
                r"tax day.*changed?",
            ],
        }

    def analyze_change_content(self, latest_items: list[dict[str, str]]) -> dict[str, Any]:
        """변경 콘텐츠 분석"""
        analysis = {
            "change_types": [],
            "affected_areas": [],
            "severity": "low",
            "requires_action": False,
        }

        all_titles = " ".join(item["title"] for item in latest_items)
        all_titles_lower = all_titles.lower()

        for change_type, patterns in self.change_patterns.items():
            for pattern in patterns:
                if (
                    re.search(pattern, all_titles_lower, re.IGNORECASE)
                    and change_type not in analysis["change_types"]
                ):
                    analysis["change_types"].append(change_type)

        if any(
            word in all_titles_lower for word in ["tax rate", "deduction", "credit", "deadline"]
        ):
            analysis["severity"] = "high"
            analysis["requires_action"] = True

            if "tax rate" in all_titles_lower:
                analysis["affected_areas"].extend(["income_tax", "calculations"])
            if "deduction" in all_titles_lower:
                analysis["affected_areas"].extend(["deductions", "itemizing"])
            if "credit" in all_titles_lower:
                analysis["affected_areas"].extend(["tax_credits", "refunds"])
            if "deadline" in all_titles_lower:
                analysis["affected_areas"].extend(["filing", "extensions"])

        return analysis

    def create_change_event(
        self, source_name: str, url: str, change_details: dict[str, Any]
    ) -> IRSChangeEvent | None:
        """변경 이벤트 생성"""
        try:
            latest_items = change_details.get("latest_items", [])

            # 여기서 analyze 를 호출하도록 변경하여 crawler -> analyzer로 이어지는 데이터 흐름을 단순화
            # Crawler는 raw change details만 주고, Analyzer가 분석 및 이벤트 생성을 담당
            analysis = self.analyze_change_content(latest_items)

            if not latest_items:
                return None

            main_item = latest_items[0]

            event_id = hashlib.sha256(
                f"{url}_{main_item['title']}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]

            change_type = analysis.get("change_types", ["general_update"])
            change_type = change_type[0] if change_type else "general_update"

            severity = analysis.get("severity", "medium")
            affected_areas = analysis.get("affected_areas", [])

            change_event = IRSChangeEvent(
                event_id=event_id,
                change_type=change_type,
                source_url=url,
                title=f"IRS {source_name.replace('_', ' ').title()}: {main_item['title']}",
                content_preview=main_item["title"],
                detected_at=datetime.now().isoformat(),
                severity=severity,
                affected_areas=affected_areas,
                action_required=analysis.get("requires_action", False),
            )

            return change_event

        except Exception as e:
            logger.error(f"Error creating change event: {e}")
            return None
