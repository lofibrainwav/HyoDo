#!/usr/bin/env python3
"""
패키지 설치 상태 체크 스크립트
Sequential Thinking Phase 2: 실제 import 테스트
"""

import importlib
import sys
from pathlib import Path

# packages/afo-core를 경로에 추가
core_path = Path(__file__).parent.parent / "packages" / "afo-core"
sys.path.insert(0, str(core_path))

# pyproject.toml에서 선언된 의존성
REQUIRED_PACKAGES = {
    # Core dependencies
    "redis": "redis",
    "langchain": "langchain",
    "openai": "openai",
    "psutil": "psutil",
    "qdrant_client": "qdrant-client",
    "pgvector": "pgvector",
    "pymongo": "pymongo",
    "numpy": "numpy",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "httpx": "httpx",
    "watchdog": "watchdog",
    "google.genai": "google-genai",
    # Optional but commonly used
    "anthropic": "anthropic",
    "sentence_transformers": "sentence-transformers",
    "ragas": "ragas",
    "langgraph": "langgraph",
    "langchain_community": "langchain-community",
    "langchain_core": "langchain-core",
}

# 코드에서 실제 사용하는 import 패턴
    "redis": ["redis"],
    "langchain": [
        "langchain",
        "langchain.chains",
        "langchain.llms",
        "langchain.prompts",
    ],
    "openai": ["openai"],
    "psutil": ["psutil"],
    "qdrant_client": ["qdrant_client"],
    "pgvector": ["pgvector"],
    "pymongo": ["pymongo"],
    "numpy": ["numpy"],
    "fastapi": ["fastapi"],
    "uvicorn": ["uvicorn"],
    "pydantic": ["pydantic"],
    "pydantic_settings": ["pydantic_settings"],
    "httpx": ["httpx"],
    "watchdog": ["watchdog", "watchdog.observers", "watchdog.events"],
    "google.genai": ["google.genai"],
    "anthropic": ["anthropic"],
    "sentence_transformers": ["sentence_transformers"],
    "ragas": ["ragas"],
    "langgraph": ["langgraph"],
    "langchain_community": ["langchain_community"],
    "langchain_core": ["langchain_core"],
}


def check_package(module_name: str, package_name: str) -> tuple[bool, str | None]:
    """패키지 설치 여부 확인"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main() -> None:
    """메인 함수"""
    print("=" * 80)
    print("🔍 AFO 왕국 패키지 설치 상태 체크")
    print("=" * 80)
    print()

    installed = []
    missing = []
    errors = []

    for module_name, package_name in REQUIRED_PACKAGES.items():
        is_installed, error = check_package(module_name, package_name)
        if is_installed:
            installed.append((module_name, package_name))
            print(f"✅ {package_name:30s} ({module_name})")
        else:
            missing.append((module_name, package_name))
            errors.append((package_name, error))
            print(f"❌ {package_name:30s} ({module_name}) - {error}")

    print()
    print("=" * 80)
    print(f"📊 요약: {len(installed)}개 설치됨, {len(missing)}개 누락")
    print("=" * 80)

    if missing:
        print()
        print("📦 설치 필요한 패키지:")
        print("poetry add " + " ".join([pkg for _, pkg in missing]))
        print()
        print("또는 개별 설치:")
        for module_name, package_name in missing:
            print(f"  poetry add {package_name}")

    return len(missing) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
