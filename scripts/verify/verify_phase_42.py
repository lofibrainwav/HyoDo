import sys
from pathlib import Path

# Ensure packages path
sys.path.append(str(Path("packages").resolve()))
sys.path.append(str(Path("packages/afo-core").resolve()))


def verify_config() -> None:
    print("Core Configuration Verification...")
    try:
        from AFO.config.log_analysis import log_analysis_settings

        print("✅ LogAnalysisSettings imported.")

        # Check new fields
        assert hasattr(log_analysis_settings, "MAX_RETRIES"), "MAX_RETRIES missing"
        assert hasattr(log_analysis_settings, "RETRY_DELAY"), "RETRY_DELAY missing"
        assert hasattr(log_analysis_settings, "ENABLE_MONITORING"), "ENABLE_MONITORING missing"
        assert hasattr(log_analysis_settings, "MEMORY_THRESHOLD_MB"), "MEMORY_THRESHOLD_MB missing"

        print("✅ New Configuration Fields Verified.")
        print(f"   MAX_RETRIES: {log_analysis_settings.MAX_RETRIES}")
        print(f"   ENABLE_MONITORING: {log_analysis_settings.ENABLE_MONITORING}")

    except ImportError as e:
        print(f"❌ ImportError: {e}")
        return False
    except AssertionError as e:
        print(f"❌ AssertionError: {e}")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    return True


def verify_metrics() -> None:
    print("\nMetrics Verification...")
    try:
        from AFO.utils.metrics import (  # noqa: F401
            log_analysis_chunks_processed_total,
            log_analysis_errors_total,
            log_analysis_processing_seconds,
        )

        print("✅ Log Analysis Metrics imported.")
        return True
    except ImportError:
        print("❌ Failed to import Log Analysis Metrics")
        return False


def verify_analyzer_streaming() -> None:
    print("\nSequential Analyzer Optimization Verification...")
    try:
        sys.path.append("scripts")
        from sequential_analyzer import SequentialAnalyzer

        analyzer = SequentialAnalyzer(chunks_dir="logs")
        if hasattr(analyzer, "analyze_stream_chunks"):
            print("✅ analyze_stream_chunks method found.")
            if hasattr(analyzer.analyze_stream_chunks, "__call__"):
                print("✅ analyze_stream_chunks is callable.")
                return True
        else:
            print("❌ analyze_stream_chunks method MISSING.")
            return False
    except ImportError:
        print("❌ Failed to import SequentialAnalyzer from scripts/")
        return False
    except Exception as e:
        print(f"❌ Exception checking analyzer: {e}")
        return False


if __name__ == "__main__":
    print("🛡️ Phase 42 Verification Protocol Initiated 🛡️\n")

    c_ok = verify_config()
    m_ok = verify_metrics()
    a_ok = verify_analyzer_streaming()

    if c_ok and m_ok and a_ok:
        print("\n✨ Phase 42 Verification SUCCESSFUL! ✨")
        sys.exit(0)
    else:
        print("\n⚠️ Phase 42 Verification FAILED.")
        sys.exit(1)
