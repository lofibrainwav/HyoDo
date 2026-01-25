"""
Kingdom Core Verification Script
眞 (Truth): 왕국 핵심 장기(Organs)의 건강 상태 검증
"""

import json

import requests

BASE_URL = "http://localhost:8010"

COLORS = {"GREEN": "\033[92m", "RED": "\033[91m", "RESET": "\033[0m", "BOLD": "\033[1m"}


def print_status(component, status_code, data) -> None:
    status_icon = "✅" if status_code == 200 else "❌"
    color = COLORS["GREEN"] if status_code == 200 else COLORS["RED"]
    print(
        f"{status_icon} {COLORS['BOLD']}[{component}]{COLORS['RESET']} Status: {color}{status_code}{COLORS['RESET']}"
    )
    if status_code != 200:
        print(f"   Error: {json.dumps(data, indent=2, ensure_ascii=False)}")
    # else:
    #     print(f"   Msg: {data.get('message', 'OK')}")


def verify_kingdom_core() -> None:
    print(f"\n{COLORS['BOLD']}🏰 AFO Kingdom Core Health Inspection 🏰{COLORS['RESET']}\n")

    endpoints = [
        ("Chancellor (Brain)", "/chancellor/health"),
        ("Trinity (Soul)", "/api/trinity/current"),
        ("Auth (Heart)", "/api/auth/health"),
        ("Users (Liver)", "/api/users/health"),
        ("Intake (Stomach)", "/api/intake/health"),
        ("Personas (Mask)", "/api/personas/health"),
        ("Family (Spleen)", "/api/family/health"),
        ("Five Pillars (Spirit)", "/api/5pillars/current"),  # Using GET mostly
    ]

    all_passed = True

    for name, path in endpoints:
        try:
            res = requests.get(f"{BASE_URL}{path}")
            print_status(name, res.status_code, res.json())
            if res.status_code != 200:
                all_passed = False
        except Exception as e:
            print(f"❌ {COLORS['BOLD']}[{name}]{COLORS['RESET']} Connection Failed: {e}")
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print(
            f"{COLORS['GREEN']}{COLORS['BOLD']}🎉 All Kingdom Core Systems Operational! 🎉{COLORS['RESET']}"
        )
    else:
        print(
            f"{COLORS['RED']}{COLORS['BOLD']}⚠️  Some Systems Require Attention! ⚠️{COLORS['RESET']}"
        )
    print("=" * 40 + "\n")


if __name__ == "__main__":
    verify_kingdom_core()
