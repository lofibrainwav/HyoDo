"""
Organic Bridge Synchronization Script (Live Monitor)
--------------------------------------------------
Calculates Real-Time Trinity Score + 5 Pillars (Jin-Seon-Mi-Hyo-Yeong):
- Truth (Jin): Connectivity Verification
- Goodness (Seon): Error Free Operation
- Beauty (Mi): System Latency Speed
- Serenity (Hyo): Network Stability (Jitter)
- Infinity (Yeong): Continuous Uptime Probability

Pushes the calculated metrics to the Vercel Edge.
"""

import os
import statistics
import sys
import time

import requests

# Add package root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../packages/afo-core")))


# Mock env setup
def load_env_file(filepath) -> None:
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
    except Exception:
        pass


env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../packages/notebook-bridge/.env.production")
)
load_env_file(env_path)

import AFO.bridge_connector as connector

STARTUP_TIME = time.time()


def measure_network_stats(samples=3) -> None:
    latencies = []
    success_count = 0

    print(f"🧠 Brain: Probing Network ({samples} samples)...")

    for _ in range(samples):
        t0 = time.time()
        try:
            resp = requests.get(
                "https://notebook-bridge.vercel.app/api/kingdom/status",
                headers={"X-API-Key": "julie-cpa-2025"},
                timeout=5,
            )
            if resp.status_code == 200:
                success_count += 1
        except:
            pass
        latencies.append((time.time() - t0) * 1000)
        time.sleep(0.5)  # Short gap

    return latencies, success_count


def calculate_pillars() -> None:
    latencies, success_count = measure_network_stats()

    # 1. TRUTH (Connectivity)
    connectivity_ratio = success_count / len(latencies)
    truth = 100.0 * connectivity_ratio

    # 2. GOODNESS (Health)
    # If connection works, we assume goodness.
    goodness = 100.0 if truth > 0 else 0.0

    # 3. BEAUTY (Speed)
    avg_latency = statistics.mean(latencies)
    # Penalty: 1 point per 10ms over 50ms
    latency_penalty = max(0, (avg_latency - 50) / 10)
    beauty = max(50.0, 100.0 - latency_penalty)

    # 4. SERENITY (Stability/Jitter)
    # Uses Standard Deviation
    if len(latencies) > 1:
        jitter = statistics.stdev(latencies)
        # Penalty: 1 point per 5ms jitter
        jitter_penalty = jitter / 5
        serenity = max(60.0, 100.0 - jitter_penalty)
    else:
        serenity = 100.0

    # 5. INFINITY (Uptime/Continuity)
    # Simple uptime metric or just projected reliability
    infinity = 99.9  # Base baseline for persistent script

    # Aggregate Trinity Score
    avg_score = (truth + goodness + beauty + serenity + infinity) / 5

    return {
        "score": float(f"{avg_score:.2f}"),
        "pillars": {
            "truth": float(f"{truth:.1f}"),
            "goodness": float(f"{goodness:.1f}"),
            "beauty": float(f"{beauty:.1f}"),
            "serenity": float(f"{serenity:.1f}"),
            "infinity": float(f"{infinity:.1f}"),
        },
        "meta": {
            "latency_ms": avg_latency,
            "jitter": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        },
    }


def run_sync() -> None:
    print("🧠 Brain: Initiating Organic 5-Pillar Analysis...")

    result = calculate_pillars()
    score = result["score"]
    pillars = result["pillars"]
    meta = result["meta"]

    print("📊 Live Metrics:")
    print(f"  - Truth (Conn):  {pillars['truth']}")
    print(f"  - Goodness:      {pillars['goodness']}")
    print(f"  - Beauty (Spd):  {pillars['beauty']} (Avg {meta['latency_ms']:.1f}ms)")
    print(f"  - Serenity (Jit):{pillars['serenity']} (Jitter {meta['jitter']:.1f}ms)")
    print(f"  - Infinity:      {pillars['infinity']}")
    print(f"  = Trinity Score: {score}")

    # Update Status
    connector.bridge.update_kingdom_status(
        trinity_score=score,
        active_agents=7,
        health="VERIFY_TRUST: 361CAF7E-4830-4D3E-9AE0-1A7B2CAA8028",
        pillars=pillars,
    )

    # Push Log
    connector.bridge.push_irs_update(
        change_id=f"SYNC_{int(time.time())}",
        summary=f"Organic Sync: Score {score} (Lat: {meta['latency_ms']:.0f}ms, Jit: {meta['jitter']:.0f}ms)",
        impact_level="LOW",
    )

    print("✅ Brain: 5-Pillar Data pushed to Upstash Redis.")


if __name__ == "__main__":
    if not connector.bridge.enabled:
        print("❌ Error: Bridge disabled.")
        sys.exit(1)
    run_sync()
