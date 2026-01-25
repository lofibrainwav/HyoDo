import argparse
import inspect
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

METHOD_CANDIDATES = ["calculate", "compute", "calc", "run", "__call__"]

DEFAULT_PAYLOAD = {
    "year": 2025,
    "tax_year": 2025,
    "filing_status": "single",
    "status": "single",
    "state": "CA",
    "taxable_income": 50000,
    "income": 50000,
    "agi": 50000,
    "magi": 50000,
    "age": 30,
}


def now_iso() -> None:
    return datetime.now(timezone.utc).isoformat()


def git_sha() -> None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def pick_callable(obj) -> None:
    for name in METHOD_CANDIDATES:
        if hasattr(obj, name):
            fn = getattr(obj, name)
            if callable(fn):
                return name, fn
    return None, None


def build_kwargs(fn, payload) -> None:
    sig = inspect.signature(fn)
    params = sig.parameters
    # if single positional param likely dict-like, pass full payload
    if len(params) == 1:
        (pname, p) = next(iter(params.items()))
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            return ("single_arg", {pname: payload}), None
    # otherwise intersect by name
    kwargs = {}
    missing_required = []
    for pname, p in params.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if pname in payload:
            kwargs[pname] = payload[pname]
        elif p.default is not inspect.Parameter.empty:
            kwargs[pname] = p.default
        else:
            missing_required.append(pname)

    if missing_required:
        return None, missing_required
    return ("kwargs", kwargs), None


def run_once(payload) -> None:
    try:
        from afo.tax_engine.calculator import TaxCalculator  # type: ignore
    except Exception as e:
        raise RuntimeError(f"IMPORT_FAIL: afo.tax_engine.calculator.TaxCalculator not found ({e})")

    try:
        calc = TaxCalculator()
    except Exception as e:
        raise RuntimeError(f"INIT_FAIL: TaxCalculator() failed ({e})")

    mname, fn = pick_callable(calc)
    if fn is None:
        raise RuntimeError(
            "CALLABLE_FAIL: No callable method found on TaxCalculator (tried calculate/compute/calc/run/__call__)"
        )

    call_plan, missing = build_kwargs(fn, payload)
    if call_plan is None:
        raise RuntimeError(f"ARGS_FAIL: Method '{mname}' requires params not in payload: {missing}")

    mode, args = call_plan
    if mode == "single_arg":
        next(iter(args.keys()))
        return fn(**args)


def percentile(sorted_vals, p) -> None:
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return float(d0 + d1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=30)
    ap.add_argument("--out", type=str, default="")
    ap.add_argument("--payload", type=str, default="")
    args = ap.parse_args()

    payload = dict(DEFAULT_PAYLOAD)
    if args.payload:
        payload.update(json.loads(Path(args.payload).read_text(encoding="utf-8")))

    out_path = (
        Path(args.out)
        if args.out
        else Path("artifacts")
        / f"bench_tax_engine_latency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "as_of": now_iso(),
        "git_sha": git_sha(),
        "python": sys.version.split()[0],
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "method": {
            "timer": "perf_counter_ns",
            "warmup_runs": args.warmup,
            "measured_runs": args.runs,
            "payload": payload,
        },
    }

    # warmup
    for _ in range(args.warmup):
        run_once(payload)

    samples_ms = []
    with out_path.open("w", encoding="utf-8") as f:
        for i in range(args.runs):
            t0 = time.perf_counter_ns()
            run_once(payload)
            t1 = time.perf_counter_ns()
            ms = (t1 - t0) / 1_000_000.0
            samples_ms.append(ms)
            row = {
                "ticket": "PERF_BENCH_TAX_ENGINE",
                "run": i + 1,
                "latency_ms": ms,
                "meta": meta if i == 0 else None,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    s = sorted(samples_ms)
    summary = {
        "as_of": meta["as_of"],
        "git_sha": meta["git_sha"],
        "python": meta["python"],
        "p50_ms": percentile(s, 50),
        "p95_ms": percentile(s, 95),
        "mean_ms": float(statistics.mean(samples_ms)),
        "runs": args.runs,
        "warmup": args.warmup,
        "out_jsonl": str(out_path),
    }
    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("✅ Bench complete")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
