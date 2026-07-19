"""Table-driven tests for every regex in the safety pattern registries.

Each labeled pattern in ``SECRET_PATTERNS``, ``DANGEROUS_COMMAND_PATTERNS`` and
``PRODUCTION_IMPACT_PATTERNS`` gets at least one positive sample that MUST be
detected. Where the regex intent has an obvious near-miss, a negative sample is
added that MUST NOT match that label.

All samples were derived from the actual regex source (see ``hyodo/safety.py``)
and confirmed empirically against :func:`scan_text`, not from guessing. Notably,
``rm_rf_root`` matches any target that begins with ``/`` (root/absolute) or ``~``
(home) — including bare ``rm -rf /``, ``rm -rf /*`` and ``rm -rf ~`` at end of
line — while relative targets such as ``rm -rf ./build`` stay undetected; the
``migration`` label matches literal tokens (``alembic`` etc.) and not the plain
English word "migration".
"""

from __future__ import annotations

import pytest

from hyodo.safety import (
    DANGEROUS_COMMAND_PATTERNS,
    PRODUCTION_IMPACT_PATTERNS,
    SECRET_PATTERNS,
    scan_text,
)

# Map every labeled pattern to the finding category scan_text assigns to it.
CATEGORY_BY_LABEL: dict[str, str] = {
    **{label: "secret" for label, _ in SECRET_PATTERNS},
    **{label: "dangerous_command" for label, _ in DANGEROUS_COMMAND_PATTERNS},
    **{label: "production_impact" for label, _ in PRODUCTION_IMPACT_PATTERNS},
}

# (label, sample, should_match). Each label has a positive case; most also have a
# negative near-miss that must not trigger the same label.
CASES: list[tuple[str, str, bool]] = [
    # --- SECRET_PATTERNS -------------------------------------------------
    # aws_access_key: AKIA + 16 uppercase alphanumerics.
    ("aws_access_key", "AKIAIOSFODNN7EXAMPLE", True),
    ("aws_access_key", "AKIA1234", False),  # too short after the AKIA prefix
    # github_token: gh[pousr]_ + 20+ token chars.
    ("github_token", "token = ghp_abcdefghijklmnopqrstuvwxyz012345", True),
    ("github_token", "ghx_abcdefghijklmnopqrst", False),  # 'x' is not in [pousr]
    # slack_token: xox[baprs]- + 10+ chars.
    ("slack_token", "xoxb-1111111111abcd", True),
    ("slack_token", "xoxz-1111111111abcd", False),  # 'z' is not in [baprs]
    # private_key_block: BEGIN [RSA|EC|OPENSSH]? PRIVATE KEY.
    ("private_key_block", "-----BEGIN RSA PRIVATE KEY-----", True),
    ("private_key_block", "-----BEGIN PUBLIC KEY-----", False),  # public, not private
    # generic_api_key_assignment: key/token/password = quoted value 8+ chars.
    ("generic_api_key_assignment", 'api_key = "supersecret123"', True),
    ("generic_api_key_assignment", 'password = "short"', False),  # value < 8 chars
    # --- DANGEROUS_COMMAND_PATTERNS -------------------------------------
    # rm_rf_root: rm + optional force flags + /, /*, ~ or /home (word-boundary anchored).
    ("rm_rf_root", "rm -rf /home", True),
    ("rm_rf_root", "rm -rf ./build", False),  # relative target, not root/absolute
    # git_reset_hard.
    ("git_reset_hard", "git reset --hard HEAD~1", True),
    ("git_reset_hard", "git reset --soft HEAD~1", False),  # --soft is safe
    # git_push_force: git push ... --force.
    ("git_push_force", "git push origin main --force", True),
    ("git_push_force", "git push origin main", False),  # no --force flag
    # drop_database: DROP DATABASE | DROP SCHEMA.
    ("drop_database", "please DROP DATABASE production;", True),
    ("drop_database", "DROP INDEX idx_users;", False),  # DROP but not DATABASE/SCHEMA
    # drop_table: DROP TABLE.
    ("drop_table", "DROP TABLE users;", True),
    ("drop_table", "DROP DATABASE analytics;", False),  # DROP but object is DATABASE
    # chmod_777: chmod [-R] 777.
    ("chmod_777", "chmod 777 deploy.sh", True),
    ("chmod_777", "chmod 755 deploy.sh", False),  # 755, not 777
    # --- PRODUCTION_IMPACT_PATTERNS -------------------------------------
    # migration: literal tokens alembic|django.db.migrations|flyway|liquibase.
    ("migration", "alembic upgrade head", True),
    ("migration", "run the database migration manually", False),  # English word, not a token
    # production_env: NODE_ENV/ENV/ENVIRONMENT = prod(uction).
    ("production_env", "NODE_ENV=production", True),
    ("production_env", "NODE_ENV=development", False),  # not prod
    # deploy_keyword: kubectl apply | terraform apply | helm upgrade.
    ("deploy_keyword", "kubectl apply -f deploy.yaml", True),
    ("deploy_keyword", "kubectl get pods", False),  # read-only, not apply
    # schema_change: ALTER TABLE | CREATE TABLE | DROP COLUMN.
    ("schema_change", "ALTER TABLE users ADD COLUMN age int", True),
    ("schema_change", "SELECT * FROM users", False),  # read-only query
]


