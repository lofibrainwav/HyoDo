import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add package root to path
sys.path.append(os.path.join(Path.cwd(), "packages/afo-core"))

from AFO.start.serenity.vision_verifier import VisionVerifier


class AutoRecon:
    """
    Serenity Pillar: Autonomous Reconnaissance.
    Patrols the Kingdom's digital borders (URLs) to ensure visual integrity.
    """

    def __init__(self) -> None:
        self.verifier = VisionVerifier()
        self.targets = [
            {"url": "http://localhost:3000", "name": "dashboard_home"},
            # Future: specialized sub-pages or component isolated views
            # {"url": "http://localhost:3000/genui/treasury", "name": "treasury_card"},
        ]
        self.report_dir = "logs/recon_reports"
        Path(self.report_dir).mkdir(exist_ok=True, parents=True)

    async def patrol(self):
        print(f"🛡️ [AutoRecon] Patrol started at {datetime.now().isoformat()}")
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": [],
            "summary": {"passed": 0, "failed": 0, "total": 0},
        }

        for target in self.targets:
            print(f"   👀 Inspecting: {target['name']} ({target['url']})")
            result = await self.verifier.verify_url(target["url"], target["name"])

            entry = {
                "name": target["name"],
                "url": target["url"],
                "passed": result.passed,
                "screenshot": result.screenshot_path,
                "errors": result.errors,
            }
            report["results"].append(entry)

            if result.passed:
                report["summary"]["passed"] += 1
                print("      ✅ Secure.")
            else:
                report["summary"]["failed"] += 1
                print(f"      ⚠️ BREACH DETECTED: {result.errors}")

        report["summary"]["total"] = len(self.targets)
        self._save_report(report)
        print(
            f"🛡️ [AutoRecon] Patrol complete. Health: {report['summary']['passed']}/{report['summary']['total']}"
        )

        return report["summary"]["failed"] == 0

    def _save_report(self, report) -> None:
        filename = f"recon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.report_dir, filename)
        with Path(path).open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"📝 Report archived: {path}")


async def main():
    recon = AutoRecon()
    success = await recon.patrol()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
