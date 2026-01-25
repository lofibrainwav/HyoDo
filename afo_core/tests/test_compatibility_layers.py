# Trinity Score: 90.0 (Established by Chancellor)
"""
Compatibility Layer Tests

These modules are thin re-export wrappers and don't need extensive testing.
The underlying implementations have their own tests.
"""

import pytest


class TestCompatibilityLayers:
    """Test that compatibility layers can be imported."""

    def test_llm_router_import(self) -> None:
        """Test llm_router module can be imported."""
        import llm_router

        assert hasattr(llm_router, "LLMRouter")
        assert hasattr(llm_router, "llm_router")

    def test_api_wallet_import(self) -> None:
        """Test api_wallet module can be imported."""
        import api_wallet

        assert hasattr(api_wallet, "APIWallet")
        assert hasattr(api_wallet, "create_wallet")
        assert hasattr(api_wallet, "wallet")

    def test_afo_llm_router_import(self) -> None:
        """Test AFO.llm_router module can be imported."""
        from AFO import llm_router

        assert hasattr(llm_router, "LLMRouter")

    def test_afo_api_wallet_import(self) -> None:
        """Test AFO.api_wallet module can be imported."""
        from AFO import api_wallet

        assert hasattr(api_wallet, "APIWallet")

    def test_afo_input_server_import(self) -> None:
        """Test AFO.input_server module can be imported."""
        from AFO.input_server import app, parse_env_text

        assert app is not None
        assert callable(parse_env_text)

    def test_afo_skills_registry_import(self) -> None:
        """Test AFO.afo_skills_registry module can be imported."""
        from AFO.afo_skills_registry import SkillRegistry, skills_registry

        assert SkillRegistry is not None
        assert skills_registry is not None
