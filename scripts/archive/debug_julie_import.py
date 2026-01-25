import sys

# Add package root to path
sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))

try:
    print("Attempting to import Julie Royal Router...")
    from AFO.api.routers.julie_royal import router

    print("✅ Success! Router imported.")
    for route in router.routes:
        print(f" - {route.path} {route.methods}")
except Exception as e:
    print(f"❌ Import Failed: {e}")
    import traceback

    traceback.print_exc()
