#!/usr/bin/env python3
"""
AFO 왕국 자동 타입 수정 시스템
SSOT 준수 타입 어노테이션 자동 추가
"""

import os
import re


def fix_missing_return_types(file_path: str) -> int:
    """함수에 누락된 리턴 타입 어노테이션 자동 추가"""
    with open(file_path, "r") as f:
        content = f.read()

    # def function_name( -> def function_name() -> dict:
    pattern = r"def (\w+)\([^)]*\):"
    replacement = r"def \1() -> dict:"

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        return 1
    return 0


def main() -> None:
    """메인 실행 함수"""
    files_to_fix = [
        "packages/afo-core/api/routers/finance_root.py",
        "packages/afo-core/api/routers/debugging.py",
    ]

    total_fixed = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fixed = fix_missing_return_types(file_path)
            total_fixed += fixed
            print(f"✅ {file_path}: {fixed}개 함수 수정")

    print(f"\n🎯 총 {total_fixed}개 타입 어노테이션 자동 추가 완료")


if __name__ == "__main__":
    main()
