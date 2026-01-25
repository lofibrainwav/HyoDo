#!/bin/bash
set -euo pipefail

# Fast Harvest for Pre-commit (runs on critical paths only)
# Goal: < 5 seconds execution with guaranteed success

echo "🐵 [MonkeyType] Fast Harvest (Pre-commit) running..."

# Skip if no staged Python changes (speed path for non-Python commits)
if command -v rg >/dev/null 2>&1; then
    if git diff --cached --name-only --diff-filter=ACM | rg -q '\.py$'; then
        :
    else
        echo "ℹ️  [MonkeyType] No staged Python changes; skipping harvest"
        exit 0
    fi
else
    if git diff --cached --name-only --diff-filter=ACM | grep -qE '\.py$'; then
        :
    else
        echo "ℹ️  [MonkeyType] No staged Python changes; skipping harvest"
        exit 0
    fi
fi

# 1. Environment check - Skip in CI/CD
if [[ "${CI:-false}" == "true" ]] || [[ "${GITHUB_ACTIONS:-false}" == "true" ]]; then
    echo "ℹ️  [MonkeyType] Skipping in CI/CD environment"
    exit 0
fi

# 2. Ensure pytest-monkeytype plugin is available (fast exit otherwise)
if ! python3 - <<'PY'
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("pytest_monkeytype") else 1)
PY
then
    echo "ℹ️  [MonkeyType] pytest-monkeytype not available; using minimal DB"
    python3 - <<'PY'
import sqlite3
import os
db_path = 'monkeytype_fast.sqlite3'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE calls (
            module TEXT,
            qualname TEXT,
            arg_types TEXT,
            return_type TEXT,
            yield_type TEXT,
            send_type TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    print("✅ Minimal MonkeyType database created")
PY
    exit 0
fi

# 2. Clean previous partial DB
rm -f monkeytype_fast.sqlite3 || true

# 3. Run minimal, stable tests for type harvesting
# Use tests that are most likely to pass and provide good type coverage
export MONKEYTYPE_TRACEBACKS=0
export MONKEYTYPE_MAX_TRACEBACKS=0

# Try multiple test sets in order of preference
TEST_FILES=(
    "packages/afo-core/tests/test_utils_advanced.py::TestCacheUtils::test_cache_init_success"
    "packages/afo-core/tests/test_utils_advanced.py::TestCacheUtils::test_cache_init_failure"
    "packages/afo-core/tests/test_scholars.py::TestScholarsBehavior::test_bangtong_implement_success"
    "packages/afo-core/tests/test_goodness_serenity.py::TestErrorHandling::test_safe_execute_success"
)

SUCCESS=false
for test_file in "${TEST_FILES[@]}"; do
    echo "🔍 [MonkeyType] Trying test: $test_file"

    # Run with timeout and ignore failures
    if command -v timeout >/dev/null 2>&1; then
        timeout 8s python3 -m pytest -q --maxfail=1 --disable-warnings --tb=no \
            --monkeytype-output=monkeytype_fast.sqlite3 \
            "$test_file" \
            > /dev/null 2>&1 && SUCCESS=true && break
    else
        python3 -m pytest -q --maxfail=1 --disable-warnings --tb=no \
        --monkeytype-output=monkeytype_fast.sqlite3 \
        "$test_file" \
        > /dev/null 2>&1 && SUCCESS=true && break
    fi
done

# 4. Always create a minimal database if none exists (for pipeline stability)
if [ ! -f monkeytype_fast.sqlite3 ]; then
    echo "📝 [MonkeyType] Creating minimal database for pipeline stability..."
    # Create a minimal SQLite database that monkeytype can work with
    python3 -c "
import sqlite3
import os
db_path = 'monkeytype_fast.sqlite3'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE calls (
            module TEXT,
            qualname TEXT,
            arg_types TEXT,
            return_type TEXT,
            yield_type TEXT,
            send_type TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print('✅ Minimal MonkeyType database created')
"
fi

# 5. Report status
if [ -f monkeytype_fast.sqlite3 ]; then
    SIZE=$(ls -lh monkeytype_fast.sqlite3 | awk '{print $5}')
    if [ "$SUCCESS" = true ]; then
        echo "✅ [MonkeyType] Successfully harvested types ($SIZE)"
    else
        echo "⚠️  [MonkeyType] Using minimal database ($SIZE) - test failures ignored"
    fi
else
    echo "❌ [MonkeyType] Failed to create database"
    exit 1
fi
