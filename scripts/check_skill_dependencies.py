#!/usr/bin/env python3
"""
스킬 의존성 체크 스크립트
Sequential Thinking Phase 2: 스킬별 필요한 패키지 확인
"""

import sys
from pathlib import Path

# packages/afo-core를 경로에 추가
core_path = Path(__file__).parent.parent / "packages" / "afo-core"
sys.path.insert(0, str(core_path))

from AFO.afo_skills_registry import register_core_skills

# Python 패키지 매핑 (스킬 의존성 → 실제 패키지명)
PACKAGE_MAPPING = {
    "openai_api": "openai",
    "transcript_mcp": "mcp",
    "postgresql": "psycopg2",
    "web3.py": "web3",
    "suno-api": "suno",  # sunoai 패키지는 import 시 suno
    "sentence-transformers": "sentence_transformers",
    "eth-account": "eth_account",
    "ai-analysis": None,  # 내부 모듈
    "react": None,  # 프론트엔드
    "iframe": None,  # 프론트엔드
    "git": "git",  # 시스템 도구 (Python Wrapper)
    "docker": "docker",  # 시스템 도구 (Python Wrapper)
    "redis": "redis",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "ragas": "ragas",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "sympy": "sympy",
    "markdown": "markdown",
    "frontmatter": "frontmatter",  # python-frontmatter는 import 시 frontmatter
    "chromadb": "chromadb",
    "neo4j": "neo4j",
    "boto3": "boto3",
    "requests": "requests",
    "kafka": "kafka",  # kafka-python은 import 시 kafka
    "ruff": "ruff",
    "pytest": "pytest",
    "mcp": "mcp",
    # Deep Research 발견 항목 (2025-12-21 추가)
    "anthropic": "anthropic",
    "playwright": "playwright",
    "qdrant-client": "qdrant_client",
    "psutil": "psutil",
    "prometheus-client": "prometheus_client",
    "sse-starlette": "sse_starlette",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "watchdog": "watchdog",
}


def check_package(package_name: str) -> tuple[bool, str | None]:
    """패키지 설치 여부 확인"""
    try:
        __import__(package_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_custom_verification(dep_name: str) -> tuple[bool, str]:
    """비-Python 의존성 (프론트엔드 등) 커스텀 체크"""
    repo_root = Path(__file__).parent.parent

    if dep_name in {"react", "iframe"}:
        # Dashboard 패키지 존재 확인
        dashboard_path = repo_root / "packages" / "dashboard" / "package.json"
        if dashboard_path.exists():
            return True, "Dashboard (Next.js) Verified"
        return False, "Dashboard Package Missing"

    if dep_name == "ai-analysis":
        # AFO Core 존재 확인
        core_path = repo_root / "packages" / "afo-core" / "AFO"
        if core_path.exists():
            return True, "AFO Core Analysis Verified"
        return False, "AFO Core Missing"

    return False, "Unknown Custom Dependency"


def main() -> None:
    """메인 함수"""
    print("=" * 80)
    print("🔍 AFO 왕국 스킬 의존성 체크")
    print("=" * 80)
    print()

    # 스킬 등록
    registry = register_core_skills()
    skills = registry.list_all()

    print(f"📋 등록된 스킬: {len(skills)}개\n")

    # 모든 스킬의 의존성 수집
    all_dependencies = set()
    for skill in skills:
        if skill.dependencies:
            all_dependencies.update(skill.dependencies)

    # Deep Research 발견 항목 추가 (시스템 코어)
    deep_research_deps = {
        "anthropic",
        "playwright",
        "qdrant-client",
        "psutil",
        "prometheus-client",
        "sse-starlette",
        "fastapi",
        "uvicorn",
        "watchdog",
    }
    all_dependencies.update(deep_research_deps)

    print(f"📦 스킬 의존성 총 {len(all_dependencies)}개\n")

    # 패키지 매핑 및 확인
    installed = []
    missing = []
    optional = []

    for dep in sorted(all_dependencies):
        package_name = PACKAGE_MAPPING.get(dep, dep)

        if package_name is None:
            # 커스텀 검증 시도
            is_verified, message = check_custom_verification(dep)
            if is_verified:
                installed.append((dep, message))
                print(f"✅ {dep:30s} ({message})")
            else:
                optional.append(dep)
                print(f"ℹ️  {dep:30s} (시스템/내부 모듈)")
            continue

        is_installed, error = check_package(package_name)
        if is_installed:
            installed.append((dep, package_name))
            print(f"✅ {package_name:30s} ({dep})")
        else:
            missing.append((dep, package_name))
            print(f"❌ {package_name:30s} ({dep}) - {error}")

    print()
    print("=" * 80)
    print("📊 요약:")
    print(f"  ✅ 설치됨: {len(installed)}개")
    print(f"  ❌ 누락: {len(missing)}개")
    print(f"  ℹ️  선택적: {len(optional)}개")
    print("=" * 80)

    if missing:
        print()
        print("📦 설치 필요한 패키지:")
        packages_to_install = [pkg for _, pkg in missing]
        print("poetry add " + " ".join(packages_to_install))

    return len(missing) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
