import json
import time

import numpy as np
from numba import njit


def pure_python_matmul(A, B) -> None:
    """Pure Python matrix multiplication"""
    m, n = A.shape
    n, p = B.shape
    C = np.zeros((m, p))
    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i, j] += A[i, k] * B[k, j]
    return C


@njit(parallel=True, cache=True)
def numba_matmul(A, B) -> None:
    """Numba parallel matrix multiplication"""
    m, n = A.shape
    n, p = B.shape
    C = np.zeros((m, p))
    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i, j] += A[i, k] * B[k, j]
    return C


def benchmark_matmul(sizes, runs=3) -> None:
    """Benchmark matrix multiplication implementations"""
    results = {}

    for size in sizes:
        print(f"Benchmarking {size}x{size} matrices...")

        # Generate random matrices
        A = np.random.rand(size, size).astype(np.float64)
        B = np.random.rand(size, size).astype(np.float64)

        # Warmup
        _ = np.dot(A, B)
        _ = numba_matmul(A, B)

        # Benchmark NumPy (BLAS)
        times_numpy = []
        for _ in range(runs):
            start = time.perf_counter_ns()
            np.dot(A, B)
            end = time.perf_counter_ns()
            times_numpy.append((end - start) / 1e6)  # Convert to ms

        # Benchmark Numba
        times_numba = []
        for _ in range(runs):
            start = time.perf_counter_ns()
            numba_matmul(A, B)
            end = time.perf_counter_ns()
            times_numba.append((end - start) / 1e6)

        # Benchmark Pure Python (small sizes only)
        times_python = []
        if size <= 64:  # Only benchmark pure Python for small matrices
            for _ in range(runs):
                start = time.perf_counter_ns()
                pure_python_matmul(A, B)
                end = time.perf_counter_ns()
                times_python.append((end - start) / 1e6)

        # Calculate statistics
        results[size] = {
            "numpy_blas": {
                "mean_ms": float(np.mean(times_numpy)),
                "std_ms": float(np.std(times_numpy)),
                "min_ms": float(np.min(times_numpy)),
                "max_ms": float(np.max(times_numpy)),
            },
            "numba_parallel": {
                "mean_ms": float(np.mean(times_numba)),
                "std_ms": float(np.std(times_numba)),
                "min_ms": float(np.min(times_numba)),
                "max_ms": float(np.max(times_numba)),
            },
        }

        if times_python:
            results[size]["pure_python"] = {
                "mean_ms": float(np.mean(times_python)),
                "std_ms": float(np.std(times_python)),
                "min_ms": float(np.min(times_python)),
                "max_ms": float(np.max(times_python)),
            }

        # Calculate GFLOPS (approximate)
        operations = 2 * size**3  # Multiply-add operations
        gflops_numpy = operations / (np.mean(times_numpy) * 1e6) / 1e9
        gflops_numba = operations / (np.mean(times_numba) * 1e6) / 1e9

        results[size]["performance"] = {
            "numpy_gflops": float(gflops_numpy),
            "numba_gflops": float(gflops_numba),
            "speedup_numba_vs_numpy": float(np.mean(times_numpy) / np.mean(times_numba)),
        }

        print(f"  NumPy BLAS: {np.mean(times_numpy):.3f}ms ({gflops_numpy:.2f} GFLOPS)")
        print(f"  Numba parallel: {np.mean(times_numba):.3f}ms ({gflops_numba:.2f} GFLOPS)")
        if times_python:
            speedup_py = np.mean(times_python) / np.mean(times_numpy)
            print(
                f"  Pure Python: {np.mean(times_python):.3f}ms ({speedup_py:.1f}x slower than NumPy)"
            )
    return results


def main() -> None:
    print("Matrix Multiplication Benchmark Suite")
    print("=" * 50)

    # Test various sizes
    sizes = [32, 64, 128, 256, 512]

    results = benchmark_matmul(sizes)

    # Save results
    output = {
        "benchmark_info": {
            "numpy_version": np.__version__,
            "blas_library": "Apple Accelerate",
            "cpu_cores": "M-series (estimated)",
            "timestamp": time.time(),
        },
        "results": results,
    }

    with open("artifacts/matrix_multiplication_benchmark_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(
        "\nBenchmark complete! Results saved to artifacts/matrix_multiplication_benchmark_results.json"
    )


if __name__ == "__main__":
    main()
