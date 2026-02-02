import os
import pathlib
import sys

# Add package root to path
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.security.vault_manager import vault
from config.settings import settings

print("🛡️ Vault Integration Verification 🛡️")
print("-" * 40)

# 1. Test Fetching a known key (ENV fallback likely active)
openai_key = vault.get_secret("OPENAI_API_KEY")
print(
    f"🔑 OPENAI_API_KEY: {'[FOUND]' if openai_key else '[MISSING]'} (Length: {len(openai_key) if openai_key else 0})"
)

# 2. Test Fetching a non-existent key
dummy_key = vault.get_secret("NON_EXISTENT_KEY_12345")
print(f"👻 NON_EXISTENT_KEY: {'[FOUND?!]' if dummy_key else '[CORRECTLY MISSING]'}")

# 3. Test Vault Priority (Inject a fake key into Vault and see if it overrides Env/Default)
test_key_name = "TEST_VAULT_PRIORITY_KEY"
test_val = "secret_from_vault_db"

print(f"\n🧪 Injecting '{test_key_name}' into Vault...")
try:
    # Remove if exists first (cleanup)
    if vault.wallet:
        vault.wallet.delete(test_key_name)

    vault.set_secret(test_key_name, test_val, service="test")

    # Retrieve
    retrieved_val = vault.get_secret(test_key_name)

    if retrieved_val == test_val:
        print(f"✅ Vault Priority Check PASSED: Retrieved '{retrieved_val}'")
    else:
        print(f"❌ Vault Priority Check FAILED: Expected '{test_val}', got '{retrieved_val}'")

    # Cleanup
    if vault.wallet:
        vault.wallet.delete(test_key_name)
        print("🧹 Cleanup complete.")

except Exception as e:
    print(f"⚠️ Test Exception: {e}")

print("-" * 40)
print("Verifying Dependencies:")
print(f"Settings Loaded: {settings.POSTGRES_DB}")
print(f"Wallet Connected: {vault.wallet.use_db if vault.wallet else 'No'}")
