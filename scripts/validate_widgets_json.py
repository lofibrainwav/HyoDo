#!/usr/bin/env python3
"""
Widget JSON Contract Validator

Validates generated/widgets.json against Pydantic v2 schema.
Used in CI/local validation, NOT in frontend build path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add afo-core to path
repo_root = Path(__file__).parent.parent
afo_core_path = repo_root / "packages" / "afo-core"
sys.path.insert(0, str(afo_core_path))

try:
    from models.widget_spec import WidgetsPayloadFlexible as WidgetsPayload
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure pydantic is installed: pip install pydantic")
    sys.exit(1)


def main() -> int:
    """Validate widgets.json"""
    widgets_json_path = (
        repo_root / "packages" / "dashboard" / "src" / "generated" / "widgets.generated.json"
    )

    if not widgets_json_path.exists():
        print(f"❌ widgets.generated.json not found: {widgets_json_path}")
        print("   Run: pnpm -C packages/dashboard gen:widgets")
        return 1

    print(f"📐 Validating: {widgets_json_path}")
    print()

    try:
        # Read JSON
        json_data = widgets_json_path.read_text(encoding="utf-8")
        data = json.loads(json_data)

        # Validate with Pydantic
        payload = WidgetsPayload.model_validate(data)

        print("✅ Validation passed!")
        print(f"   Source: {payload.source}")
        print(f"   Generated at: {payload.generatedAt}")
        print(f"   Widget count: {payload.count}")
        print(f"   Validated widgets: {len(payload.widgets)}")

        # Check for duplicates
        widget_ids = [w.id for w in payload.widgets]
        duplicates = [id for id in widget_ids if widget_ids.count(id) > 1]
        if duplicates:
            print(f"⚠️  Duplicate IDs found: {set(duplicates)}")
            return 1

        # [Ticket 3 Gate] slug 규칙 고정 + 중복 체크
        print()
        print("3. Slug 규칙 검증...")
        slug_issues = []
        for w in payload.widgets:
            widget_dict = w if isinstance(w, dict) else w.model_dump()
            widget_id = widget_dict.get("id", "")

            # slug는 id에서 파생 (id 자체가 slug)
            # SSOT 규칙:
            # - 허용 문자: 소문자 a-z, 숫자 0-9, 하이픈(-), 한글(가-힣)
            # - 공백/언더스코어/대문자 불가
            # - 연속 하이픈(--), 양끝 하이픈(-foo / foo-) 불가
            import re

            # 허용 문자셋: a-z, 0-9, -, 가-힣
            slug_pattern = re.compile(r"^[a-z0-9가-힣\-]+$")
            if not slug_pattern.match(widget_id):
                slug_issues.append(
                    f"Invalid slug format (허용 문자: a-z, 0-9, -, 가-힣): {widget_id}"
                )
                continue

            # 연속 하이픈 체크
            if "--" in widget_id:
                slug_issues.append(f"Invalid slug format (연속 하이픈 불가): {widget_id}")
                continue

            # 양끝 하이픈 체크
            if widget_id.startswith("-") or widget_id.endswith("-"):
                slug_issues.append(f"Invalid slug format (양끝 하이픈 불가): {widget_id}")
                continue

        if slug_issues:
            print("⚠️  Slug 규칙 위반:")
            for issue in slug_issues:
                print(f"   - {issue}")
            return 1

        print("   ✅ Slug 규칙 통과 (허용 문자: a-z, 0-9, -, 가-힣)")

        # [Ticket 4 Gate] fragment 경로 필드 검증 (강화)
        print()
        print("4. Fragment 경로 필드 검증...")
        fragment_errors = []
        fragment_key_count = 0
        fallback_count = 0

        for w in payload.widgets:
            widget_dict = w if isinstance(w, dict) else w.model_dump()
            widget_id = widget_dict.get("id", "")

            # [Ticket 4] SSOT: fragment_key는 반드시 존재 (error로 강화)
            # 읽을 때만 fallback: fragment_key ?? html_section_id ?? sourceId
            fragment_key = widget_dict.get("fragment_key")
            html_section_id = widget_dict.get("html_section_id")
            source_id = widget_dict.get("sourceId")

            # 표준 키 확인
            if fragment_key:
                fragment_key_count += 1
            else:
                # Fallback 확인 (경고 → error로 변경)
                fallback_value = html_section_id or source_id
                if fallback_value:
                    fallback_count += 1
                    # [Ticket 4] 이제는 error로 처리 (표준화 완료되었으므로)
                    fragment_errors.append(
                        f"Missing fragment_key (required): {widget_id} (fallback: {fallback_value})"
                    )
                else:
                    # 완전히 없음 (error)
                    fragment_errors.append(f"Missing fragment pointer: {widget_id}")

        # 결과 출력
        if fragment_key_count > 0:
            print(f"   ✅ 표준 키(fragment_key) 사용: {fragment_key_count}개")

        if fallback_count > 0:
            print(
                f"   ⚠️  Fallback 필드 사용: {fallback_count}개 (fragment_key로 마이그레이션 필요)"
            )

        if fragment_errors:
            print(f"   ❌ Fragment 포인터 에러 ({len(fragment_errors)}개):")
            for issue in fragment_errors[:5]:  # 최대 5개만 표시
                print(f"      - {issue}")
            if len(fragment_errors) > 5:
                print(f"      ... and {len(fragment_errors) - 5} more")
            print(
                "   [Ticket 4] fragment_key는 필수입니다. generate_widgets_from_html.mjs에서 생성하세요."
            )
            return 1  # Error로 처리

        print("   ✅ Fragment 경로 필드 검증 완료")

        print()
        print("✅ All widgets valid, no duplicates found")
        print("✅ Slug 규칙 통과")
        print("✅ Fragment 경로 필드 검증 완료")
        return 0

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
