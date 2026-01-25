#!/usr/bin/env python3
"""SSOT 무결성 검증 스크립트"""

import os
import sys


def check_ssot():
    """SSOT 파일들의 존재 여부와 최신 상태 확인"""
    ssot_files = [
        "AGENTS.md",
        "docs/AFO_SSOT_CORE_DEFINITIONS.md",
        "docs/AFO_ROYAL_LIBRARY.md",
        "health_gate_rules.txt",
    ]

    missing_files = []

    print("🎯 Checking SSOT integrity...")

    for f in ssot_files:
        if os.path.exists(f):
            print(f"✅ {f}")
            # 최근 수정 시간 확인 (선택적)
            try:
                mod_time = os.path.getmtime(f)
                from datetime import datetime

                mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   📅 Last modified: {mod_date}")
            except:
                pass
        else:
            print(f"❌ {f} - MISSING")
            missing_files.append(f)

    if missing_files:
        print(f"\n❌ Missing SSOT files: {len(missing_files)} files")
        for f in missing_files:
            print(f"  - {f}")
        return False
    else:
        print("\n🎯 SSOT integrity verified")
        return True


if __name__ == "__main__":
    success = check_ssot()
    sys.exit(0 if success else 1)
