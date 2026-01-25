"""Trinity Score Sharing Coverage Gap Tests (100% Coverage Goal)

L1 도메인 레이어 커버리지 갭 해소 테스트.
SSOT: TRINITY_OS_PERSONAS.yaml, domain/metrics/trinity_ssot.py

NOTE: This file is a thin re-export for backward compatibility.
      Tests have been split into separate files for 500-line rule compliance:
      - test_coverage_gaps_domain.py: Domain Models tests
      - test_coverage_gaps_optimizer.py: Optimizer tests
      - test_coverage_gaps_pool.py: TrinityScorePool tests
      - test_coverage_gaps_system.py: SharingSystem & Feedback tests
"""

# Re-export all test classes for backward compatibility
from tests.trinity_score_sharing.test_coverage_gaps_domain import (
    TestDomainModelsCoverageGaps,
)
from tests.trinity_score_sharing.test_coverage_gaps_optimizer import (
    TestOptimizerCoverageGaps,
    TestOptimizerFullCoverage,
)
from tests.trinity_score_sharing.test_coverage_gaps_pool import (
    TestFinalCoverageGaps,
    TestTrinityScorePoolCoverage,
)
from tests.trinity_score_sharing.test_coverage_gaps_system import (
    TestFeedbackFullCoverage,
    TestSharingSystemFullCoverage,
)

__all__ = [
    "TestDomainModelsCoverageGaps",
    "TestOptimizerCoverageGaps",
    "TestOptimizerFullCoverage",
    "TestTrinityScorePoolCoverage",
    "TestFinalCoverageGaps",
    "TestSharingSystemFullCoverage",
    "TestFeedbackFullCoverage",
]
