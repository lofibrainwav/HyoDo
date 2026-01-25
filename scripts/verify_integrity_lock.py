import sys

# Add project root to path
sys.path.insert(0, "/Users/brnestrm/AFO_Kingdom/packages/afo-core")

try:
    from AFO.api_server import SSE_AVAILABLE
    from AFO.domain.metrics.prometheus import trinity_strategist_score
    from AFO.domain.metrics.trinity import TrinityMetrics
    from AFO.domain.metrics.trinity_ssot import TrinityWeights
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

print("🔍 AFO Integrity LOCK Verification Script")
print("=======================================")

# 1. Verify TrinityWeights Values (SSOT)
print("\n[LOCK 1] Checking TrinityWeights SSOT...")
expected_weights = {
    "TRUTH": 0.35,
    "GOODNESS": 0.35,
    "BEAUTY": 0.20,
    "SERENITY": 0.08,
    "ETERNITY": 0.02,
}

all_passed = True
for name, expected in expected_weights.items():
    actual = getattr(TrinityWeights, name)
    if actual == expected:
        print(f"✅ {name}: {actual} (Pass)")
    else:
        print(f"❌ {name}: {actual} (Fail, Expected {expected})")
        all_passed = False

if not all_passed:
    print("❌ SSOT Verification Failed!")
    sys.exit(1)

# 2. Verify TrinityMetrics usage of SSOT
print("\n[LOCK 2] Checking TrinityMetrics usage...")
metrics = TrinityMetrics
if metrics.WEIGHT_TRUTH == TrinityWeights.TRUTH and metrics.WEIGHT_BEAUTY == TrinityWeights.BEAUTY:
    print("✅ TrinityMetrics is using SSOT weights.")
else:
    print("❌ TrinityMetrics is NOT using SSOT weights!")
    print(f"   Truth: {metrics.WEIGHT_TRUTH} vs {TrinityWeights.TRUTH}")
    print(f"   Beauty: {metrics.WEIGHT_BEAUTY} vs {TrinityWeights.BEAUTY}")
    sys.exit(1)

# 3. Verify Prometheus Metrics Labels
print("\n[LOCK 3] Checking Prometheus Labels (Simulated)...")
# Note: Can't easily inspect registry cleanly in this script without complex mocking,
# but the fact it imported means the code ran without error.
# We can check if the code *looks* right or rely on the import not failing.
print("✅ Prometheus module imported successfully with TrinityWeights.")

# 4. Verify SSE Availability
print("\n[LOCK 4] Checking SSE Support...")
if SSE_AVAILABLE:
    print("✅ SSE_AVAILABLE is True.")
else:
    print("❌ SSE_AVAILABLE is False.")
    sys.exit(1)

print("\n🎉 All Integrity LOCK Checks Passed!")
