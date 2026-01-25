"""
Meta-SSOT Reporter - Console/file output formatting

Handles:
- Health check report printing
- Metacognitive layer output
"""


def print_report(results: dict) -> None:
    """건강 체크 결과 출력"""
    print("=" * 60)
    print("  META-SSOT HEALTH REPORT (메타인지 자기참조 시스템)")
    print("=" * 60)
    print(f"  Timestamp: {results['timestamp']}")
    print(f"  Overall Status: {results['overall_status']}")
    print("-" * 60)

    for system in results["systems"]:
        status_icon = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "STALE": "🕐",
            "MISSING": "❌",
            "NOT_LOADED": "🔌",
            "ERROR": "💥",
            "SKIP": "⏭️",
            "UNKNOWN": "❓",
        }.get(system["status"], "?")

        exists_icon = "📄" if system["exists"] else "🚫"
        print(f"  {status_icon} {system['name']}")
        print(f"     {exists_icon} {system['path']}")
        print(f"     └─ {system['message']}")
        print()

    print("-" * 60)
    print("  SUMMARY:")
    meta = results["meta"]
    print(f"    Healthy: {meta['healthy']}/{meta['total']}")
    print(f"    Warning: {meta['warning']}")
    print(f"    Stale:   {meta['stale']}")
    print(f"    Missing: {meta['missing']}")
    print(f"    Error:   {meta['error']}")
    print("=" * 60)


def print_metacognitive_report(results: dict, verbose: bool = False) -> None:
    """메타인지 계층 출력"""
    print("\n" + "=" * 60)
    print("  [v2.0] METACOGNITIVE LAYER (메타인지 계층)")
    print("=" * 60)

    metacog = results.get("metacognitive", {})

    # launchd 런타임
    runtime = metacog.get("launchd_runtime", {})
    print(f"\n  🔄 launchd Runtime: {runtime.get('loaded', 0)}/{runtime.get('total', 0)} loaded")
    for svc in runtime.get("services", []):
        icon = "✅" if svc["loaded"] else "❌"
        exit_info = f" (exit={svc['last_exit_code']})" if svc.get("last_exit_code") else ""
        print(f"     {icon} {svc['name']}{exit_info}")

    # 교차 검증
    xval = metacog.get("cross_validation", {})
    print(f"\n  🔍 Cross-Validation: {xval.get('passed', 0)}/{xval.get('total_checks', 0)} passed")
    for v in xval.get("validations", []):
        icon = "✅" if v.get("valid") else "❌"
        print(f"     {icon} {v['check']}")

    # 자가 치유 결과
    if "self_heal" in metacog:
        heal = metacog["self_heal"]
        mode = "DRY-RUN" if heal["dry_run"] else "EXECUTED"
        print(f"\n  🩹 Self-Heal ({mode}): {heal['healed']} healed, {heal['pending']} pending")
        for action in heal.get("actions", []):
            icon = "✅" if action.get("executed") else "⏳"
            print(f"     {icon} {action['service']}: {action['issue']}")
            if verbose:
                print(f"        → {action['action']}")

    print("\n" + "=" * 60)
