from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from index_obsidian_to_qdrant import index_obsidian_vault
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from config import (
    OBSIDIAN_VAULT_PATH,
    QDRANT_COLLECTION_NAME,
    QDRANT_URL,
    SYNC_INTERVAL,
    SYNC_STATE_FILE,
)

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
# mypy: ignore-errors
"""옵시디언 vault 자동 동기화
파일 변경 감지 및 자동 재인덱싱
"""


# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


class ObsidianVaultHandler(FileSystemEventHandler):
    """옵시디언 vault 파일 변경 핸들러"""

    def __init__(self, vault_path: Path, sync_state_file: Path) -> None:
        self.vault_path = vault_path
        self.sync_state_file = sync_state_file
        self.file_hashes = self._load_sync_state()
        self.changed_files = set()
        self.last_sync = time.time()

    def _load_sync_state(self) -> dict[str, str]:
        """동기화 상태 로드"""
        if self.sync_state_file.exists():
            try:
                with open(self.sync_state_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_sync_state(self) -> None:
        """동기화 상태 저장"""
        try:
            with open(self.sync_state_file, "w") as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️  상태 저장 실패: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
        except Exception:
            return ""

    def on_modified(self, event) -> None:
        """파일 수정 이벤트"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != ".md":
            return

        # vault 내부 파일만 처리
        try:
            rel_path = file_path.relative_to(self.vault_path)
        except ValueError:
            return

        # 제외 패턴 확인
        if any(pattern in str(rel_path) for pattern in [".obsidian", "templates"]):
            return

        # 해시 확인
        current_hash = self._get_file_hash(file_path)
        stored_hash = self.file_hashes.get(str(rel_path))

        if current_hash != stored_hash:
            self.changed_files.add(str(rel_path))
            self.file_hashes[str(rel_path)] = current_hash
            print(f"📝 변경 감지: {rel_path}")

    def on_created(self, event) -> None:
        """파일 생성 이벤트"""
        self.on_modified(event)

    def on_deleted(self, event) -> None:
        """파일 삭제 이벤트"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != ".md":
            return

        try:
            rel_path = file_path.relative_to(self.vault_path)
            if str(rel_path) in self.file_hashes:
                del self.file_hashes[str(rel_path)]
                print(f"🗑️  삭제 감지: {rel_path}")
        except ValueError:
            pass

    def should_sync(self) -> bool:
        """동기화 필요 여부 확인"""
        current_time = time.time()
        has_changes = len(self.changed_files) > 0
        interval_passed = (current_time - self.last_sync) >= SYNC_INTERVAL

        return has_changes and interval_passed

    def sync(self) -> None:
        """동기화 실행"""
        if not self.should_sync():
            return

        print(f"\n🔄 동기화 시작 ({len(self.changed_files)}개 파일 변경)")

        try:
            # 전체 재인덱싱 (증분 업데이트는 복잡하므로)
            index_obsidian_vault(
                vault_path=self.vault_path,
                qdrant_url=QDRANT_URL,
                collection_name=QDRANT_COLLECTION_NAME,
                clear_existing=False,  # 기존 데이터 유지
            )

            self.changed_files.clear()
            self.last_sync = time.time()
            self._save_sync_state()

            print("✅ 동기화 완료\n")
        except Exception as e:
            print(f"❌ 동기화 실패: {e}\n")


def watch_obsidian_vault(vault_path: Path, sync_state_file: Path) -> None:
    """옵시디언 vault 감시 시작"""
    print(f"👀 옵시디언 vault 감시 시작: {vault_path}\n")

    event_handler = ObsidianVaultHandler(vault_path, sync_state_file)
    observer = Observer()
    observer.schedule(event_handler, str(vault_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(10)  # 10초마다 동기화 확인
            event_handler.sync()
    except KeyboardInterrupt:
        print("\n⏹️  감시 중지")
        observer.stop()

    observer.join()
    event_handler._save_sync_state()


def main() -> None:
    """메인 함수"""

    parser = argparse.ArgumentParser(description="옵시디언 vault 자동 동기화")
    parser.add_argument("--vault-path", type=str, default=str(OBSIDIAN_VAULT_PATH))
    parser.add_argument("--state-file", type=str, default=str(SYNC_STATE_FILE))
    parser.add_argument("--initial-sync", action="store_true", help="초기 동기화 실행")

    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    state_file = Path(args.state_file)

    # 초기 동기화
    if args.initial_sync:
        print("🔄 초기 동기화 실행...")
        index_obsidian_vault(
            vault_path=vault_path,
            qdrant_url=QDRANT_URL,
            collection_name=QDRANT_COLLECTION_NAME,
            clear_existing=True,
        )
        print("✅ 초기 동기화 완료\n")

    # 감시 시작
    watch_obsidian_vault(vault_path, state_file)


if __name__ == "__main__":
    main()
