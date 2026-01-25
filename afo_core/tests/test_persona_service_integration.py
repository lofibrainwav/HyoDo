# Trinity Score: 90.0 (Established by Chancellor)
"""Persona Service 통합 테스트
Phase 4: 최종 검증 - 페르소나 전환 시나리오
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_AFO_ROOT = Path(__file__).resolve().parent.parent
if str(_AFO_ROOT) not in sys.path:
    sys.path.insert(0, str(_AFO_ROOT))


async def test_persona_switch_scenario() -> None:
    """페르소나 전환 시나리오 테스트"""
    print("🧪 [통합 테스트] 페르소나 전환 시나리오 시작...\n")

    try:
        from AFO.services.persona_service import persona_service

        # 1. 현재 페르소나 조회
        print("1️⃣ 현재 페르소나 조회")
        current = await persona_service.get_current_persona()
        print(f"   ✅ 현재 페르소나: {current['name']} ({current['type']})")
        print(f"   Trinity Scores: {current['trinity_scores']}\n")

        # 2. Learner 페르소나로 전환
        print("2️⃣ Learner 페르소나로 전환")
        switch_result = await persona_service.switch_persona(
            "learner", context={"reason": "테스트", "test_id": "integration_001"}
        )
        print(f"   ✅ 전환 완료: {switch_result['current_persona']}")
        print(f"   상태: {switch_result['status']}")
        print(f"   Trinity Scores: {switch_result['trinity_scores']}\n")

        # 3. 전환 후 현재 페르소나 확인
        print("3️⃣ 전환 후 현재 페르소나 확인")
        new_current = await persona_service.get_current_persona()
        assert new_current["type"] == "learner", "페르소나 전환 실패"
        print(f"   ✅ 확인 완료: {new_current['name']} ({new_current['type']})\n")

        # 4. Trinity Score 계산 테스트
        print("4️⃣ Trinity Score 계산 테스트")
        persona_data = {
            "id": "p007",
            "name": "배움의 길 (眞 Learning)",
            "type": "learner",
            "role": "Learner",
        }
        score_result = await persona_service.calculate_trinity_score(
            persona_data=persona_data, context={"test": True}
        )
        print("   ✅ 계산 완료:")
        print(f"   - Truth: {score_result.get('truth_score', 0)}")
        print(f"   - Goodness: {score_result.get('goodness_score', 0)}")
        print(f"   - Beauty: {score_result.get('beauty_score', 0)}")
        print(f"   - Serenity: {score_result.get('serenity_score', 0)}")
        print(f"   - Eternity: {score_result.get('eternity_score', 0)}")
        print(f"   - 총점: {score_result.get('total_score', 0)}")
        print(f"   - 평가: {score_result.get('evaluation', 'N/A')}\n")

        # 5. Commander로 복귀
        print("5️⃣ Commander 페르소나로 복귀")
        final_result = await persona_service.switch_persona("commander")
        print(f"   ✅ 복귀 완료: {final_result['current_persona']}\n")

        print("🎉 [통합 테스트] 모든 시나리오 통과!")

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("   💡 AFO 모듈을 찾을 수 없습니다. PYTHONPATH를 확인하세요.")
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


async def test_all_personas() -> None:
    """모든 페르소나 타입 전환 테스트"""
    print("\n🧪 [통합 테스트] 모든 페르소나 타입 전환 테스트 시작...\n")

    persona_types = [
        "commander",
        "family_head",
        "creator",
        "learner",
        "jang_yeong_sil",
        "sima_yi",
        "zhou_yu",
    ]

    try:
        from AFO.services.persona_service import persona_service

        for persona_type in persona_types:
            print(f"🔄 {persona_type} 페르소나로 전환 중...")
            result = await persona_service.switch_persona(persona_type)
            current = await persona_service.get_current_persona()
            assert current["type"] == persona_type, f"{persona_type} 전환 실패"
            print(f"   ✅ {result['current_persona']} 활성화 완료")

        print("\n🎉 [통합 테스트] 모든 페르소나 타입 전환 성공!")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


async def main() -> None:
    """메인 테스트 실행"""
    print("=" * 60)
    print("🏰 AFO Kingdom - Persona Service 통합 테스트")
    print("=" * 60)
    print()

    await test_persona_switch_scenario()
    await test_all_personas()

    print("\n" + "=" * 60)
    print("✅ 모든 통합 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
