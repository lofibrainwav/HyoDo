# Trinity Score: 95.0 (Phase 29B Functional Coverage)
"""Functional Coverage Tests

NOTE: This file is a thin re-export for backward compatibility.
      Tests have been split into separate files for 500-line rule compliance:
      - test_functional_skills.py: Skills, Royal Library, Input Server tests
      - test_functional_rag.py: Hybrid RAG tests
      - test_functional_julie.py: Julie AI Agents, Music Provider tests
      - test_functional_chancellor.py: Chancellor Router tests
      - test_functional_utils.py: Utils, Exponential Backoff, Circuit Breaker tests
      - test_functional_stubs.py: Coverage gap import stubs
"""

# Re-export test functions for backward compatibility
from tests.test_functional_chancellor import (
    test_chancellor_router_deep,
    test_chancellor_router_logic,
    test_final_push_stubs,
)
from tests.test_functional_julie import (
    test_aicpa_interface,
    test_julie_orchestrator,
    test_music_provider_imports,
)
from tests.test_functional_rag import (
    test_hybrid_rag_answer,
    test_hybrid_rag_basics,
    test_hybrid_rag_deep,
)
from tests.test_functional_skills import (
    test_input_server_logic,
    test_protocols_basic,
    test_royal_library_principles,
    test_skills_core_registration,
    test_skills_service_logic,
    test_type_guards_basic,
)
from tests.test_functional_stubs import (
    test_coverage_gap_stubs,
    test_coverage_gap_stubs_part2,
    test_coverage_gap_stubs_part3,
)
from tests.test_functional_utils import (
    test_circuit_breaker_basic,
    test_utils_async_backoff,
    test_utils_exponential_backoff,
)

__all__ = [
    # Skills
    "test_protocols_basic",
    "test_type_guards_basic",
    "test_royal_library_principles",
    "test_skills_core_registration",
    "test_skills_service_logic",
    "test_input_server_logic",
    # RAG
    "test_hybrid_rag_basics",
    "test_hybrid_rag_answer",
    "test_hybrid_rag_deep",
    # Julie
    "test_julie_orchestrator",
    "test_aicpa_interface",
    "test_music_provider_imports",
    # Chancellor
    "test_chancellor_router_logic",
    "test_chancellor_router_deep",
    "test_final_push_stubs",
    # Utils
    "test_utils_exponential_backoff",
    "test_utils_async_backoff",
    "test_circuit_breaker_basic",
    # Stubs
    "test_coverage_gap_stubs",
    "test_coverage_gap_stubs_part2",
    "test_coverage_gap_stubs_part3",
]
