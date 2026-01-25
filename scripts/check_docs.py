#!/usr/bin/env python3
"""문서 완전성 검증 스크립트"""

import os
import sys


def check_documentation():
    """필수 문서 파일들의 존재 여부 확인"""
    docs = [
        "README.md",
        "AUDIT_README.md",
        "docs/AFO_ROYAL_LIBRARY.md",
        "docs/AFO_SSOT_CORE_DEFINITIONS.md",
        "AGENTS.md",
        "CLAUDE.md",
    ]

    missing_docs = []

    print("📚 Checking documentation completeness...")

    for doc in docs:
        if os.path.exists(doc):
            print(f"✅ {doc}")
        else:
            print(f"❌ {doc} - MISSING")
            missing_docs.append(doc)

    if missing_docs:
        print(f"\n❌ Missing required documentation: {len(missing_docs)} files")
        for doc in missing_docs:
            print(f"  - {doc}")
        return False
    else:
        print("\n🎉 All required documentation is present")
        return True


if __name__ == "__main__":
    success = check_documentation()
    sys.exit(0 if success else 1)
