#!/usr/bin/env python3
import os
from urllib.request import Request, urlopen

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
JOB = os.getenv("AFO_METRICS_JOB", "afo_ci_quality")
INSTANCE = os.getenv("AFO_INSTANCE", "afo_kingdom_main")
WORKFLOW = os.getenv("AFO_WORKFLOW", "unknown")
REPO = os.getenv("AFO_REPO", "lofibrainwav/AFO_Kingdom")


def _to_float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def push_metrics(payload: str) -> None:
    url = f"{PUSHGATEWAY_URL}/metrics/job/{JOB}/instance/{INSTANCE}/workflow/{WORKFLOW}"
    req = Request(url=url, data=payload.encode("utf-8"), method="PUT")
    req.add_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")

    # Basic Auth 지원
    basic_auth = os.getenv("PUSHGATEWAY_BASIC_AUTH")
    if basic_auth:
        import base64

        auth_string = base64.b64encode(basic_auth.encode()).decode()
        req.add_header("Authorization", f"Basic {auth_string}")

    with urlopen(req, timeout=10) as resp:
        if resp.status >= 400:
            msg = f"Pushgateway error: {resp.status}"
            raise RuntimeError(msg)


def main() -> int:
    # CI env inputs (numbers)
    english_ratio = _to_float(os.getenv("AFO_REPORT_ENGLISH_RATIO", "0"))
    pr_risk_score = _to_float(os.getenv("AFO_PR_RISK_SCORE", "0"))
    chaos_success = _to_float(os.getenv("AFO_CHAOS_LAST_SUCCESS", "0"))
    chaos_self_heal_seconds_last = _to_float(os.getenv("AFO_CHAOS_SELF_HEAL_SECONDS", "0"))
    ssot_fail_24h = _to_float(os.getenv("AFO_SSOT_FAIL_24H", "0"))

    lines = []

    # SSOT Gauges (Pushgateway는 타임스탬프 허용하지 않음)
    lines.append("# TYPE afo_report_english_ratio gauge")
    lines.append(f'afo_report_english_ratio{{repo="{REPO}"}} {english_ratio}')

    lines.append("# TYPE afo_pr_risk_score gauge")
    lines.append(f'afo_pr_risk_score{{repo="{REPO}"}} {pr_risk_score}')

    lines.append("# TYPE afo_chaos_nightly_success gauge")
    lines.append(f'afo_chaos_nightly_success{{repo="{REPO}",test_type="lite"}} {chaos_success}')

    # Histogram SSOT 유지 + A1용 gauge 파생치
    lines.append("# TYPE afo_chaos_selfheal_seconds_last gauge")
    lines.append(
        f'afo_chaos_selfheal_seconds_last{{repo="{REPO}",test_type="lite"}} {chaos_self_heal_seconds_last}'
    )

    # Counter 대신 임시 gauge (A1)
    lines.append("# TYPE afo_report_ssot_gate_fail_24h gauge")
    lines.append(f'afo_report_ssot_gate_fail_24h{{repo="{REPO}"}} {ssot_fail_24h}')

    payload = "\n".join(lines) + "\n"
    push_metrics(payload)
    print("Pushed CI quality metrics to Pushgateway:", PUSHGATEWAY_URL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
