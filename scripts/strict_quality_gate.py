#!/usr/bin/env python3
"""
🛡️ Strict Quality Gate (L4 Presentation Shield)
Enforces "Zero Any" rule for core API routes using Pyright.
"""

import json
import subprocess
import sys

# Core routes to protect (from AFO_FINAL_SSOT.md)
CORE_ROUTES = [
    "packages/afo-core/AFO/api/routes/chat.py",
    "packages/afo-core/AFO/api/routes/julie.py",
    "packages/afo-core/AFO/api/routes/scholar.py",
    "packages/afo-core/AFO/api/routes/gateway.py",
    "packages/afo-core/AFO/api/routes/llm.py",
]


def run_pyright_audit() -> dict:
    """Run pyright on core routes and analyze Any usage."""
    results = {"ok": True, "violations": [], "checked_files": [], "error": None}

    try:
        # Construct pyright command
        cmd = ["pyright", "--outputjson"] + CORE_ROUTES

        # Execute
        process = subprocess.run(cmd, capture_output=True, text=True)

        # Pyright returns 1 if issues found, but we want the JSON regardless
        try:
            output = json.loads(process.stdout)
        except json.JSONDecodeError:
            results["ok"] = False
            results["error"] = "Failed to parse Pyright JSON output"
            return results

        # Iterate through general diagnostics
        diagnostics = output.get("generalDiagnostics", [])

        for diag in diagnostics:
            # We are specifically looking for "Any" related issues
            # Pyright doesn't have a single "Any check" flag like mypy,
            # but we can look for "Unknown" or implicit Any if configured,
            # or simply report ANY diagnostic on these files as a violation for "Strict" gate.

            message = diag.get("message", "").lower()
            file_path = diag.get("file", "")

            # If any error/warning in core routes, it's a violation of STRICT protocol
            results["violations"].append(
                {
                    "file": file_path,
                    "line": diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                    "message": diag.get("message"),
                    "severity": diag.get("severity"),
                }
            )

        results["ok"] = len(results["violations"]) == 0
        results["checked_files"] = CORE_ROUTES

    except Exception as e:
        results["ok"] = False
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    print("🛡️ [L4 Gate] Starting Strict Quality Audit...")
    audit_results = run_pyright_audit()

    if audit_results["error"]:
        print(f"❌ Error: {audit_results['error']}")
        sys.exit(1)

    print(f"📊 Checked Files: {len(audit_results['checked_files'])}")

    if audit_results["ok"]:
        print("✅ [眞] Truth Guard: Core Routes are perfectly typed. (Shield is IRON)")
        sys.exit(0)
    else:
        print(f"❌ [眞] Drift Detected! {len(audit_results['violations'])} violations found.")
        for v in audit_results["violations"]:
            print(f"  - {v['file']}:{v['line']} -> {v['message']}")
        sys.exit(2)
