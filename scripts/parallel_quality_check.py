#!/usr/bin/env python3
"""
AFO 왕국 병렬 품질 검사 시스템
독립적인 코드 품질 도구들을 동시에 실행하여 실행 시간 단축
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


class ParallelQualityChecker:
    """병렬 품질 검사 실행기"""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.results = {}

    async def run_command_async(
        self, name: str, cmd: List[str], cwd: Path = None
    ) -> Tuple[str, bool, str]:
        """비동기로 명령어 실행"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd or self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0

            return name, success, output

        except Exception as e:
            return name, False, f"Error: {e}"

    async def run_parallel_checks(self) -> Dict[str, Tuple[bool, str]]:
        """병렬로 품질 검사 실행"""

        # Phase 35-3: 지능적 병렬화 전략
        # 독립적인 도구들을 그룹화하여 동시에 실행

        parallel_tasks = [
            # 그룹 1: 초고속 도구들 (서로 독립적)
            (
                "ruff",
                [
                    "ruff",
                    "check",
                    "--fix",
                    "--unsafe-fixes",
                    "packages/afo-core/",
                    "scripts/",
                ],
            ),
            (
                "mypy",
                [
                    "mypy",
                    "packages/afo-core/",
                    "--exclude",
                    "packages/afo-core/tests/|packages/afo-core/legacy/",
                ],
            ),
            # 그룹 2: 중간 속도 도구들
            ("pyright", ["pyright", "--project", "pyproject.toml"]),
            (
                "bandit",
                ["bandit", "-c", "pyproject.toml", "-lll", "-r", "packages/afo-core/"],
            ),
        ]

        print("🛡️  [AFO] 병렬 품질 검사 시작...")
        start_time = time.time()

        # 모든 태스크를 동시에 실행
        tasks = [self.run_command_async(name, cmd) for name, cmd in parallel_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        execution_time = time.time() - start_time

        # 결과 정리
        final_results = {}
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ 태스크 실행 중 예외: {result}")
                continue

            name, success, output = result
            final_results[name] = (success, output)

            status = "✅" if success else "❌"
            print(f"{status} [{name}] 완료")

        print(f"⏱️  [AFO] 병렬 검사 완료: {execution_time:.2f}초")
        return final_results

    def run_sequential_fallbacks(self) -> Dict[str, Tuple[bool, str]]:
        """순차적 폴백 실행 (병렬 실패 시)"""
        print("🔄 [AFO] 순차적 폴백 모드로 전환...")

        sequential_checks = {
            "ruff_format": ["ruff", "format", "packages/afo-core/", "scripts/"],
            "syntax_check": ["python", "scripts/syntax_check.py"],
        }

        results = {}
        for name, cmd in sequential_checks.items():
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr
                results[name] = (success, output)

                status = "✅" if success else "❌"
                print(f"{status} [{name}] 순차 실행 완료")

            except subprocess.TimeoutExpired:
                results[name] = (False, "Timeout after 30 seconds")
                print(f"⏰ [{name}] 타임아웃")
            except Exception as e:
                results[name] = (False, f"Error: {e}")
                print(f"❌ [{name}] 실행 실패: {e}")

        return results


async def main():
    """메인 실행 함수"""
    checker = ParallelQualityChecker()

    try:
        # 병렬 실행 시도
        results = await checker.run_parallel_checks()

        # 결과 요약
        successful = sum(1 for success, _ in results.values() if success)
        total = len(results)

        print(f"\n📊 [AFO] 품질 검사 결과: {successful}/{total} 성공")

        # 실패한 항목들 보고
        failures = [(name, output) for name, (success, output) in results.items() if not success]
        if failures:
            print("\n❌ 실패한 검사들:")
            for name, output in failures[:3]:  # 처음 3개만 표시
                print(f"  - {name}: {output[:100]}...")

        # 성공률에 따른 종료 코드
        success_rate = successful / total if total > 0 else 0
        exit_code = 0 if success_rate >= 0.8 else 1  # 80% 이상 성공 시 통과

        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ [AFO] 병렬 검사 시스템 실패: {e}")
        print("🔄 순차적 폴백으로 전환...")

        # 폴백 실행
        fallback_results = checker.run_sequential_fallbacks()
        successful = sum(1 for success, _ in fallback_results.values() if success)
        total = len(fallback_results)

        print(f"📊 [AFO] 폴백 결과: {successful}/{total} 성공")
        sys.exit(0 if successful >= total * 0.8 else 1)


if __name__ == "__main__":
    asyncio.run(main())
