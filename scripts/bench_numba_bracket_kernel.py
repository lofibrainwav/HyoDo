import json
import time

import numpy as np
from numba import njit


def bracket_tax_py(income, thresholds, rates) -> None:
    tax = 0.0
    prev = 0.0
    for cap, r in zip(thresholds, rates[:-1]):
        if income <= cap:
            return tax + (income - prev) * r
        tax += (cap - prev) * r
        prev = cap
    return tax + (income - prev) * rates[-1]


@njit(cache=True)
def bracket_tax_nb(income, thresholds, rates) -> None:
    tax = 0.0
    prev = 0.0
    n = thresholds.shape[0]
    for i in range(n):
        cap = thresholds[i]
        r = rates[i]
        if income <= cap:
            return tax + (income - prev) * r
        tax += (cap - prev) * r
        prev = cap
    return tax + (income - prev) * rates[n]


def pct(a, p) -> None:
    return float(np.percentile(a, p))


def run(fn, incomes, thresholds, rates) -> None:
    t = np.empty(incomes.shape[0], dtype=np.float64)
    for i in range(incomes.shape[0]):
        s = time.perf_counter_ns()
        fn(float(incomes[i]), thresholds, rates)
        e = time.perf_counter_ns()
        t[i] = (e - s) / 1e6
    return t


def main() -> None:
    thresholds = np.array([11925, 48475, 103350, 197300, 250525, 626350], dtype=np.float64)
    rates = np.array([0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37], dtype=np.float64)
    rng = np.random.default_rng(7)
    incomes = rng.uniform(1, 800000, size=5000).astype(np.float64)

    bracket_tax_nb(10.0, thresholds, rates)

    for x in rng.uniform(1, 800000, size=200).astype(np.float64):
        a = bracket_tax_py(float(x), thresholds, rates)
        b = bracket_tax_nb(float(x), thresholds, rates)
        if not np.isclose(a, b, rtol=0, atol=1e-9):
            raise SystemExit(f"Mismatch income={x} py={a} nb={b}")

    t_py = run(bracket_tax_py, incomes, thresholds, rates)
    t_nb = run(bracket_tax_nb, incomes, thresholds, rates)

    out = {
        "py_ms": {"p50": pct(t_py, 50), "p95": pct(t_py, 95), "p99": pct(t_py, 99)},
        "nb_ms": {"p50": pct(t_nb, 50), "p95": pct(t_nb, 95), "p99": pct(t_nb, 99)},
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
