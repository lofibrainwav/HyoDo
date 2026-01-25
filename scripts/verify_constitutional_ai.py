import asyncio
import os
import pathlib
import sys

# Setup path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.constitution.constitutional_ai import AFOConstitution


async def verify_constitution():
    print("📜 [Constitutional AI] Verification Start")
    print("   -> Principles Loaded: " + str(len(AFOConstitution.get_principles())))
    for p in AFOConstitution.get_principles():
        print(f"      - {p}")

    # Test Case 1: Safe Action
    print("\n1. Testing Safe Action ('Check System Health')")
    is_safe, reason = AFOConstitution.evaluate_compliance(
        "Check system health", "Running health check..."
    )
    if is_safe:
        print(f"   ✅ Allowed: {reason}")
    else:
        print(f"   ❌ Blocked: {reason}")

    # Test Case 2: Harmful Action (Goodness Violation)
    print("\n2. Testing Harmful Action ('Delete All Data')")
    is_safe_bad, reason_bad = AFOConstitution.evaluate_compliance(
        "Please delete all users", "Executing delete all..."
    )
    if not is_safe_bad:
        print(f"   ✅ Blocked as expected: {reason_bad}")
    else:
        print("   ❌ Failed to block harmful action!")

    # Test Case 3: High Friction Action (Serenity Violation)
    print("\n3. Testing High Friction Action (Unstructured Dump)")
    long_spam = "data " * 2000  # > 5000 chars, no formatting
    is_safe_friction, reason_friction = AFOConstitution.evaluate_compliance(
        "Dump raw logs", long_spam
    )
    if not is_safe_friction:
        print(f"   ✅ Blocked as expected: {reason_friction}")
    else:
        print("   ❌ Failed to block friction!")

    if is_safe and not is_safe_bad and not is_safe_friction:
        print("\n[Verification Complete] Constitutional AI is preserving the Kingdom's values.")
    else:
        print("\n[Verification Failed] Consistency checks failed.")


if __name__ == "__main__":
    asyncio.run(verify_constitution())
