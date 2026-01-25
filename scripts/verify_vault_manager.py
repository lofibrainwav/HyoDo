import os
import pathlib
import sys

# 프로젝트 루트 경로 추가
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.security.vault_manager import VaultManager, vault


def verify_vault_manager() -> None:
    print("=== VaultManager Verification ===")

    # Check Singleton
    v1 = VaultManager.get_instance()
    v2 = VaultManager.get_instance()
    assert v1 is v2, "Singleton check failed"
    print("✅ Singleton Pattern Verified")

    # Check Fallback (Since we don't have Vault, it should use Env)
    print("\n[Step 1] Verifying Get Secret (Fallback)...")
    # Test value - not a real secret (safe for testing)
    test_value = "EnvValue123"
    os.environ["TEST_SECRET_KEY"] = test_value

    val = vault.get_secret("TEST_SECRET_KEY", default="DefaultValue")
    print(f"Result: {val}")

    assert val == "EnvValue123", "Fallback to Env failed"
    print("✅ Fallback to Environment Verified")

    # Check Default
    val_default = vault.get_secret("NON_EXISTENT_KEY", default="MyDefault")
    assert val_default == "MyDefault", "Default value failed"
    print("✅ Default Value Verified")

    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    verify_vault_manager()
