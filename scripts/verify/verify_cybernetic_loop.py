import asyncio
import logging
import shutil
import sys
from pathlib import Path

# Setup Path
sys.path.append("packages/afo-core")

from AFO.config.log_analysis import log_analysis_settings
from AFO.serenity.self_diagnostics import SelfDiagnostics
from AFO.services.log_analysis import LogAnalysisService


async def verify_loop():
    print("🔄 Cybernetic Loop Verification Initiated...")

    # 1. Setup Environment
    # Use a temporary output directory for isolation
    test_output_dir = Path("verify_loop_results")
    test_output_dir.mkdir(exist_ok=True)

    # Temporarily override settings
    # (In a real app, we'd use env vars or dependency injection, but here we patch the object)
    original_output_dir = log_analysis_settings.OUTPUT_DIR
    log_analysis_settings.OUTPUT_DIR = test_output_dir

    service = LogAnalysisService(output_dir=str(test_output_dir))
    diagnostics = SelfDiagnostics()

    # 2. Baseline Check (Should be healthy or quiet)
    print("\n[Step 1] Baseline Diagnostics")
    baseline = await diagnostics.run_full_diagnosis()
    print(f"Baseline Score: {baseline['trinity']['trinity_score']}")

    # 3. Inject Critical Error Log
    print("\n[Step 2] Injecting Critical Log")
    log_file = test_output_dir / "critical.log"
    log_file.write_text(
        "2024-01-01 10:00:00 [ERROR] CRITICAL: Database corruption detected.\n"
        + "Expected an indented block\n"  # Trigger syntax error pattern
    )

    # 4. Trigger Analysis (Observation)
    print("\n[Step 3] Running Log Analysis")
    result = service.run_pipeline(str(log_file))
    report_file = result["sequential"]["report_file"]
    print(f"Analysis Report Generated: {report_file}")

    # 5. Check Diagnostics Again (Impact)
    print("\n[Step 4] Post-Analysis Diagnostics")
    post_analysis = await diagnostics.run_full_diagnosis()
    truth_lens = next(d for d in post_analysis["details"] if d.lens == "眞")

    print(f"Post-Analysis Truth Score: {truth_lens.score}")
    print("Findings:")
    for f in truth_lens.findings:
        print(f" - {f}")

    # 6. Verification
    success = False
    if truth_lens.score < 1.0:
        print("\n✅ SUCCESS: Truth score degraded due to log analysis findings.")
        success = True
    else:
        print("\n❌ FAILURE: Truth score did not degrade.")

    if any("CRITICAL: Log Analysis" in f for f in truth_lens.findings):
        print("✅ SUCCESS: Critical finding detected in diagnostics.")
    else:
        print("❌ FAILURE: Critical finding NOT detected.")
        success = False

    # Cleanup
    log_analysis_settings.OUTPUT_DIR = original_output_dir
    shutil.rmtree(test_output_dir)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(verify_loop())
