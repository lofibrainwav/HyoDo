#!/usr/bin/env python3
"""
AFO Import 변환 스크립트
from AFO.* → 상대 import로 변환

사용법:
python scripts/fix_afo_imports.py --dry-run    # 미리보기
python scripts/fix_afo_imports.py --apply      # 실제 적용
"""

import argparse
import re
from pathlib import Path


class AFOImportFixer:
    """AFO 절대 import를 상대 import로 변환하는 클래스"""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)
        self.conversion_map = self._build_conversion_map()

    def _build_conversion_map(self) -> dict[str, str]:
        """AFO 모듈 경로를 상대 경로로 변환하는 매핑 생성"""
        return {
            # packages/afo-core/AFO/ 기준 상대 경로
            "AFO.config": "..config",
            "AFO.services": "..services",
            "AFO.api": "..api",
            "AFO.domain": "..domain",
            "AFO.utils": "..utils",
            "AFO.schemas": "..schemas",
            "AFO.models": "..models",
            "AFO.chancellor": "..chancellor",
            "AFO.observability": "..observability",
            "AFO.scholars": "..scholars",
            "AFO.tigers": "..tigers",
            "AFO.agents": "..agents",
            "AFO.aicpa": "..aicpa",
            "AFO.julie_cpa": "..julie_cpa",
            "AFO.start": "..start",
            "AFO.llm_router": "..llm_router",
            "AFO.llms": "..llms",
            "AFO.api_wallet": "..api_wallet",
            "AFO.input_server": "..input_server",
            "AFO.afo_skills_registry": "..afo_skills_registry",
            "AFO.api_server": "..api_server",
            "AFO.chancellor_graph": "..chancellor_graph",
            "AFO.kms": "..kms",
            "AFO.constitution": "..constitution",
            "AFO.guardians": "..guardians",
            "AFO.genui": "..genui",
            "AFO.health": "..health",
            "AFO.legacy": "..legacy",
            "AFO.browser_auth": "..browser_auth",
            "AFO.config.antigravity": "..config.antigravity",
            "AFO.config.settings": "..config.settings",
            "AFO.services.trinity_calculator": "..services.trinity_calculator",
            "AFO.services.database": "..services.database",
            "AFO.api.compat": "..api.compat",
            "AFO.api.config": "..api.config",
            "AFO.domain.metrics.trinity": "..domain.metrics.trinity",
            "AFO.utils.redis_connection": "..utils.redis_connection",
            "AFO.utils.cache_utils": "..utils.cache_utils",
            "AFO.scholars.yeongdeok": "..scholars.yeongdeok",
        }

    def find_afo_imports(self, file_path: Path) -> list[tuple[str, str]]:
        """파일에서 AFO import 문장들을 찾아서 변환 매핑 반환"""
        conversions = []

        try:
            content = Path(file_path).read_text(encoding="utf-8")

            # from AFO.xxx import yyy 패턴 찾기
            pattern = r"from\s+(AFO(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)\s+import"
            matches = re.findall(pattern, content)

            for match in matches:
                if match in self.conversion_map:
                    # 원본 import 문장 찾기
                    import_pattern = rf"from\s+{re.escape(match)}\s+import.*"
                    import_match = re.search(import_pattern, content, re.MULTILINE)
                    if import_match:
                        original_line = import_match.group(0)
                        new_import = original_line.replace(
                            f"from {match}", f"from {self.conversion_map[match]}"
                        )
                        conversions.append((original_line, new_import))

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return conversions

    def convert_file(self, file_path: Path, dry_run: bool = True) -> bool:
        """단일 파일 변환"""
        conversions = self.find_afo_imports(file_path)

        if not conversions:
            return False

        if dry_run:
            print(f"\n📄 {file_path.relative_to(self.root_dir)}:")
            for original, converted in conversions:
                print(f"  ❌ {original}")
                print(f"  ✅ {converted}")
        else:
            try:
                content = Path(file_path).read_text(encoding="utf-8")

                for original, converted in conversions:
                    content = content.replace(original, converted)

                Path(file_path).write_text(content, encoding="utf-8")

                print(
                    f"✅ Converted {len(conversions)} imports in {file_path.relative_to(self.root_dir)}"
                )

            except Exception as e:
                print(f"❌ Error converting {file_path}: {e}")
                return False

        return len(conversions) > 0

    def find_all_files_with_afo_imports(self) -> list[Path]:
        """AFO import를 사용하는 모든 파일 찾기"""
        files_with_imports = []

        # 변환 대상 디렉토리들
        target_dirs = [
            self.root_dir / "packages" / "afo-core",
            self.root_dir / "scripts",
            self.root_dir / "tests",
        ]

        for target_dir in target_dirs:
            if not target_dir.exists():
                continue

            for file_path in target_dir.rglob("*.py"):
                if self.find_afo_imports(file_path):
                    files_with_imports.append(file_path)

        return files_with_imports

    def find_relative_imports(self, file_path: Path) -> list[tuple[str, str]]:
        """상대 import 문장들을 찾아서 절대 import로 변환 매핑 반환"""
        conversions = []

        try:
            content = Path(file_path).read_text(encoding="utf-8")

            # from ..api.config import ... → from AFO.api.config import ...
            # from .api.config import ... → from AFO.api.config import ...

            lines = content.split("\n")
            for i, line in enumerate(lines):
                # 상대 import 라인 찾기
                if line.strip().startswith("from ") and ("from .." in line or "from ." in line):
                    original_line = line
                    # 상대 import를 절대 import로 변환
                    if "from ..." in line:
                        # ... (세 개의 점) → AFO.
                        new_line = line.replace("from ...", "from AFO.", 1)
                    elif "from .." in line:
                        # .. (두 개의 점) → AFO.
                        new_line = line.replace("from ..", "from AFO.", 1)
                    elif "from ." in line:
                        # . (한 개의 점) → AFO.
                        new_line = line.replace("from .", "from AFO.", 1)
                    else:
                        continue

                    conversions.append((original_line, new_line))

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return conversions

    def convert_all(self, dry_run: bool = True, reverse: bool = False) -> tuple[int, int]:
        """모든 파일 변환 (정방향 또는 역방향)"""
        if reverse:
            # 역방향: 상대 import → 절대 import
            files = self.find_all_files_with_relative_imports()
            print("\n🔄 REVERSE MODE: Converting relative imports back to absolute")
        else:
            # 정방향: 절대 import → 상대 import
            files = self.find_all_files_with_afo_imports()
            print("\n🔍 FORWARD MODE: Converting absolute imports to relative")

        converted_count = 0
        total_imports = 0

        print(f"Found {len(files)} files to process")

        for file_path in sorted(files):
            if reverse:
                conversions = self.find_relative_imports(file_path)
            else:
                conversions = self.find_afo_imports(file_path)

            if conversions:
                total_imports += len(conversions)
                if self.convert_file_reverse(file_path, conversions, dry_run):
                    converted_count += 1

        return converted_count, total_imports

    def find_all_files_with_relative_imports(self) -> list[Path]:
        """상대 import를 사용하는 모든 파일 찾기"""
        files_with_imports = []

        # 변환 대상 디렉토리들
        target_dirs = [
            self.root_dir / "packages" / "afo-core",
            self.root_dir / "scripts",
            self.root_dir / "tests",
        ]

        # 제외할 디렉토리들
        exclude_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            "node_modules",
            "dist",
            "build",
            "*.egg-info",
        ]

        for target_dir in target_dirs:
            if not target_dir.exists():
                continue

            for file_path in target_dir.rglob("*.py"):
                # 제외 패턴 확인
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if exclude_pattern in str(file_path):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                if self.find_relative_imports(file_path):
                    files_with_imports.append(file_path)

        return files_with_imports

    def convert_file_reverse(
        self, file_path: Path, conversions: list[tuple[str, str]], dry_run: bool = True
    ) -> bool:
        """역방향 변환: 상대 import → 절대 import"""
        if not conversions:
            return False

        if dry_run:
            print(f"\n📄 {file_path.relative_to(self.root_dir)}:")
            for original, converted in conversions:
                print(f"  ❌ {original}")
                print(f"  ✅ {converted}")
        else:
            try:
                content = Path(file_path).read_text(encoding="utf-8")

                for original, converted in conversions:
                    content = content.replace(original, converted)

                Path(file_path).write_text(content, encoding="utf-8")

                print(
                    f"✅ Reverse converted {len(conversions)} imports in {file_path.relative_to(self.root_dir)}"
                )

            except Exception as e:
                print(f"❌ Error reverse converting {file_path}: {e}")
                return False

        return len(conversions) > 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert AFO absolute imports to relative imports")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--apply", action="store_true", help="Apply the changes")
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse conversion: relative imports → absolute imports",
    )
    parser.add_argument("--root-dir", default=".", help="Root directory to search")

    args = parser.parse_args()

    if not (args.dry_run or args.apply):
        print("❌ Specify either --dry-run or --apply")
        return

    fixer = AFOImportFixer(args.root_dir)

    if args.dry_run:
        if args.reverse:
            print("🔄 REVERSE DRY RUN MODE - Showing relative → absolute conversion:")
        else:
            print("🔍 FORWARD DRY RUN MODE - Showing absolute → relative conversion:")
        converted, total = fixer.convert_all(dry_run=True, reverse=args.reverse)
        print(
            f"\n📊 Summary: {converted} files would be changed, {total} imports would be converted"
        )

    elif args.apply:
        if args.reverse:
            print("⚠️  REVERSE APPLY MODE - Converting relative imports back to absolute!")
        else:
            print("⚠️  FORWARD APPLY MODE - Converting absolute imports to relative!")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Operation cancelled")
            return

        converted, total = fixer.convert_all(dry_run=False, reverse=args.reverse)
        if args.reverse:
            print(f"\n✅ Successfully reverse converted {total} imports in {converted} files")
        else:
            print(f"\n✅ Successfully converted {total} imports in {converted} files")


if __name__ == "__main__":
    main()
