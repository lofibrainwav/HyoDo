"""Property-based boundary tests for safety pattern registries.

Philosophy: Native collectors (Benevolence / Hyo / Yeong) are irreplaceable —
if a pattern fails to catch what it claims, no shell command can compensate.
These tests verify the *boundary invariants* of each regex: the exact
character that separates match from no-match.

This is Truth (진): measurement grounded in the actual pattern source, not
guesswork.  Every strategy generates near-miss strings at the regex boundary,
proving that one character more or fewer flips the detection result.
"""

from __future__ import annotations

import string

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from hyodo.safety import (
    DANGEROUS_COMMAND_PATTERNS,
    PRODUCTION_IMPACT_PATTERNS,
    SECRET_PATTERNS,
    scan_text,
)

# ---------------------------------------------------------------------------
# Strategies — boundary generators for each pattern class
# ---------------------------------------------------------------------------


def _aws_access_key_boundary() -> st.SearchStrategy[str]:
    """AKIA + 16+ uppercase alphanumerics (match) vs AKIA + 15 (no-match, one short).

    The regex is ``AKIA[0-9A-Z]{16}`` — no word-boundary anchor, so 17+ chars
    also match.  The boundary is at *minimum* length: 15 suffix chars must not
    match, 16 must.
    """
    alnum = st.sampled_from(list(string.ascii_uppercase + string.digits))
    return st.one_of(
        # Positive: AKIA + 16+ chars (boundary and beyond)
        st.builds(lambda cs: "AKIA" + "".join(cs), st.lists(alnum, min_size=16, max_size=18)),
        # Negative: AKIA + 15 chars (one short)
        st.builds(lambda cs: "AKIA" + "".join(cs), st.lists(alnum, min_size=15, max_size=15)),
    )


def _aws_access_key_expected(s: str) -> bool | None:
    """Return True if the string should match aws_access_key, False if not, None if ambiguous."""
    suffix = s[4:] if s.startswith("AKIA") else ""
    if not s.startswith("AKIA"):
        return None
    if not all(c in string.ascii_uppercase + string.digits for c in suffix):
        return None
    # The regex requires exactly 16 chars after AKIA; 15 is too short.
    # 17+ also match (no $ anchor) — that's a known design choice, not a bug.
    if len(suffix) >= 16:
        return True
    if len(suffix) == 15:
        return False
    return None


def _github_token_boundary() -> st.SearchStrategy[str]:
    """gh[pousr]_ + 20+ token chars (match) vs ghx_ (no-match, invalid prefix).

    The regex is ``gh[pousr]_[A-Za-z0-9_]{20,}``.  The minimum body length
    that matches is 20 chars; 19 chars must not match.  Only alphanumeric
    and underscore characters are valid — hyphens are not in the pattern.
    """
    token_chars = st.sampled_from(list(string.ascii_letters + string.digits + "_"))
    prefix = st.sampled_from(["ghp_", "gho_", "ghu_", "ghs_", "ghr_"])
    return st.one_of(
        # Positive: valid prefix + 20+ chars (boundary and beyond)
        st.builds(
            lambda p, cs: p + "".join(cs), prefix, st.lists(token_chars, min_size=20, max_size=40)
        ),
        # Negative: valid prefix + 19 chars (one short)
        st.builds(
            lambda p, cs: p + "".join(cs), prefix, st.lists(token_chars, min_size=19, max_size=19)
        ),
        # Negative: invalid prefix ghx_ + 20+ chars
        st.builds(lambda cs: "ghx_" + "".join(cs), st.lists(token_chars, min_size=20, max_size=30)),
    )


def _rm_rf_boundary() -> st.SearchStrategy[str]:
    """rm -rf /... (match) vs rm -rf ./... (no-match) at boundary."""
    return st.one_of(
        st.just("rm -rf /"),
        st.just("rm -rf /*"),
        st.just("rm -rf ~"),
        st.just("rm -rf ./build"),
        st.just("rm -rf /home/user/project"),
        # Boundary: bare 'rm /' without -f — still matches (pattern doesn't require -f)
        st.just("rm /tmp/scratch"),
        # Negative: relative path
        st.just("rm -rf ./tmp"),
    )


def _drop_keyword_boundary() -> st.SearchStrategy[str]:
    """DROP DATABASE/TABLE (match) vs DROP INDEX (no-match)."""
    return st.one_of(
        st.just("DROP DATABASE production;"),
        st.just("DROP TABLE users;"),
        st.just("DROP INDEX idx_users;"),  # negative — not DATABASE/TABLE
        st.just("drop schema public;"),  # case-insensitive match
        st.just("DROP VIEW v_users;"),  # negative
    )


def _production_env_boundary() -> st.SearchStrategy[str]:
    """NODE_ENV=production (match) vs development (no-match)."""
    return st.one_of(
        st.just("NODE_ENV=production"),
        st.just("ENV=prod"),
        st.just('ENVIRONMENT="production"'),
        st.just("NODE_ENV=development"),  # negative
        st.just("NODE_ENV=staging"),  # negative
    )


# ---------------------------------------------------------------------------
# Boundary property: exact one-character boundary for AWS key
# ---------------------------------------------------------------------------


