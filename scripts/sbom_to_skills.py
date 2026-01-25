#!/usr/bin/env python3
"""
SBOM → Skills Registry 연동 스크립트

CycloneDX SBOM에서 컴포넌트를 파싱하여 Skills Registry에 등록합니다.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def parse_cyclonedx_sbom(sbom_path: str) -> list[dict]:
    """CycloneDX JSON SBOM을 파싱하여 컴포넌트 목록 반환"""
    with Path(sbom_path).open(encoding="utf-8") as f:
        sbom = json.load(f)

    return [
        {
            "name": comp.get("name", "unknown"),
            "version": comp.get("version", "0.0.0"),
            "type": comp.get("type", "library"),
            "purl": comp.get("purl", ""),
            "licenses": [
                lic.get("license", {}).get("id", "unknown") for lic in comp.get("licenses", [])
            ],
        }
        for comp in sbom.get("components", [])
    ]


def calculate_goodness_score(components: list[dict]) -> float:
    """善 (Goodness) 점수 계산 - 라이선스 준수 기반"""
    if not components:
        return 1.0

    approved_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "Python-2.0"}
    compliant = sum(
        1 for c in components if any(lic in approved_licenses for lic in c.get("licenses", []))
    )

    return round(compliant / len(components), 2)


def generate_skills_registry(components: list[dict]) -> dict:
    """Skills Registry 형식으로 변환"""
    goodness_score = calculate_goodness_score(components)

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_dependencies": len(components),
        "goodness_score": goodness_score,
        "components": components[:50],  # Top 50
        "license_summary": _summarize_licenses(components),
    }


def _summarize_licenses(components: list[dict]) -> dict:
    """라이선스 분포 요약"""
    license_counts: dict[str, int] = {}
    for comp in components:
        for lic in comp.get("licenses", ["unknown"]):
            license_counts[lic] = license_counts.get(lic, 0) + 1
    return license_counts


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: sbom_to_skills.py <sbom.cdx.json>")
        sys.exit(1)

    sbom_path = sys.argv[1]

    if not Path(sbom_path).exists():
        print(f"SBOM file not found: {sbom_path}")
        sys.exit(1)

    components = parse_cyclonedx_sbom(sbom_path)
    registry = generate_skills_registry(components)

    output_path = "skills_registry.json"
    with Path(output_path).open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print(f"✅ Skills Registry 생성 완료: {output_path}")
    print(f"   - 총 컴포넌트: {registry['total_dependencies']}")
    print(f"   - 善 (Goodness) 점수: {registry['goodness_score']}")


if __name__ == "__main__":
    main()
