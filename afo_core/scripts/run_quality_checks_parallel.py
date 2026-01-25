# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""AFO 왕국 코드 품질 체크 스크립트 (병렬 실행 - Python 버전)
ruff, pytest, mypy 병렬 실행
"""

import asyncio
import os
import sys
from pathlib import Path

# 색상 정의
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


async def run_command(name: str, command: list[str], description: str) -> tuple[str, bool, str]:
    """명령 실행 (비동기)

    Returns:
        (name, success, output)

    """
    print(f"{BLUE}📋 [병렬] {description} 시작...{NC}")

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        output = stdout.decode("utf-8", errors="replace")
        success = process.returncode == 0
        return (name, success, output)
    except Exception as e:
        return (name, False, f"오류: {e}")


async def check_tool_installed(tool: str) -> bool:
    """도구 설치 확인"""
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            tool,
            "--version",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        return process.returncode == 0
    except Exception:
        return False


async def install_tool(tool: str, package: str) -> bool:
    """도구 설치"""
    print(f"{YELLOW}⚠️  {tool}가 설치되지 않았습니다. 설치 중...{NC}")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            package,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        if process.returncode != 0:
            # --user 실패 시 시스템 설치 시도
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                package,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.wait()
        return process.returncode == 0
    except Exception:
        return False


async def main():
    """메인 함수"""
    script_dir = Path(__file__).parent
    afo_root = script_dir.parent
    os.chdir(afo_root)

    print("=== 🔍 AFO 왕국 코드 품질 체크 (병렬 실행) ===")
    print("")

    # 1. 도구 설치 확인
    print("📦 도구 설치 확인 중...")

    tools = [
        ("ruff", "ruff"),
        ("mypy", "mypy"),
        ("pytest", "pytest"),
    ]

    for tool, package in tools:
        if not await check_tool_installed(tool):
            await install_tool(tool, package)

    print("")

    # 2. 테스트 파일 확인
    tests_dir = afo_root / "tests"
    has_tests = (
        tests_dir.exists()
        and len(list(tests_dir.glob("test_*.py"))) + len(list(tests_dir.glob("*_test.py"))) > 0
    )

    # 3. 병렬 실행 태스크 생성
    tasks = [
        run_command(
            "ruff_lint",
            [sys.executable, "-m", "ruff", "check", "."],
            "Ruff Lint 체크",
        ),
        run_command(
            "ruff_format",
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            "Ruff Format 체크",
        ),
        run_command(
            "mypy",
            [sys.executable, "-m", "mypy", "AFO", "--ignore-missing-imports"],
            "MyPy 타입 체크",
        ),
    ]

    if has_tests:
        tasks.append(
            run_command(
                "pytest",
                [sys.executable, "-m", "pytest", "tests", "-v"],
                "Pytest 테스트",
            )
        )
    else:
        print(f"{YELLOW}⚠️  테스트 파일이 없습니다. tests/ 디렉토리를 생성하세요.{NC}")

    # 4. 병렬 실행
    print("🚀 병렬 실행 시작...")
    print("")

    results = await asyncio.gather(*tasks)

    print("")

    # 5. 결과 출력 및 집계
    failed = False

    for name, success, output in results:
        if name == "ruff_format" and not success:
            # Format은 경고만
            print(f"{YELLOW}⚠️  Ruff Format: 포맷팅 필요{NC}")
            print("   다음 명령으로 자동 포맷팅: ruff format .")
        elif success:
            print(f"{GREEN}✅ {name.replace('_', ' ').title()}: 통과{NC}")
        else:
            print(f"{RED}❌ {name.replace('_', ' ').title()}: 실패{NC}")
            if output.strip():
                print(output)
            failed = True

    # 최종 결과
    print("")
    print("=== 🏁 최종 결과 ===")
    if not failed:
        print(f"{GREEN}✨ 모든 코드 품질 체크 통과!{NC}")
        sys.exit(0)
    else:
        print(f"{RED}❌ 일부 체크 실패{NC}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
