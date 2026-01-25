#!/usr/bin/env python3
"""
Debug script to check router registration in AFO Kingdom API Server
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "afo-core"))


def test_direct_import() -> None:
    """Test direct import of skills router"""
    print("=" * 50)
    print("🔍 TESTING DIRECT IMPORT")
    print("=" * 50)

    try:
        print("📦 Importing AFO.api.routers.skills...")
        from AFO.api.routers.skills import router

        print("✅ Direct import successful!")
        print(f"   Router type: {type(router)}")
        print(f"   Router is None: {router is None}")

        if router:
            routes = []
            for route in router.routes:
                if hasattr(route, "path"):
                    methods = getattr(route, "methods", set())
                    routes.append(f"{route.path} ({list(methods)})")

            print("   Router routes:")
            for route in routes:
                print(f"     - {route}")
            print(f"   Total routes: {len(routes)}")

            if router:
                print("✅ Router is truthy - will be registered")
            else:
                print("❌ Router is falsy - will NOT be registered")
        else:
            print("❌ Router is None")

    except Exception as e:
        print(f"❌ Direct import failed: {e}")
        import traceback

        traceback.print_exc()

    print()


def test_compat_import() -> None:
    """Test import through compat layer"""
    print("=" * 50)
    print("🔍 TESTING COMPAT LAYER IMPORT")
    print("=" * 50)

    try:
        print("📦 Importing AFO.api.compat.skills_router...")
        from AFO.api.compat import skills_router

        print("✅ Compat layer import successful!")
        print(f"   Router type: {type(skills_router)}")
        print(f"   Router is None: {skills_router is None}")

        if skills_router:
            routes = []
            for route in skills_router.routes:
                if hasattr(route, "path"):
                    methods = getattr(route, "methods", set())
                    routes.append(f"{route.path} ({list(methods)})")

            print("   Router routes:")
            for route in routes:
                print(f"     - {route}")
            print(f"   Total routes: {len(routes)}")

            if skills_router:
                print("✅ Router is truthy - will be registered")
            else:
                print("❌ Router is falsy - will NOT be registered")
        else:
            print("❌ Router is None")

    except Exception as e:
        print(f"❌ Compat layer import failed: {e}")
        import traceback

        traceback.print_exc()

    print()


def test_app_registration() -> None:
    """Test FastAPI app registration"""
    print("=" * 50)
    print("🔍 TESTING FASTAPI APP REGISTRATION")
    print("=" * 50)

    try:
        print("🏗️ Creating FastAPI app...")
        from AFO.api.config import get_app_config
        from AFO.api.middleware import setup_middleware
        from AFO.api.routers import setup_routers

        app = get_app_config()
        print("✅ App created successfully")

        setup_middleware(app)
        print("✅ Middleware setup completed")

        setup_routers(app)
        print("✅ Router setup completed")

        # Check registered routes
        skills_routes = []
        for route in app.routes:
            if hasattr(route, "path") and "skills" in route.path:
                methods = getattr(route, "methods", set())
                skills_routes.append(f"{route.path} ({list(methods)})")

        if skills_routes:
            print("🎯 Skills routes found in app:")
            for route in skills_routes:
                print(f"   - {route}")
        else:
            print("❌ No skills routes found in app")

        # Check all routes containing 'skills'
        print("📋 All routes containing 'skills':")
        all_skills_routes = [
            route.path
            for route in app.routes
            if hasattr(route, "path") and "skills" in route.path.lower()
        ]
        if all_skills_routes:
            for route in all_skills_routes:
                print(f"   - {route}")
        else:
            print("   (none)")

    except Exception as e:
        print(f"❌ App registration test failed: {e}")
        import traceback

        traceback.print_exc()

    print()


if __name__ == "__main__":
    print("🚀 AFO Kingdom Router Registration Debug")
    print("=" * 50)
    print()

    test_direct_import()
    test_compat_import()
    test_app_registration()

    print("=" * 50)
    print("✨ Debug complete!")
    print("=" * 50)
