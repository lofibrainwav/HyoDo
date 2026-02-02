#!/usr/bin/env python3
from pathlib import Path

import yaml


def audit_workflows() -> None:
    workflow_dir = Path(".github/workflows")
    workflows = list(workflow_dir.glob("*.yml"))

    print(f"📊 Auditing {len(workflows)} workflows...")

    summary = {
        "total": len(workflows),
        "redundancies": [],
        "caching_issues": [],
        "optimization_suggestions": [],
    }

    steps_seen = {}

    for wf_path in workflows:
        try:
            with open(wf_path, "r") as f:
                wf = yaml.safe_load(f)

            jobs = wf.get("jobs", {})
            for job_name, job_data in jobs.items():
                steps = job_data.get("steps", [])
                for i, step in enumerate(steps):
                    uses = step.get("uses", "")
                    run = step.get("run", "")

                    # Track common steps for redundancy
                    key = uses or run[:50]
                    if key:
                        if key not in steps_seen:
                            steps_seen[key] = []
                        steps_seen[key].append(wf_path.name)

                    # Caching Check
                    if "setup-python" in uses and "cache" not in step.get("with", {}):
                        summary["caching_issues"].append(
                            f"{wf_path.name}: {job_name} - missing python cache"
                        )

                    if "setup-node" in uses and "cache" not in step.get("with", {}):
                        summary["caching_issues"].append(
                            f"{wf_path.name}: {job_name} - missing node cache"
                        )

                    # Slow Cleanup Check
                    if "apt-get clean" in run or "autoremove" in run:
                        summary["optimization_suggestions"].append(
                            f"{wf_path.name}: Consider removing aggressive apt cleanup on every run"
                        )

        except Exception as e:
            print(f"Error auditing {wf_path.name}: {e}")

    # Identify Redundant Steps across workflows
    for step_key, wf_names in steps_seen.items():
        if len(wf_names) > 5 and "actions/checkout" not in step_key:
            summary["redundancies"].append(
                {"step": step_key[:100], "count": len(wf_names), "workflows": list(set(wf_names))}
            )

    return summary


if __name__ == "__main__":
    report = audit_workflows()
    print("\n--- AUDIT REPORT ---")
    print(f"Caching Issues: {len(report['caching_issues'])}")
    for issue in report["caching_issues"][:5]:
        print(f"  - {issue}")

    print(f"\nOptimization Suggestions: {len(report['optimization_suggestions'])}")
    for sug in report["optimization_suggestions"][:5]:
        print(f"  - {sug}")

    print(f"\nRedundancy Hotspots: {len(report['redundancies'])}")
    for red in report["redundancies"]:
        print(f"  - {red['step']} (Used in {red['count']} workflows)")