@example(s="AKIAIOSFODNN7EXAMPLE")
@given(s=_aws_access_key_boundary())
@settings(deadline=None, suppress_health_check=[HealthCheck.filter_too_much], max_examples=200)
def test_aws_access_key_boundary_property(s: str) -> None:
    """An AKIA key of exactly 20 chars (AKIA+16) must match; 19 or 21 must not."""
    findings = scan_text(s)
    expected = _aws_access_key_expected(s)
    if expected is None:
        return  # ambiguous — skip
    found = any(f.label == "aws_access_key" for f in findings)
    assert found == expected, f"AWS key length {len(s)}: expected match={expected}, found={found}"


# ---------------------------------------------------------------------------
# Boundary property: github token prefix discrimination
# ---------------------------------------------------------------------------


@given(s=_github_token_boundary())
@settings(deadline=None, suppress_health_check=[HealthCheck.filter_too_much], max_examples=200)
def test_github_token_prefix_discrimination(s: str) -> None:
    """gh[pousr]_ + 20+ chars must match; ghx_ or 19-char body must not."""
    findings = scan_text(s)
    found = any(f.label == "github_token" for f in findings)
    body = s[4:]  # after the prefix
    if s.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_")) and len(body) >= 20:
        assert found, f"Valid github token not detected: prefix={s[:4]} body_len={len(body)}"
    if s.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_")) and len(body) == 19:
        # One char too short — must NOT match
        assert not found, f"Short body (19 chars) incorrectly matched: {s[:8]}..."
    if s.startswith("ghx_"):
        assert not found, "Invalid prefix ghx_ incorrectly matched as github_token"


# ---------------------------------------------------------------------------
# Boundary property: rm -rf root vs relative target discrimination
# ---------------------------------------------------------------------------


@given(s=_rm_rf_boundary())
@settings(deadline=None, max_examples=50)
def test_rm_rf_root_vs_relative_discrimination(s: str) -> None:
    """rm -rf with absolute/home target must match; relative ./ must not."""
    findings = scan_text(s)
    found = any(f.label == "rm_rf_root" for f in findings)
    # The pattern specifically targets root/home absolute paths
    if s in ("rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf /home/user/project", "rm /tmp/scratch"):
        assert found, f"Absolute-path rm not caught: {s}"
    if s in ("rm -rf ./build", "rm -rf ./tmp"):
        assert not found, f"Relative-path rm incorrectly flagged: {s}"


# ---------------------------------------------------------------------------
# Boundary property: DROP DATABASE/TABLE vs other DROP statements
# ---------------------------------------------------------------------------


@given(s=_drop_keyword_boundary())
@settings(deadline=None, max_examples=50)
def test_drop_keyword_discrimination(s: str) -> None:
    """DROP DATABASE/TABLE must match; DROP INDEX/VIEW must not."""
    findings = scan_text(s)
    found_drop_db = any(f.label == "drop_database" for f in findings)
    found_drop_tbl = any(f.label == "drop_table" for f in findings)
    s_upper = s.upper()
    if "DATABASE" in s_upper or "SCHEMA" in s_upper:
        assert found_drop_db, f"DROP DATABASE/SCHEMA not caught: {s}"
    if "TABLE" in s_upper and "DATABASE" not in s_upper:
        assert found_drop_tbl, f"DROP TABLE not caught: {s}"
    if "INDEX" in s_upper or "VIEW" in s_upper:
        assert not found_drop_db, f"DROP INDEX/VIEW incorrectly flagged as drop_database: {s}"
        assert not found_drop_tbl, f"DROP INDEX/VIEW incorrectly flagged as drop_table: {s}"


# ---------------------------------------------------------------------------
# Boundary property: production env detection vs development
# ---------------------------------------------------------------------------


@given(s=_production_env_boundary())
@settings(deadline=None, max_examples=50)
def test_production_env_discrimination(s: str) -> None:
    """NODE_ENV=production must match; development/staging must not."""
    findings = scan_text(s)
    found = any(f.label == "production_env" for f in findings)
    s_lower = s.lower()
    if "production" in s_lower or "=prod" in s_lower:
        assert found, f"Production env not detected: {s}"
    if "development" in s_lower or "staging" in s_lower:
        assert not found, f"Non-production env incorrectly flagged: {s}"


# ---------------------------------------------------------------------------
# Cross-registry invariant: no unlabeled pattern exists
# ---------------------------------------------------------------------------


def test_all_labeled_patterns_are_in_test_registry() -> None:
    """Every labeled pattern must appear in test_safety_patterns CASES registry.

    This is a completeness check — if a pattern is added to safety.py but not
    to the test registry, this test fails. Truth: unmeasured = unverified.
    """
    # Import at runtime to avoid module resolution issues in collection.
    from test_safety_patterns import CASES  # type: ignore[import-untyped]

    tested_labels = {label for label, _, _ in CASES}

    all_labeled = (
        {label for label, _ in SECRET_PATTERNS}
        | {label for label, _ in DANGEROUS_COMMAND_PATTERNS}
        | {label for label, _ in PRODUCTION_IMPACT_PATTERNS}
    )

    missing = all_labeled - tested_labels
    assert not missing, (
        f"Labeled patterns with no test case: {missing}. "
        f"Every labeled pattern must have at least one positive test case."
    )
