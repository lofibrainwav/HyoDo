#!/usr/bin/env python3
"""
AFO Kingdom PR Comment Generator

SSOT 위반, 영어 비율 경고 등에 대한 표준화된 PR 코멘트를 생성합니다.
Context7과 통합하여 위험도별 메시지 톤과 관련 링크를 제공합니다.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_documentation_links() -> dict[str, str]:
    """관련 문서 링크 반환"""
    base_url = "https://github.com/lofibrainwav/AFO_Kingdom/blob/main"
    return {
        "report_template": f"{base_url}/docs/reports/_TEMPLATE.md",
        "ssot_guide": f"{base_url}/docs/AFO_CHANCELLOR_GRAPH_SPEC.md",
        "english_guide": f"{base_url}/AGENTS.md#reporting-rules",
        "weekly_metrics": f"{base_url}/docs/reports/_metrics/README.md",
    }


def generate_ssot_violation_comment(violations: list[str]) -> str:
    """SSOT 위반 코멘트 생성"""
    links = get_documentation_links()

    return f"""## ❌ SSOT Report Gate Failed

보고서 품질 검증에 실패했습니다. AFO 왕국의 표준을 준수해주세요.

### 📋 위반 사항
{chr(10).join(f"- {v}" for v in violations[:5])}

### 🔗 참고 자료
- [보고서 템플릿]({links["report_template"]})
- [SSOT 가이드]({links["ssot_guide"]})
- [주간 메트릭]({links["weekly_metrics"]})

### 💡 수정 방법
1. 템플릿 형식 준수
2. 필수 섹션 포함 (Context/Analysis/Evidence/Next Steps)
3. "완료/구현됨" 금지어 제거

문의사항이 있으시면 언제든 말씀해주세요! 🙏"""


def generate_english_ratio_comment(flagged_reports: list[dict[str, Any]]) -> str:
    """영어 비율 경고 코멘트 생성"""
    links = get_documentation_links()

    return f"""## ⚠️ English-heavy Report Detected

협업 효율을 위해 영어 비율을 조정해주세요.

### 📊 경고 대상
{chr(10).join(f"- {r['file']} (영어 비율: {r['english_ratio']:.1%})" for r in flagged_reports[:5])}

### 🔗 참고 자료
- [보고 규칙]({links["english_guide"]})
- [보고서 템플릿]({links["report_template"]})

### 💡 개선 팁
- 핵심 개념은 영어로 설명하되
- 절차/예시는 한국어로 작성
- 코드와 데이터는 원래 언어 유지

영어 사용은 환영하지만, 협업 효율을 위해 한국어 비중을 조금 높여주세요! 🇰🇷"""


def generate_combined_comment(
    ssot_violations: list[str] | None = None,
    english_warnings: list[dict[str, Any]] | None = None,
) -> str:
    """통합 코멘트 생성"""
    comments = []

    if ssot_violations:
        comments.append(generate_ssot_violation_comment(ssot_violations))

    if english_warnings:
        comments.append(generate_english_ratio_comment(english_warnings))

    return "\n\n---\n\n".join(comments)


def main() -> None:
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate PR comments for AFO Kingdom")
    parser.add_argument("--ssot-violations", nargs="*", help="SSOT violations")
    parser.add_argument("--english-warnings", type=json.loads, help="English ratio warnings JSON")

    args = parser.parse_args()

    comment = generate_combined_comment(
        ssot_violations=args.ssot_violations, english_warnings=args.english_warnings
    )

    print(comment)


if __name__ == "__main__":
    main()
