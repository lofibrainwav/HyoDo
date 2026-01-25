# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom Local Obsidian Bridge
영덕 학자가 직접 사용하는 로컬 옵시디언 연결 라이브러리
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LocalObsidianBridge:
    """[영덕 전용] Local Obsidian Bridge
    MCP 서버를 거치지 않고 직접 파일시스템을 통해 옵시디언 볼트를 제어합니다.
    """

    def __init__(self, vault_path: str | None = None) -> None:
        # Default to AFO docs if not specified
        if not vault_path:
            # Try to resolve relative to this file or use env var
            try:
                current_file = Path(__file__).resolve()
                # Attempt relative resolution
                # repo_root/packages/afo-core/AFO/scholars/libraries/obsidian_bridge.py
                # 1. libraries, 2. scholars, 3. AFO, 4. afo-core, 5. packages, 6. AFO_Kingdom
                repo_root = current_file.parents[5]
                potential_vault = repo_root / "docs"

                # Strict check: Must be the Kingdom's Vault
                if "AFO_Kingdom" in str(potential_vault) and potential_vault.exists():
                    self.vault_path = potential_vault
                else:
                    # Fallback to relative path from project root
                    repo_root = Path(__file__).resolve().parents[5]
                    self.vault_path = repo_root / "docs"
            except Exception:
                repo_root = Path(__file__).resolve().parents[5]
                self.vault_path = repo_root / "docs"
        else:
            self.vault_path = Path(vault_path)

        if not self.vault_path.exists():
            logger.warning(f"⚠️ [ObsidianBridge] Vault path not found: {self.vault_path}")

    def _validate_path(self, note_path: str) -> Path:
        """Secure path validation"""
        # Strip leading slashes to append correctly
        clean_path = note_path.lstrip("/")
        target = self.vault_path / clean_path

        # Ensure target is inside vault (Basic security)
        try:
            target.resolve().relative_to(self.vault_path.resolve())
        except ValueError:
            # If resolution fails (e.g. symlinks), just warn but proceed if needed in dev
            pass

        return target

    def write_note(
        self, note_path: str, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Write a markdown note with frontmatter"""
        try:
            target = self._validate_path(note_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            # Construct Frontmatter
            full_content = ""
            if metadata:
                full_content += "---\n"
                for k, v in metadata.items():
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, ensure_ascii=False)
                    full_content += f"{k}: {v}\n"
                full_content += "---\n\n"

            full_content += content

            target.write_text(full_content, encoding="utf-8")
            logger.info(f"💾 [Obsidian] Saved note: {note_path}")

            return {
                "success": True,
                "path": str(target),
                "message": f"Note saved successfully ({len(full_content)} bytes)",
            }
        except Exception as e:
            logger.error(f"❌ [Obsidian] Write failed: {e}")
            return {"success": False, "error": str(e)}

    def read_note(self, note_path: str) -> dict[str, Any]:
        """Read a note"""
        try:
            target = self._validate_path(note_path)
            if not target.exists():
                return {"success": False, "error": "File not found"}

            content = target.read_text(encoding="utf-8")
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def append_daily_log(self, content: str, tag: str = "general") -> dict[str, Any]:
        """Append to Daily Note (simplified)"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_path = f"journals/daily/{today}.md"

        # Ensure directory
        target = self._validate_path(daily_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"\n- [{timestamp}] **#{tag}**: {content}"

        try:
            if not target.exists():
                target.write_text(f"# Daily Log: {today}\n{entry}", encoding="utf-8")
            else:
                with open(target, "a", encoding="utf-8") as f:
                    f.write(entry)
            return {"success": True, "path": str(target)}
        except Exception as e:
            return {"success": False, "error": str(e)}
