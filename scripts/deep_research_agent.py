import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

# Configuration
PYTHON_EXE = "./.venv/bin/python"
PROJECT_ROOT = Path(".")
CORE_PATH = PROJECT_ROOT / "packages" / "afo-core"
AFO_PATH = CORE_PATH / "AFO"
LOGS = [
    PROJECT_ROOT / "api_server_reboot.log",
    PROJECT_ROOT / "aicpa_reboot.log",
    PROJECT_ROOT / "dashboard_reboot.log",
]


def run_command(cmd: List[str], cwd: Path = PROJECT_ROOT) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


def check_dependencies() -> Dict[str, Any]:
    print("running pip check...")
    output = run_command([PYTHON_EXE, "-m", "pip", "check"])
    return {
        "status": "passed" if "No broken requirements found" in output else "failed",
        "output": output.strip(),
    }


def check_dead_code() -> Dict[str, Any]:
    print("running vulture...")
    # Using specific targets to avoid scanning venvs or tests if desired, or just AFO main
    cmd = [PYTHON_EXE, "-m", "vulture", str(AFO_PATH), "--min-confidence", "80"]
    output = run_command(cmd)
    lines = [line for line in output.split("\n") if line.strip()]
    return {
        "count": len(lines),
        "sample": lines[:10],  # First 10 items
    }


def check_complexity() -> Dict[str, Any]:
    print("running radon...")
    # Check for complexity grade B or worse (score > 5-10 range usually, B is > 5)
    cmd = [PYTHON_EXE, "-m", "radon", "cc", str(AFO_PATH), "-s", "-n", "B"]
    output = run_command(cmd)
    lines = [line for line in output.split("\n") if line.strip()]
    return {"count": len(lines), "high_complexity_items": lines}


def check_type_safety() -> Dict[str, Any]:
    print("running mypy...")
    # Running on AFO core only to save time
    cmd = [
        PYTHON_EXE,
        "-m",
        "mypy",
        str(AFO_PATH),
        "--ignore-missing-imports",
        "--no-strict-optional",
    ]
    output = run_command(cmd, cwd=CORE_PATH)
    lines = output.split("\n")
    errors = [l for l in lines if "error:" in l]
    return {"error_count": len(errors), "sample": errors[:10]}


def scan_logs() -> Dict[str, Any]:
    print("scanning logs...")
    findings = {}
    for log_file in LOGS:
        if not log_file.exists():
            continue
        content = log_file.read_text(errors="ignore")
        errors = re.findall(r"(ERROR|CRITICAL|Exception|Traceback)", content, re.IGNORECASE)
        warnings = re.findall(r"(WARNING|WARN)", content, re.IGNORECASE)
        findings[log_file.name] = {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "recent_tail": content[-500:],  # Last 500 chars
        }
    return findings


def scan_annotations() -> Dict[str, Any]:
    print("scanning annotations...")
    cmd = ["grep", "-r", "-E", "TODO|FIXME|HACK|XXX", str(AFO_PATH)]
    output = run_command(cmd)
    lines = output.split("\n")
    valid_lines = [l for l in lines if l.strip() and "Binary file" not in l]

    counts = {"TODO": 0, "FIXME": 0, "HACK": 0, "XXX": 0}

    for l in valid_lines:
        for key in counts:
            if key in l:
                counts[key] += 1

    return {"total_count": len(valid_lines), "breakdown": counts, "sample": valid_lines[:5]}


def main():
    report = {
        "dependencies": check_dependencies(),
        "dead_code": check_dead_code(),
        "complexity": check_complexity(),
        "type_safety": check_type_safety(),
        "logs": scan_logs(),
        "technical_debt": scan_annotations(),
    }

    print(json.dumps(report, indent=2))

    # Save to file
    with open("deep_research_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