def _case_id(case: tuple[str, str, bool]) -> str:
    label, _, should_match = case
    return f"{label}-{'pos' if should_match else 'neg'}"


@pytest.mark.parametrize(
    ("label", "sample", "should_match"), CASES, ids=[_case_id(c) for c in CASES]
)
def test_safety_pattern_sample(label: str, sample: str, should_match: bool) -> None:
    findings = scan_text(sample)
    matched = [f for f in findings if f.label == label]

    if should_match:
        assert matched, f"expected label {label!r} to be detected in {sample!r}"
        # The finding must carry the category scan_text assigns to that registry.
        expected_category = CATEGORY_BY_LABEL[label]
        assert all(f.category == expected_category for f in matched), (
            f"label {label!r} should map to category {expected_category!r}"
        )
    else:
        assert not matched, f"label {label!r} must NOT be detected in near-miss sample {sample!r}"


@pytest.mark.parametrize(
    "sample",
    ["rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf /home", "sudo rm -rf /", "rm -fr /"],
)
def test_rm_rf_root_detects_root_and_home_targets(sample: str) -> None:
    """Regression: catastrophic bare targets must be detected.

    The previous regex anchored the target with a trailing ``\\b``, so
    non-word-ending targets (``/``, ``/*``, ``~``) at end of line slipped
    through. hyodo safe's whole purpose is early warning on exactly these.
    """
    findings = scan_text(sample)
    assert any(f.label == "rm_rf_root" for f in findings), (
        f"expected rm_rf_root to be detected in {sample!r}"
    )


@pytest.mark.parametrize("sample", ["rm -rf ./build", "rm -rf build/", "rm -rf .", "rm -rf tmpdir"])
def test_rm_rf_root_ignores_relative_targets(sample: str) -> None:
    """Relative targets (not starting with / or ~) must stay undetected."""
    findings = scan_text(sample)
    assert not any(f.label == "rm_rf_root" for f in findings), (
        f"relative target {sample!r} must not trigger rm_rf_root"
    )


def test_every_registry_label_has_a_positive_case() -> None:
    """Guard: every labeled pattern in the source has at least one positive sample.

    If a new pattern is added to a registry, this test fails until a positive
    case is added above, keeping the table exhaustive.
    """
    covered_positive = {label for label, _, should_match in CASES if should_match}
    all_source_labels = set(CATEGORY_BY_LABEL)
    missing = all_source_labels - covered_positive
    assert not missing, f"registry labels without a positive test case: {sorted(missing)}"
