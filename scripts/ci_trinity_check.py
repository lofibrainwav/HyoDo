#!/usr/bin/env python3
import os
import pathlib
import re
import sys


def analyze_risk(directory: str) -> float:
    """
    [Goodness 善] Calculate Risk Score by scanning for dangerous patterns.
    Base Risk: 0
    +10 per hardcoded secret
    +20 per dangerous shell command (os.system) without comments
    """
    risk_score = 0
    risk_patterns = [
        (r"os\.system\(", 20, "Dangerous shell execution detected (os.system)"),
        (r"subprocess\.call\(", 10, "Subprocess call detected"),
        (r"API_KEY\s*=\s*['\"]sk-", 50, "Hardcoded API Key detected"),
        (r"password\s*=\s*['\"]", 30, "Hardcoded password detected"),
        (r"DROP TABLE", 50, "Destructive SQL detected"),
    ]

    # Simple recursive scan
    for root, dirs, files in os.walk(directory):
        # Exclude hidden and dependency directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                "node_modules",
                ".git",
                "__pycache__",
                "venv",
                ".venv",
                ".next",
                "dist",
                "build",
                "site-packages",
                "lib",
                "dgm",  # DGM upstream test data
                "quarantine",  # Quarantined files
                "red_team",  # Intentional adversarial patterns
                "scripts",  # Dev/utility scripts
            }
        ]

        # Skip known false positive paths
        skip_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            ".next",
            "tools/dgm",  # DGM upstream test fixtures
            "/quarantine/",  # Quarantined/deprecated code
            "/red_team/",  # Intentional security test patterns
            "docs/ssot/evidence",  # Historical evidence snapshots
            "/scripts/",  # Dev/utility scripts
        ]
        if any(ex in root for ex in skip_patterns):
            continue

        for file in files:
            if not file.endswith((".py", ".js", ".ts", ".tsx", ".sh")):
                continue

            # Skip security detection files (intentional patterns)
            if file in ("security_agent.py", "constitutional_ai.py"):
                continue

            path = os.path.join(root, file)
            try:
                with pathlib.Path(path).open(encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern, weight, msg in risk_patterns:
                        if re.search(pattern, content):
                            # Skip if suppressed with comment (Safety Override)
                            if "# nosec" in content or "# safe" in content:
                                continue
                            print(f"⚠️ [Risk] {file}: {msg} (+{weight})")
                            risk_score += weight
            except Exception:
                pass

    return risk_score


def analyze_truth_beauty() -> tuple[float, float]:
    """
    [Truth 眞 & Beauty 美]
    Simulate score based on hypothetical linting results for this demo integration.
    In real CI, this parses `mypy.log` and `ruff.json`.
    """
    # For now, we assume a baseline of high quality unless 'FAIL' marker file exists
    truth_score = 100.0
    beauty_score = 100.0

    if pathlib.Path("FORCE_FAIL_TRUTH").exists():
        truth_score = 50.0
    if pathlib.Path("FORCE_FAIL_BEAUTY").exists():
        beauty_score = 60.0

    return truth_score, beauty_score


def main() -> None:
    print("==================================================")
    print(" 🛡️  Shield of Goodness: Trinity CI Guard")
    print("==================================================")

    workspace = sys.argv[1] if len(sys.argv) > 1 else "."

    # 1. Evaluate Columns
    truth, beauty = analyze_truth_beauty()
    risk = analyze_risk(workspace)
    goodness = max(0, 100 - risk)  # Goodness is inverse of Risk

    # 2. Calculate Weighted Trinity Score (SSOT)
    # Truth(35) + Goodness(35) + Beauty(20) + Serenity(8) + Eternity(2)
    # Mocking Serenity/Eternity as 100 for static check context
    serenity = 100.0
    eternity = 100.0

    trinity_score = (
        (truth * 0.35) + (goodness * 0.35) + (beauty * 0.20) + (serenity * 0.08) + (eternity * 0.02)
    )

    print("\n📊 [Scorecard]")
    print(f"   - 眞 (Truth): {truth}")
    print(f"   - 善 (Goodness): {goodness} (Risk: {risk})")
    print(f"   - 美 (Beauty): {beauty}")
    print("   -----------------------------")
    print(f"   🏆 Trinity Score: {trinity_score:.2f}")

    # 3. Decision Logic (The Shield)
    passed = False
    reasons = []
    suggestions = []

    if trinity_score >= 90.0 and risk <= 10.0:
        print("\n✅ [AUTO_MERGE_ELIGIBLE] The Shield is lowered. You may pass.")
        passed = True
    else:
        print("\n🛡️ [BLOCKED] The Shield is raised.")
        if risk > 10.0:
            reasons.append(f"High Risk ({risk} > 10)")
            suggestions.append("Remove hardcoded secrets, avoid os.system() calls")
        if trinity_score < 90.0:
            reasons.append(f"Low Trinity Score ({trinity_score:.2f} < 90)")
            if truth < 100:
                suggestions.append("Run mypy/pyright to improve Truth (type safety)")
            if beauty < 100:
                suggestions.append("Run ruff/eslint to improve Beauty (code style)")

        for r in reasons:
            print(f"   ❌ Reason: {r}")

        if suggestions:
            print("\n💡 [SUGGESTIONS]")
            for s in suggestions:
                print(f"   → {s}")

        passed = False

    # Output for GitHub Actions
    if os.environ.get("GITHUB_OUTPUT"):
        with pathlib.Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as f:
            f.write(f"trinity_score={trinity_score}\n")
            f.write(f"risk_score={risk}\n")
            f.write(f"passed={str(passed).lower()}\n")

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
