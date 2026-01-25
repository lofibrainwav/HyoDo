#!/usr/bin/env python3
"""
Skills Registry의 모든 스킬이 Trinity Score를 가지고 있는지 검증

眞善美孝永 5기둥 점수가 모든 스킬에 등록되어 있는지 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

try:
    from afo_skills_registry import register_core_skills
except ImportError as e:
    print(f"❌ Import 실패: {e}")
    sys.exit(1)


def main() -> None:
    """모든 스킬의 Trinity Score 검증"""
    print("=" * 70)
    print("眞善美孝永 - Skills Registry 전체 검증")
    print("=" * 70)

    registry = register_core_skills()
    all_skills = registry.list_all()

    print(f"\n📋 총 등록된 스킬: {len(all_skills)}개\n")

    results = {
        "total": len(all_skills),
        "with_philosophy": 0,
        "without_philosophy": 0,
        "skills": [],
    }

    for skill in all_skills:
        skill_info = {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "category": (
                skill.category.value if hasattr(skill.category, "value") else str(skill.category)
            ),
            "has_philosophy": skill.philosophy_scores is not None,
        }

        if skill.philosophy_scores:
            results["with_philosophy"] += 1
            skill_info["philosophy_scores"] = {
                "truth": skill.philosophy_scores.truth,
                "goodness": skill.philosophy_scores.goodness,
                "beauty": skill.philosophy_scores.beauty,
                "serenity": skill.philosophy_scores.serenity,
                "average": skill.philosophy_scores.average,
            }
            status_icon = "✅"
        else:
            results["without_philosophy"] += 1
            skill_info["philosophy_scores"] = None
            status_icon = "❌"

        results["skills"].append(skill_info)

        # 출력
        print(f"{status_icon} {skill.skill_id}")
        print(f"   이름: {skill.name}")
        print(f"   카테고리: {skill_info['category']}")

        if skill.philosophy_scores:
            print(f"   철학 점수: {skill.philosophy_scores.summary}")
        else:
            print("   ⚠️  철학 점수 없음")

        print()

    # 요약
    print("=" * 70)
    print("📊 검증 결과 요약")
    print("=" * 70)
    print(f"전체 스킬: {results['total']}개")
    print(f"철학 점수 있음: {results['with_philosophy']}개 ✅")
    print(f"철학 점수 없음: {results['without_philosophy']}개")

    if results["without_philosophy"] > 0:
        print("\n⚠️  철학 점수가 없는 스킬:")
        for skill_info in results["skills"]:
            if not skill_info["has_philosophy"]:
                print(f"  - {skill_info['skill_id']}: {skill_info['name']}")

    # 통과율
    pass_rate = (results["with_philosophy"] / results["total"] * 100) if results["total"] > 0 else 0
    print(f"\n통과율: {pass_rate:.1f}%")

    if results["without_philosophy"] == 0:
        print("\n✅ 모든 스킬이 철학 점수를 가지고 있습니다!")
        return 0
    print(f"\n⚠️  {results['without_philosophy']}개 스킬에 철학 점수가 없습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
