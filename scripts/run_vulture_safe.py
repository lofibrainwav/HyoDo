#!/usr/bin/env python3
import subprocess

dirs = [
    "packages/afo-core/AFO/agents",
    "packages/afo-core/AFO/api",
    "packages/afo-core/AFO/audit",
    "packages/afo-core/AFO/core",
    "packages/afo-core/AFO/domain",
    "packages/afo-core/AFO/health",
    "packages/afo-core/AFO/irs",
    "packages/afo-core/AFO/julie",
    "packages/afo-core/AFO/memory_system",
    "packages/afo-core/AFO/multimodal",
    "packages/afo-core/AFO/schemas",
    "packages/afo-core/AFO/services",
    "packages/afo-core/AFO/utils",
    "packages/afo-core/AFO",
]

output_file = "vulture_report.txt"
with open(output_file, "w") as f:
    f.write("")  # Clear file

for d in dirs:
    print(f"Running vulture on {d}...")
    cmd = ["./.venv/bin/python", "-m", "vulture", d]
    if d == "packages/afo-core/AFO":
        # For the root, exclude subdirectories already scanned
        cmd += [
            "--exclude",
            "agents,api,audit,core,domain,health,irs,julie,memory_system,multimodal,schemas,services,utils",
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    with open(output_file, "a") as f:
        f.write(result.stdout)
        if result.stderr:
            print(f"Error in {d}: {result.stderr[:100]}...")

print("Done.")
