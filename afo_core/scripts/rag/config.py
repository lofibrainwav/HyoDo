from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from api_wallet import APIWallet

from AFO.config.settings import get_settings

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
"""
RAG 시스템 설정 파일
리포지토리 구조에 맞게 경로 자동 감지
API Wallet 통합: API 키 자동 로드
"""


def get_repo_root() -> Path:
    """리포지토리 루트 경로 자동 감지"""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent.parent

    if (repo_root / ".git").exists() or (repo_root / "docs").exists():
        return repo_root

    repo_path = os.getenv("AFO_REPO_ROOT")
    if repo_path:
        return Path(repo_path)

    return repo_root


def get_obsidian_vault_path() -> Path:
    """옵시디언 vault 경로 자동 감지"""
    repo_root = get_repo_root()
    vault_path = repo_root / "docs"

    env_vault = os.getenv("OBSIDIAN_VAULT_PATH")
    if env_vault:
        return Path(env_vault)

    return vault_path


def get_sync_state_file() -> Path:
    """동기화 상태 파일 경로"""
    repo_root = get_repo_root()
    return repo_root / ".obsidian_sync_state.json"


def get_openai_api_key() -> str | None:
    """OpenAI API 키 가져오기 (간소화된 버전)"""
    # 환경 변수에서 먼저 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    # API Wallet 시도 (단순화)
    try:
        current_file = Path(__file__).resolve()
        repo_root = current_file.parent.parent.parent
        sys.path.insert(0, str(repo_root))

        wallet = APIWallet()
        possible_names = ["openai", "OPENAI", "OpenAI", "gpt", "GPT"]
        for name in possible_names:
            key = wallet.get(name)
            if key:
                return key
    except Exception:
        pass

    return None


# 설정 값
REPO_ROOT = get_repo_root()
OBSIDIAN_VAULT_PATH = get_obsidian_vault_path()
SYNC_STATE_FILE = get_sync_state_file()

# 중앙 설정 사용 (Phase 1 리팩토링)
try:
    repo_root = Path(__file__).parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    QDRANT_URL = get_settings().QDRANT_URL
except (ImportError, AttributeError):
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME = "obsidian_vault"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SYNC_INTERVAL = 60  # 초

# OpenAI API 키 (환경 변수 또는 API Wallet에서 자동 로드)
OPENAI_API_KEY = get_openai_api_key()

# 환경 변수로 설정 (다른 모듈에서 사용 가능하도록)
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# API Wallet 가용성 확인
try:
    API_WALLET_AVAILABLE = True
except ImportError:
    API_WALLET_AVAILABLE = False


def print_config() -> None:
    """설정 정보 출력"""
    print("📋 RAG 시스템 설정:")
    print(f"  리포지토리 루트: {REPO_ROOT}")
    print(f"  옵시디언 vault: {OBSIDIAN_VAULT_PATH}")
    print(f"  동기화 상태 파일: {SYNC_STATE_FILE}")
    print(f"  Qdrant URL: {QDRANT_URL}")
    print(f"  컬렉션 이름: {QDRANT_COLLECTION_NAME}")
    print(f"  API Wallet: {'✅ 사용 가능' if API_WALLET_AVAILABLE else '❌ 사용 불가'}")
    if OPENAI_API_KEY:
        print(f"  OpenAI API Key: ✅ 설정됨 ({len(OPENAI_API_KEY)} 문자)")
    else:
        print("  OpenAI API Key: ❌ 설정되지 않음")


if __name__ == "__main__":
    print_config()
