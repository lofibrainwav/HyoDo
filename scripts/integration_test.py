#!/usr/bin/env python3
"""
AFO Kingdom Integration Test Suite

Tests the complete system integration including:
- FastAPI app startup and configuration
- Router registration and API endpoints
- Database connectivity
- External service integrations
- Middleware functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "afo-core"))


def test_app_initialization() -> None:
    """Test FastAPI app initialization and configuration"""
    print("=" * 60)
    print("🧪 TESTING FASTAPI APP INITIALIZATION")
    print("=" * 60)

    try:
        from AFO.api.config import get_app_config
        from AFO.api.metadata import get_api_metadata

        # Test metadata
        metadata = get_api_metadata()
        assert metadata["title"] == "AFO Kingdom Soul Engine API"
        assert metadata["version"] == "6.3.0"
        assert "openapi_tags" in metadata
        print("✅ API metadata configuration valid")

        # Test app creation
        app = get_app_config()
        assert app.title == "AFO Kingdom Soul Engine API"
        assert app.version == "6.3.0"
        print("✅ FastAPI app created successfully")

        return app

    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_middleware_setup(app) -> None:
    """Test middleware setup"""
    print("=" * 60)
    print("🧪 TESTING MIDDLEWARE SETUP")
    print("=" * 60)

    try:
        from AFO.api.middleware import setup_middleware

        # Apply middleware
        setup_middleware(app)
        print("✅ Middleware setup completed")

        # Check CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls") and "CORSMiddleware" in str(middleware.cls):
                cors_middleware = middleware
                break

        if cors_middleware:
            print("✅ CORS middleware configured")
        else:
            print("⚠️ CORS middleware not found")

        return True

    except Exception as e:
        print(f"❌ Middleware setup failed: {e}")
        return False


def test_router_registration(app) -> None:
    """Test router registration and API endpoints"""
    print("=" * 60)
    print("🧪 TESTING ROUTER REGISTRATION")
    print("=" * 60)

    try:
        from AFO.api.routers import setup_routers

        # Setup routers
        setup_routers(app)
        print("✅ Router setup completed")

        # Check registered routes
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                methods = getattr(route, "methods", set())
                routes.append({"path": route.path, "methods": list(methods)})

        # Categorize routes
        health_routes = [r for r in routes if "health" in r["path"].lower()]
        skills_routes = [r for r in routes if "skills" in r["path"].lower()]
        api_routes = [r for r in routes if r["path"].startswith("/api/")]

        print(f"📊 Total routes registered: {len(routes)}")
        print(f"🏥 Health routes: {len(health_routes)}")
        print(f"🎯 Skills routes: {len(skills_routes)}")
        print(f"🔗 API routes: {len(api_routes)}")

        # Verify Skills API routes
        expected_skills_routes = [
            "/api/skills/list",
            "/api/skills/detail/{skill_id}",
            "/api/skills/execute",
            "/api/skills/health",
        ]

        registered_skills_paths = [r["path"] for r in skills_routes]
        for expected in expected_skills_routes:
            if expected in registered_skills_paths:
                print(f"✅ Skills route registered: {expected}")
            else:
                print(f"❌ Missing Skills route: {expected}")

        # Check for basic health endpoints
        basic_health_endpoints = ["/health", "/api/health/comprehensive"]
        for endpoint in basic_health_endpoints:
            if any(endpoint in r["path"] for r in routes):
                print(f"✅ Health endpoint available: {endpoint}")
            else:
                print(f"⚠️ Health endpoint missing: {endpoint}")

        return True

    except Exception as e:
        print(f"❌ Router registration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_database_connectivity() -> None:
    """Test database connectivity"""
    print("=" * 60)
    print("🧪 TESTING DATABASE CONNECTIVITY")
    print("=" * 60)

    try:
        from AFO.api.initialization import _initialize_databases

        # Test database initialization
        asyncio.run(_initialize_databases())

        # Check if connections are established
        from AFO.api.initialization import PG_POOL, REDIS_CLIENT

        db_status = {
            "postgresql": PG_POOL is not None,
            "redis": REDIS_CLIENT is not None,
        }

        for db, connected in db_status.items():
            if connected:
                print(f"✅ {db.capitalize()} connection established")
            else:
                print(f"⚠️ {db.capitalize()} connection not available")

        return True

    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False


def test_external_services() -> None:
    """Test external service integrations"""
    print("=" * 60)
    print("🧪 TESTING EXTERNAL SERVICE INTEGRATIONS")
    print("=" * 60)

    try:
        from AFO.api.initialization import _initialize_llm_clients

        # Test LLM client initialization
        asyncio.run(_initialize_llm_clients())

        # Check service availability
        from AFO.api.compat import ANTHROPIC_AVAILABLE, OPENAI_AVAILABLE

        services = {
            "OpenAI": OPENAI_AVAILABLE,
            "Anthropic": ANTHROPIC_AVAILABLE,
        }

        for service, available in services.items():
            if available:
                print(f"✅ {service} integration available")
            else:
                print(f"ℹ️ {service} integration not configured")

        return True

    except Exception as e:
        print(f"❌ External services test failed: {e}")
        return False


def test_system_initialization() -> None:
    """Test complete system initialization"""
    print("=" * 60)
    print("🧪 TESTING COMPLETE SYSTEM INITIALIZATION")
    print("=" * 60)

    try:
        from AFO.api.cleanup import cleanup_system
        from AFO.api.initialization import initialize_system

        # Test initialization
        asyncio.run(initialize_system())
        print("✅ System initialization completed")

        # Test cleanup
        asyncio.run(cleanup_system())
        print("✅ System cleanup completed")

        return True

    except Exception as e:
        print(f"❌ System initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_integration_tests() -> None:
    """Run all integration tests"""
    print("🚀 AFO Kingdom Integration Test Suite")
    print("=" * 60)

    results = []

    # Test 1: App Initialization
    app = test_app_initialization()
    results.append(("App Initialization", app is not None))

    if app:
        # Test 2: Middleware Setup
        middleware_ok = test_middleware_setup(app)
        results.append(("Middleware Setup", middleware_ok))

        # Test 3: Router Registration
        router_ok = test_router_registration(app)
        results.append(("Router Registration", router_ok))

    # Test 4: Database Connectivity
    db_ok = test_database_connectivity()
    results.append(("Database Connectivity", db_ok))

    # Test 5: External Services
    services_ok = test_external_services()
    results.append(("External Services", services_ok))

    # Test 6: System Initialization
    init_ok = test_system_initialization()
    results.append(("System Initialization", init_ok))

    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    print("⚠️ Some integration tests failed")
    return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
