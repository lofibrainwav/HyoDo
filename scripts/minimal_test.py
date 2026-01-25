#!/usr/bin/env python3
"""
Minimal test to isolate Skills API registration issue
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

# Disable AntiGravity for minimal testing
os.environ["DISABLE_ANTIGRAVITY"] = "1"


def test_minimal_app() -> None:
    """Test with minimal FastAPI app"""
    print("🧪 TESTING MINIMAL FASTAPI APP")

    from fastapi import FastAPI

    # Create minimal app
    app = FastAPI(title="Test App")

    # Manually add Skills router
    try:
        from AFO.api.compat import skills_router

        print("✅ Skills router imported from compat")

        if skills_router:
            app.include_router(skills_router, prefix="/api/skills", tags=["Skills"])
            print("✅ Skills router registered manually")

            # Check registered routes
            skills_routes = [
                r for r in app.routes if hasattr(r, "path") and "skills" in r.path.lower()
            ]
            print(f"📊 Skills routes: {len(skills_routes)}")

            for route in skills_routes:
                print(f"   - {route.path} ({list(getattr(route, 'methods', set()))})")

            return len(skills_routes) > 0
        print("❌ Skills router is None")
        return False

    except Exception as e:
        print(f"❌ Manual registration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_full_setup() -> None:
    """Test with full AFO setup but minimal initialization"""
    print("\n🧪 TESTING FULL AFO SETUP")

    try:
        # Test config
        from AFO.api.config import get_app_config

        app = get_app_config()
        print("✅ App created")

        # Test middleware (skip if problematic)
        try:
            from AFO.api.middleware import setup_middleware

            setup_middleware(app)
            print("✅ Middleware setup")
        except Exception as e:
            print(f"⚠️ Middleware setup skipped: {e}")

        # Test router setup
        from AFO.api.routers import setup_routers

        setup_routers(app)
        print("✅ Routers setup")

        # Check skills routes
        skills_routes = [r for r in app.routes if hasattr(r, "path") and "skills" in r.path.lower()]
        print(f"📊 Skills routes after full setup: {len(skills_routes)}")

        for route in skills_routes:
            print(f"   - {route.path}")

        return len(skills_routes) > 0

    except Exception as e:
        print(f"❌ Full setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 AFO Kingdom Skills API Minimal Test")
    print("=" * 50)

    # Test 1: Minimal manual registration
    minimal_success = test_minimal_app()

    # Test 2: Full AFO setup
    full_success = test_full_setup()

    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    print(f"Minimal test: {'✅ PASS' if minimal_success else '❌ FAIL'}")
    print(f"Full setup: {'✅ PASS' if full_success else '❌ FAIL'}")

    if minimal_success and not full_success:
        print("\n🔍 ISSUE: Skills router works manually but fails in full setup")
        print("   Possible causes:")
        print("   - Router conflict during setup_routers()")
        print("   - Initialization order issue")
        print("   - Duplicate route registration")

    elif not minimal_success:
        print("\n🔍 ISSUE: Skills router has fundamental problems")
        print("   Check AFO.api.routers.skills implementation")

    else:
        print("\n🎉 SUCCESS: Skills API registration works correctly!")

    print("=" * 50)
