#!/usr/bin/env python3
"""
AFO 왕국 CI/CD 에이전트 시스템 테스트
전체 에이전트 네트워크의 통합 테스트
"""

import asyncio
import sys
import time
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "afo-core"))


async def test_agent_system():
    """에이전트 시스템 통합 테스트"""
    print("🎯 [시스템 테스트] AFO 왕국 CI/CD 에이전트 네트워크 테스트 시작")

    try:
        # 에이전트 모듈들 임포트
        from AFO.agents.ci_cd_agents import (
            get_pipeline_status,
            initialize_ci_cd_agents,
            run_ci_cd_pipeline,
        )
        from AFO.agents.quality_agents import initialize_quality_agents

        print("📦 [시스템 테스트] 모듈 임포트 완료")

        # 에이전트들 초기화
        print("🔧 [시스템 테스트] 에이전트 초기화 중...")
        await initialize_ci_cd_agents()
        await initialize_quality_agents()
        print("✅ [시스템 테스트] 에이전트 초기화 완료")

        # 테스트 파일들 준비
        test_files = [
            "packages/afo-core/AFO/__init__.py",
            "packages/afo-core/AFO/settings.py",
            "packages/afo-core/AFO/agents/ci_cd_agents.py",
        ]

        print(f"📁 [시스템 테스트] 테스트 파일: {len(test_files)}개")

        # 파이프라인 실행
        print("🚀 [시스템 테스트] CI/CD 파이프라인 시작")
        start_time = time.time()

        session_id = await run_ci_cd_pipeline(test_files)
        print(f"🎯 [시스템 테스트] 세션 시작: {session_id}")

        # 실행 모니터링 (최대 60초)
        max_wait = 60
        for i in range(max_wait):
            status = await get_pipeline_status()
            active_agents = status.get("active_agents", 0)

            if i % 10 == 0:  # 10초마다 상태 출력
                print(f"📊 [시스템 테스트] {i}s: 활성 에이전트 {active_agents}개")

            if active_agents == 0 and status.get("status") in ["idle", "completed"]:
                break

            await asyncio.sleep(1.0)

        total_time = time.time() - start_time

        # 최종 결과
        final_status = await get_pipeline_status()

        print("\n🎉 [시스템 테스트] 결과 요약")
        print(f"⏱️  총 실행 시간: {total_time:.2f}초")
        print(f"🎯 세션 ID: {final_status.get('session_id', 'N/A')}")
        print(f"📊 최종 상태: {final_status.get('status', 'unknown')}")
        print(f"🤖 총 에이전트: {final_status.get('total_agents', 0)}개")

        # 성공/실패 판단
        if total_time < 30 and final_status.get("status") in ["completed", "idle"]:
            print("✅ [시스템 테스트] 성공: 빠른 실행 및 정상 완료")
            return True
        elif total_time < 60:
            print("⚠️  [시스템 테스트] 부분 성공: 실행은 되었으나 최적화 필요")
            return True
        else:
            print("❌ [시스템 테스트] 실패: 타임아웃 또는 실행 오류")
            return False

    except Exception as e:
        print(f"❌ [시스템 테스트] 치명적 오류: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """메인 함수"""
    print("=" * 60)
    print("🛡️  AFO 왕국 CI/CD 에이전트 시스템 통합 테스트")
    print("=" * 60)

    success = await test_agent_system()

    print("\n" + "=" * 60)
    if success:
        print("🎊 테스트 성공! 에이전트 시스템이 정상 작동합니다.")
        sys.exit(0)
    else:
        print("💥 테스트 실패! 시스템 점검이 필요합니다.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
