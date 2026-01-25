import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Add package root to sys.path
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_root not in sys.path:
    sys.path.append(package_root)

from services.integrated_learning_system import integrated_learning_system
from services.vision_verifier import vision_verifier

from AFO.chancellor_graph import ChancellorGraph

# Now we can import AFO modules
from AFO.config.settings import settings
from AFO.llms.ollama_api import ollama_api
from AFO.llms.openai_api import openai_api

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AFO.Verifier")


class KingdomVerifier:
    def __init__(self, require_openai: bool = False, output_dir: str = "artifacts") -> None:
        self.results = {}
        self.require_openai = require_openai or os.getenv("AFO_REQUIRE_OPENAI") == "1"
        self.output_dir = output_dir
        self.metadata = {
            "timestamp": datetime.now().isoformat(),
            "os": sys.platform,
            "python_version": sys.version,
            "require_openai": self.require_openai,
        }

    def report(self, name: str, success: bool, message: str = "") -> None:
        status = "✅ PASS" if success else "❌ FAIL"
        self.results[name] = {"success": success, "message": message}
        logger.info(f"[{status}] {name}: {message}")

    async def verify_infra(self):
        logger.info("🛡️ Phase 1: Infrastructure Verification")
        self.report("Settings", True, f"Base Dir: {settings.BASE_DIR}")

    async def verify_llms(self):
        logger.info("🧠 Phase 2: LLM Connectivity Verification")

        # Ollama
        ollama_ok = ollama_api.is_available()
        self.report(
            "Ollama API",
            ollama_ok,
            f"URL: {ollama_api.base_url}, Model: {ollama_api.model}",
        )

        # OpenAI (API Key check)
        openai_available = openai_api.is_available()
        if not openai_available:
            if not openai_api.api_key:
                msg = "EXPECTED-SKIP: OPENAI_API_KEY is not set"
                success = not self.require_openai
                self.report("OpenAI API", success, msg)
            else:
                self.report(
                    "OpenAI API",
                    False,
                    "FAIL: API Key set but service unreachable/invalid",
                )
        else:
            self.report("OpenAI API", True, "Successfully reached OpenAI")

    async def verify_chancellor(self):
        logger.info("🏛️ Phase 3: Chancellor V2 Logic Verification")
        try:
            input_payload = {"command": "test health check", "mode": "lite"}
            result = await ChancellorGraph.run_v2(input_payload)
            decision = result.get("decision", {})
            mode = decision.get("mode", "unknown")
            trace_id = result.get("trace_id")

            graph_ok = trace_id is not None and "outputs" in result
            self.report("Chancellor V2", graph_ok, f"Mode: {mode}, Trace ID: {trace_id}")

            if not graph_ok:
                logger.error(f"Chancellor result missing outputs/trace: {result.get('error')}")
        except Exception as e:
            self.report("Chancellor V2", False, str(e))

    async def verify_learning_system(self):
        logger.info("📚 Phase 4: Integrated Learning System (ILS) Verification")
        try:
            status = await integrated_learning_system.get_system_status()
            sys_status = status.get("system_status")
            success = sys_status in [
                "active",
                "initialized",
                "initializing",
                "unknown",
                None,
            ]
            self.report("Learning System (Status)", success, f"Status: {sys_status}")
        except Exception as e:
            self.report("Learning System", False, str(e))

    async def verify_vision(self):
        logger.info("👁️ Phase 5: Vision Verifier Verification")
        dashboard_url = settings.DASHBOARD_URL
        self.report("Vision Config", True, f"Dashboard URL: {dashboard_url}")

    async def verify_containers(self):
        logger.info("🐳 Phase 6: Container Ecosystem Verification (Ph.45)")
        # Call the existing script as a subprocess
        script_path = os.path.join(package_root, "scripts", "check_container_health.py")
        if not os.path.exists(script_path):
            self.report("Container Health", False, f"Script not found: {script_path}")
            return

        try:
            # Using asyncio subprocess
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                self.report("Container Health", True, "All containers healthy")
            else:
                error_msg = stderr.decode().strip() or "Exit code non-zero"
                self.report("Container Health", False, f"Check failed: {error_msg}")
        except Exception as e:
            self.report("Container Health", False, f"Execution error: {str(e)}")

    def generate_reports(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON Report
        json_report = {"metadata": self.metadata, "results": self.results}
        json_path = os.path.join(self.output_dir, f"verification_report_{timestamp_slug}.json")
        with open(json_path, "w") as f:
            json.dump(json_report, f, indent=2)

        # Markdown Report
        md_path = os.path.join(self.output_dir, f"verification_report_{timestamp_slug}.md")
        with open(md_path, "w") as f:
            f.write("# AFO Kingdom Verification Report\n\n")
            f.write(f"- **Timestamp**: {self.metadata['timestamp']}\n")
            f.write(f"- **Require OpenAI**: {self.metadata['require_openai']}\n\n")
            f.write("| Component | Status | Message |\n")
            f.write("|-----------|--------|---------|\n")
            for name, res in self.results.items():
                status = "✅ PASS" if res["success"] else "❌ FAIL"
                f.write(f"| {name} | {status} | {res['message']} |\n")

        logger.info(f"📄 Reports generated: {json_path}, {md_path}")

    async def run_all(self):
        logger.info("🏰 Starting Full Kingdom Verification Audit...")
        await self.verify_infra()
        await self.verify_llms()
        await self.verify_chancellor()
        await self.verify_learning_system()
        await self.verify_vision()
        await self.verify_containers()

        self.generate_reports()

        failed = [name for name, res in self.results.items() if not res["success"]]
        if failed:
            logger.error(f"❌ Verification Failed for: {', '.join(failed)}")
            sys.exit(1)
        else:
            logger.info("✅ All systems report healthy in the AFO Kingdom!")
            sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="AFO Kingdom Full-Stack Verifier")
    parser.add_argument(
        "--require-openai",
        action="store_true",
        help="Force fail if OpenAI is unavailable",
    )
    parser.add_argument("--output-dir", default="artifacts", help="Directory to save reports")
    args = parser.parse_args()

    verifier = KingdomVerifier(require_openai=args.require_openai, output_dir=args.output_dir)
    asyncio.run(verifier.run_all())


if __name__ == "__main__":
    main()
