#!/usr/bin/env python3
"""
AFO 왕국 Syntax 검증 스크립트
pre-commit hook용 간단한 syntax checker

성능 최적화: Staged 파일만 검사 (전체 프로젝트 스캔 대신)
"""

import subprocess
import sys
from pathlib import Path


def get_staged_python_files() -> list[Path]:
    """Git staged Python 파일 목록 가져오기"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=False,
        )
        files = [
            Path(f)
            for f in result.stdout.strip().splitlines()
            if f.endswith(".py") and Path(f).exists()
        ]
        return files
    except Exception:
        return []


def main() -> None:
    # 성능 최적화: Staged 파일만 검사
    staged_files = get_staged_python_files()

    if not staged_files:
        print("ℹ️  No staged Python files to check, skipping syntax validation")
        sys.exit(0)

    print(f"AFO 왕국 Syntax 검증: {len(staged_files)}개 staged 파일 검사 중...")

    errors = []
    for py_file in staged_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            compile(content, str(py_file), "exec")
        except UnicodeDecodeError:
            print(f"⚠️  건너뜀 (디코딩 실패): {py_file}")
            continue
        except SyntaxError as e:
            errors.append(f"{py_file}: {e}")
        except Exception as e:
            errors.append(f"{py_file}: 알 수 없는 오류 - {e}")

    if errors:
        print("❌ Syntax 오류 발견:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ 모든 staged Python 파일 Syntax 정상!")


if __name__ == "__main__":
    main()
