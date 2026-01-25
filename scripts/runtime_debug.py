#!/usr/bin/env python3
"""
AFO Kingdom Skills API Runtime Debug Script

Debugs the Skills API registration issue during actual server runtime.
Tests the complete FastAPI app lifecycle to identify where registration fails.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def debug_app_creation() -> None:
    """Debug FastAPI app creation process"""
    print("=" * 60)
    print("🔍 DEBUGGING FASTAPI APP CREATION")
    print("=" * 60)

    try:
        print("1. Importing config module...")
        from AFO.api.config import get_app_config, get_server_config

        print("2. Getting server config...")
        host, port = get_server_config()
        print(f"   Server config: {host}:{port}")

        print("3. Creating FastAPI app...")
        app = get_app_config()
        print(f"   App created: {app.title} v{app.version}")

        print("4. Checking initial routes...")
        initial_routes = len([r for r in app.routes if hasattr(r, "path")])
        print(f"   Initial routes: {initial_routes}")

        return app

    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def debug_router_setup(app) -> None:
    """Debug router setup process"""
    print("=" * 60)
    print("🔍 DEBUGGING ROUTER SETUP")
    print("=" * 60)

    try:
        print("1. Importing router setup...")
        from AFO.api.routers import setup_routers

        print("2. Setting up routers...")
        setup_routers(app)

        print("3. Checking routes after setup...")
        all_routes = []
        skills_routes = []

        for route in app.routes:
            if hasattr(route, "path"):
                route_info = {
                    "path": route.path,
                    "methods": list(getattr(route, "methods", set())),
                    "name": getattr(route, "name", "unknown"),
                }
                all_routes.append(route_info)

                if "skills" in route.path.lower():
                    skills_routes.append(route_info)

        print(f"   Total routes after setup: {len(all_routes)}")
        print(f"   Skills routes found: {len(skills_routes)}")

        if skills_routes:
            print("   Skills routes:")
            for route in skills_routes:
                print(f"     - {route['path']} {route['methods']}")
        else:
            print("   ❌ No skills routes found!")

        # Check if skills router was imported
        try:
            from AFO.api.compat import skills_router

            print(f"   Skills router in compat: {skills_router is not None}")
            if skills_router:
                router_routes = len(skills_router.routes)
                print(f"   Skills router has {router_routes} routes")
        except Exception as e:
            print(f"   ❌ Skills router import failed: {e}")

        return all_routes, skills_routes

    except Exception as e:
        print(f"❌ Router setup debug failed: {e}")
        import traceback

        traceback.print_exc()
        return None, None


def debug_lifespan_execution() -> None:
    """Debug lifespan execution"""
    print("=" * 60)
    print("🔍 DEBUGGING LIFESPAN EXECUTION")
    print("=" * 60)

    try:
        print("1. Testing lifespan manager...")
        from AFO.api.config import get_lifespan_manager

        get_lifespan_manager()
        print("   Lifespan manager created")

        print("2. Testing initialization...")
        from AFO.api.initialization import initialize_system

        # This will show us what happens during startup
        print("   Running initialize_system...")
        asyncio.run(initialize_system())
        print("   ✅ Initialization completed")

        print("3. Testing cleanup...")
        from AFO.api.cleanup import cleanup_system

        asyncio.run(cleanup_system())
        print("   ✅ Cleanup completed")

    except Exception as e:
        print(f"❌ Lifespan debug failed: {e}")
        import traceback

        traceback.print_exc()


def test_server_startup() -> None:
    """Test actual server startup"""
    print("=" * 60)
    print("🔍 TESTING SERVER STARTUP")
    print("=" * 60)

    import subprocess
    import time

    try:
        print("1. Starting server in background...")
        server_process = subprocess.Popen(
            [sys.executable, "packages/afo-core/api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            text=True,
        )

        print("2. Waiting for server to start...")
        time.sleep(3)

        # Check if process is still running
        if server_process.poll() is None:
            print("   ✅ Server process is running")

            # Test health endpoint
            import requests

            try:
                response = requests.get("http://localhost:8010/health", timeout=2)
                print(f"   Health check: {response.status_code}")

                # Test OpenAPI
                openapi_response = requests.get("http://localhost:8010/openapi.json", timeout=2)
                if openapi_response.status_code == 200:
                    openapi_data = openapi_response.json()
                    paths = list(openapi_data.get("paths", {}).keys())
                    skills_paths = [p for p in paths if "skills" in p.lower()]
                    print(f"   OpenAPI paths: {len(paths)} total")
                    print(f"   Skills paths in OpenAPI: {len(skills_paths)}")
                    if skills_paths:
                        for path in skills_paths:
                            print(f"     - {path}")
                    else:
                        print("   ❌ No skills paths in OpenAPI!")
                else:
                    print(f"   ❌ OpenAPI failed: {openapi_response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"   ❌ HTTP requests failed: {e}")

            # Test direct skills endpoint
            try:
                skills_response = requests.get("http://localhost:8010/api/skills/list", timeout=2)
                print(f"   Skills API direct test: {skills_response.status_code}")
                if skills_response.status_code != 404:
                    print(f"   Response: {skills_response.text[:200]}...")
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Skills API test failed: {e}")

        else:
            print("   ❌ Server process failed to start")
            stdout, stderr = server_process.communicate()
            print("   STDOUT:", stdout[-500:])  # Last 500 chars
            print("   STDERR:", stderr[-500:])  # Last 500 chars

        # Cleanup
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("   ✅ Server terminated")

    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback

        traceback.print_exc()


def main() -> None:
    """Main debug function"""
    print("🚀 AFO Kingdom Skills API Runtime Debug")
    print("=" * 60)
    print()

    # Test 1: App creation
    app = debug_app_creation()
    print()

    if app:
        # Test 2: Router setup
        _all_routes, skills_routes = debug_router_setup(app)
        print()

        # Test 3: Lifespan execution
        debug_lifespan_execution()
        print()

        # Test 4: Actual server startup
        test_server_startup()
        print()

    # Summary
    print("=" * 60)
    print("📊 DEBUG SUMMARY")
    print("=" * 60)

    if app and skills_routes:
        print("✅ Skills router appears to be working in isolated testing")
        print("❓ Issue may be in server startup or environment differences")
        print("\n🔧 NEXT STEPS:")
        print("1. Check server logs for import errors during startup")
        print("2. Verify PYTHONPATH and working directory")
        print("3. Test with minimal server configuration")
        print("4. Add debug logging to compat.py load_routers()")
    else:
        print("❌ Skills router registration is failing")
        print("\n🔧 NEXT STEPS:")
        print("1. Check compat.py load_routers() function")
        print("2. Verify AFO.api.routers.skills import path")
        print("3. Test router creation manually")


if __name__ == "__main__":
    main()
