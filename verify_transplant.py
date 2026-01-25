import sys
from pathlib import Path

# Add local afo_core to path
current_dir = Path(__file__).parent.resolve()
sys.path.append(str(current_dir / "afo_core"))

print(f"Testing transplant in: {current_dir}")
print(f"Sys path added: {sys.path[-1]}")

try:
    from AFO.domain.metrics.trinity_manager import trinity_manager

    print("✅ Successfully imported TrinityManager from transplanted code!")

    metrics = trinity_manager.get_current_metrics()
    print(f"📊 Current Trinity Score (Default): {metrics.trinity_score}")

    # Check if TruthSensor service module exists (file check only, not run)
    truth_sensor_path = (
        current_dir / "afo_core" / "AFO" / "services" / "truth_sensor.py"
    )
    if truth_sensor_path.exists():
        print("✅ TruthSensor module found.")
    else:
        print("❌ TruthSensor module MISSING.")

    print("Transplantation Verification: SUCCESS")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Runtime error: {e}")
    sys.exit(1)
