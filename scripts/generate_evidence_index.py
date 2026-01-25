#!/usr/bin/env python3
"""
Evidence Index Generator for AFO Kingdom
永(Eternity) - Records and indexes all Trinity Evidence for trend analysis

This script scans all Trinity evidence directories and generates a comprehensive index
for operational analytics and trend monitoring.
"""

import json
import operator
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EvidenceIndexGenerator:
    """Generates comprehensive index of Trinity evidence for analytics"""

    def __init__(self) -> None:
        self.trinity_dir = Path("artifacts/trinity")
        self.index_dir = Path("artifacts/index")
        self.index_file = self.index_dir / "evidence_index.json"

    def scan_evidence_directories(self) -> list[str]:
        """Scan all date directories containing evidence"""
        if not self.trinity_dir.exists():
            return []

        date_dirs = []
        for item in self.trinity_dir.iterdir():
            if item.is_dir() and item.name.replace("-", "").isdigit():
                # Validate date format (YYYY-MM-DD)
                try:
                    datetime.fromisoformat(item.name)
                    date_dirs.append(item.name)
                except ValueError:
                    continue

        return sorted(date_dirs)

    def load_evidence_data(self, date_str: str) -> dict[str, Any]:
        """Load evidence data for a specific date"""
        evidence_file = self.trinity_dir / date_str / "evidence.json"

        if not evidence_file.exists():
            return None

        try:
            with Path(evidence_file).open(encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load evidence for {date_str}: {e}")
            return None

    def calculate_trinity_statistics(self, all_evidence: list[dict]) -> dict[str, Any]:
        """Calculate comprehensive Trinity Score statistics"""
        if not all_evidence:
            return {}

        # Extract scores
        scores = [ev["calculation"]["total"] for ev in all_evidence if ev]
        truth_scores = [ev["calculation"]["truth"] for ev in all_evidence if ev]
        goodness_scores = [ev["calculation"]["goodness"] for ev in all_evidence if ev]
        beauty_scores = [ev["calculation"]["beauty"] for ev in all_evidence if ev]
        serenity_scores = [ev["calculation"]["serenity"] for ev in all_evidence if ev]
        eternity_scores = [ev["calculation"]["eternity"] for ev in all_evidence if ev]

        gates = [ev["calculation"]["gate"] for ev in all_evidence if ev]

        def safe_stats(values: list[float]) -> dict[str, float]:
            if not values:
                return {"mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
            return {
                "mean": round(statistics.mean(values), 3),
                "median": round(statistics.median(values), 3),
                "std": round(statistics.stdev(values) if len(values) > 1 else 0, 3),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
            }

        return {
            "overall": safe_stats(scores),
            "pillars": {
                "truth": safe_stats(truth_scores),
                "goodness": safe_stats(goodness_scores),
                "beauty": safe_stats(beauty_scores),
                "serenity": safe_stats(serenity_scores),
                "eternity": safe_stats(eternity_scores),
            },
            "gates": {
                "distribution": dict(Counter(gates)),
                "auto_run_ratio": (
                    round(gates.count("AUTO_RUN") / len(gates), 3) if gates else 0.0
                ),
                "total_evaluations": len(gates),
            },
        }

    def analyze_trends(self, date_evidence: list[tuple[str, dict]]) -> dict[str, Any]:
        """Analyze trends over time"""
        if len(date_evidence) < 2:
            return {
                "insufficient_data": True,
                "message": "Need at least 2 data points for trend analysis",
            }

        # Sort by date
        sorted_data = sorted(date_evidence, key=operator.itemgetter(0))

        # Calculate day-over-day changes
        changes = []
        for i in range(1, len(sorted_data)):
            prev_score = sorted_data[i - 1][1]["calculation"]["total"]
            curr_score = sorted_data[i][1]["calculation"]["total"]
            changes.append(curr_score - prev_score)

        trend = {
            "direction": "stable",
            "avg_daily_change": round(statistics.mean(changes), 3) if changes else 0.0,
            "volatility": (round(statistics.stdev(changes), 3) if len(changes) > 1 else 0.0),
            "consistency_score": round(
                1.0 - (statistics.stdev(changes) if len(changes) > 1 else 0), 3
            ),
        }

        # Determine trend direction
        if changes:
            avg_change = statistics.mean(changes)
            if avg_change > 0.01:
                trend["direction"] = "improving"
            elif avg_change < -0.01:
                trend["direction"] = "declining"
            else:
                trend["direction"] = "stable"

        return trend

    def identify_failure_patterns(self, all_evidence: list[dict]) -> dict[str, Any]:
        """Analyze failure patterns and root causes"""
        failures = [ev for ev in all_evidence if ev and ev["calculation"]["gate"] != "AUTO_RUN"]

        if not failures:
            return {
                "no_failures": True,
                "message": "All evaluations passed AUTO_RUN threshold",
            }

        # Analyze failure reasons (would need to be added to evidence structure)
        # For now, provide basic failure statistics
        failure_dates = []
        failure_scores = []

        for ev in failures:
            # Extract date from evidence metadata if available
            if "metadata" in ev and "generated_at" in ev["metadata"]:
                # Parse ISO datetime and extract date
                try:
                    dt = datetime.fromisoformat(ev["metadata"]["generated_at"])
                    failure_dates.append(dt.date().isoformat())
                except (ValueError, TypeError):
                    pass
            failure_scores.append(ev["calculation"]["total"])

        return {
            "total_failures": len(failures),
            "failure_rate": round(len(failures) / len(all_evidence), 3),
            "avg_failure_score": (
                round(statistics.mean(failure_scores), 3) if failure_scores else 0.0
            ),
            "failure_dates": failure_dates[:5],  # Last 5 failures
            "recommendations": [
                "Investigate scores below 0.95 threshold",
                "Review system health metrics",
                "Check for environmental factors",
            ],
        }

    def generate_comprehensive_index(self) -> dict[str, Any]:
        """Generate the complete evidence index"""
        print("🏰 Evidence Index 생성 시작")

        # Scan directories
        date_dirs = self.scan_evidence_directories()
        print(f"📊 발견된 증거 날짜: {len(date_dirs)}개")

        # Load all evidence
        all_evidence = []
        date_evidence = []

        for date_str in date_dirs:
            evidence = self.load_evidence_data(date_str)
            if evidence:
                all_evidence.append(evidence)
                date_evidence.append((date_str, evidence))

        print(f"✅ 유효한 증거 데이터: {len(all_evidence)}개")

        # Generate index
        return {
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat() + "Z",
                "kingdom": "AFO Kingdom",
                "version": "1.0.0",
                "description": "Comprehensive index of Trinity evidence for operational analytics",
            },
            "summary": {
                "total_days": len(date_dirs),
                "valid_evidences": len(all_evidence),
                "date_range": {
                    "start": min(date_dirs) if date_dirs else None,
                    "end": max(date_dirs) if date_dirs else None,
                },
            },
            "statistics": self.calculate_trinity_statistics(all_evidence),
            "trends": self.analyze_trends(date_evidence),
            "failures": self.identify_failure_patterns(all_evidence),
            "daily_breakdown": {
                date: {
                    "score": ev["calculation"]["total"],
                    "gate": ev["calculation"]["gate"],
                    "pillars": {
                        "truth": ev["calculation"]["truth"],
                        "goodness": ev["calculation"]["goodness"],
                        "beauty": ev["calculation"]["beauty"],
                        "serenity": ev["calculation"]["serenity"],
                        "eternity": ev["calculation"]["eternity"],
                    },
                }
                for date, ev in date_evidence
            },
        }

    def save_index(self, index: dict[str, Any]) -> bool:
        """Save the evidence index to file"""
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)

            with Path(self.index_file).open("w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            print(f"✅ Evidence Index 저장 완료: {self.index_file}")
            return True

        except Exception as e:
            print(f"❌ Evidence Index 저장 실패: {e}")
            return False


def main() -> None:
    """Main execution function"""
    print("🏰 AFO 왕국 Evidence Index 생성기")
    print("=" * 50)

    generator = EvidenceIndexGenerator()
    index = generator.generate_comprehensive_index()
    success = generator.save_index(index)

    if success:
        print("\n📊 Evidence Index 생성 완료!")
        print(f"📁 파일 위치: {generator.index_file}")
        print(f"📈 분석된 증거: {index['summary']['valid_evidences']}개")
        print(
            f"📅 날짜 범위: {index['summary']['date_range']['start']} ~ {index['summary']['date_range']['end']}"
        )

        # Print key statistics
        stats = index["statistics"]
        if stats:
            print("🏆 Trinity Score 통계:")
            print(f"   평균 점수: {stats['overall']['mean']:.3f}")
            print(f"   AUTO_RUN 비율: {stats['gates']['auto_run_ratio']:.1%}")
    else:
        print("❌ Evidence Index 생성 실패")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
