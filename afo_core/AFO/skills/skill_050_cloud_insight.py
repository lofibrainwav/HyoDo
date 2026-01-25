import subprocess
from typing import Any


def cloud_insight_skill() -> dict[str, Any]:
    """
    Skill to provide insights into the Google Cloud environment.
    Check if gcloud is installed and return basic info.
    """
    try:
        # Check gcloud version
        version_proc = subprocess.run(
            ["gcloud", "--version"], capture_output=True, text=True, check=True
        )
        version_info = version_proc.stdout.split("\n")[0]

        # Check active account (optional, might fail if not logged in)
        account_proc = subprocess.run(
            ["gcloud", "config", "get-value", "account"], capture_output=True, text=True
        )
        account = account_proc.stdout.strip() or "Not Logged In"

        return {
            "status": "active",
            "version": version_info,
            "account": account,
            "message": f"GCP SDK detected: {version_info}. Account: {account}",
        }
    except Exception as e:
        return {"status": "error", "message": f"GCP SDK check failed: {e!s}"}


if __name__ == "__main__":
    print(cloud_insight_skill())
