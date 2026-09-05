"""Pytest/Hypothesis configuration for HyoDo.

CI determinism is separate from local exploration:
- CI disables the example database and uses deterministic generation so a
  given Hypothesis/Python/test version is repeatable on a fresh clone.
- Local runs keep Hypothesis defaults, including its local example database and
  normal exploration, so development does not become artificially narrow.
- Durable regression cases belong in explicit ``@example`` decorators; generated
  sequences are not promised to remain identical across dependency/test changes.
"""

from __future__ import annotations

import os

from hypothesis import HealthCheck, settings

settings.register_profile(
    "hyodo_ci",
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    print_blob=True,
    database=None,
)

if os.environ.get("CI"):
    settings.load_profile("hyodo_ci")
