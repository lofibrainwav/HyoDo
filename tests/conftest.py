"""Pytest/Hypothesis configuration for HyoDo.

Determinism over caching:
- Hypothesis runs with a fixed seed so CI and fresh clones produce the
  same generated examples.  The .hypothesis/ directory remains a local
  cache (gitignored); reproducibility comes from the seed, not the DB.
- deadline=None: macOS CI runners can be slow; hypothesis deadlines
  produce flaky failures on I/O-bound tests.
"""

from __future__ import annotations

from hypothesis import HealthCheck, settings

# Fixed-seed profile: same examples on every machine, no .hypothesis DB.
settings.register_profile(
    "ci",
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    print_blob=True,
    database=None,
)

# Activate the CI profile by default; individual tests may override
# via their own @settings decorators.
settings.load_profile("ci")
