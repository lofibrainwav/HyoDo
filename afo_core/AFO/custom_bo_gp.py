"""
커스텀 GP+EI Bayesian Optimization
연속 파라미터 최적화용 (MIPROv2와 분리)
"""

from collections.abc import Callable

import numpy as np
from numpy import ndarray
from scipy.stats import norm


class GaussianProcess:
    """Gaussian Process for Bayesian Optimization"""

    def __init__(self, kernel: str = "RBF", length_scale: float = 1.0, noise: float = 1e-6) -> None:
        self.kernel = kernel
        self.length_scale = length_scale
        self.noise = noise
        self.X_train: ndarray | None = None
        self.y_train: ndarray | None = None
        self.K: ndarray | None = None
        self.K_inv: ndarray | None = None

    def _rbf_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """RBF (Radial Basis Function) Kernel"""
        X1 = X1.reshape(-1, 1) if X1.ndim == 1 else X1
        X2 = X2.reshape(-1, 1) if X2.ndim == 1 else X2
        sqdist = np.sum(X1**2, 1).reshape(-1, 1) + np.sum(X2**2, 1) - 2 * np.dot(X1, X2.T)
        return np.exp(-0.5 * sqdist / (self.length_scale**2))

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """GP 학습"""
        self.X_train = X.reshape(-1, 1) if X.ndim == 1 else X
        self.y_train = y.flatten()

        n = len(self.X_train)
        self.K = self._rbf_kernel(self.X_train, self.X_train) + self.noise * np.eye(n)
        self.K_inv = np.linalg.inv(self.K)

    def predict(self, X_new: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """새로운 지점 예측 (평균, 분산)"""
        if self.X_train is None or self.K_inv is None:
            raise ValueError("GP must be fitted before prediction")

        X_new = X_new.reshape(-1, 1) if X_new.ndim == 1 else X_new
        K_star = self._rbf_kernel(self.X_train, X_new)
        K_star_star = self._rbf_kernel(X_new, X_new)

        mu = K_star.T @ self.K_inv @ self.y_train
        cov = K_star_star - K_star.T @ self.K_inv @ K_star
        sigma = np.sqrt(np.maximum(np.diag(cov), 0))  # Ensure non-negative

        return mu, sigma


def expected_improvement(
    X: np.ndarray, gp: GaussianProcess, f_best: float, xi: float = 0.01
) -> np.ndarray:
    """
    Expected Improvement (EI) 계산

    EI(x) = σ(x) * [ξ * Φ(ξ) + φ(ξ)]
    ξ = (μ(x) - f_best - ξ) / σ(x)
    """
    mu, sigma = gp.predict(X)

    with np.errstate(divide="warn", invalid="warn"):
        xi_normalized = (mu - f_best - xi) / sigma

        # σ(x)가 0인 경우 처리
        ei = np.zeros_like(mu)
        valid = sigma > 1e-10

        if np.any(valid):
            ei[valid] = sigma[valid] * (
                xi_normalized[valid] * norm.cdf(xi_normalized[valid])
                + norm.pdf(xi_normalized[valid])
            )

    return ei


def bayesian_optimize(
    objective_fn: Callable[[float], float],
    bounds: tuple[float, float],
    n_initial: int = 5,
    n_iterations: int = 10,
    xi: float = 0.01,
    random_state: int = 42,
) -> tuple[float, float]:
    """
    Bayesian Optimization using GP + EI

    Args:
        objective_fn: 최적화할 함수 (maximize)
        bounds: (lower, upper) 범위
        n_initial: 초기 랜덤 샘플 수
        n_iterations: BO 반복 수
        xi: EI exploration parameter
        random_state: 재현성을 위한 시드

    Returns:
        (optimal_x, optimal_y)
    """

    np.random.seed(random_state)
    lower, upper = bounds

    # 초기 랜덤 샘플링
    X_samples = np.random.uniform(lower, upper, n_initial)
    y_samples = np.array([objective_fn(x) for x in X_samples])

    gp = GaussianProcess()

    for iteration in range(n_iterations):
        # GP 학습
        gp.fit(X_samples, y_samples)

        # 현재 최적값
        f_best = np.max(y_samples)

        # EI 기반 다음 후보 선택 (최적화로 찾기)
        def ei_negative(x) -> None:
            return -expected_improvement(np.array([x]), gp, f_best, xi)[0]

        # 여러 시작점에서 최적화
        candidates = np.linspace(lower, upper, 100)
        ei_values = expected_improvement(candidates.reshape(-1, 1), gp, f_best, xi)
        best_idx = np.argmax(ei_values)
        next_x = candidates[best_idx]

        # 평가
        next_y = objective_fn(next_x)

        # 데이터 추가
        X_samples = np.append(X_samples, next_x)
        y_samples = np.append(y_samples, next_y)

    # 최종 최적값
    best_idx = np.argmax(y_samples)
    optimal_x = X_samples[best_idx]
    optimal_y = y_samples[best_idx]

    return optimal_x, optimal_y


# 예시 사용법 (테스트용)
if __name__ == "__main__":
    # 테스트 함수: f(x) = -(x-2)^2 + 1 (최대값은 x=2에서 1)
    def test_fn(x) -> None:
        return -((x - 2) ** 2) + 1

    # 최적화 실행
    bounds = (0, 4)
    optimal_x, optimal_y = bayesian_optimize(test_fn, bounds, n_initial=3, n_iterations=5)

    print(".2f")
    print(".4f")  # 실제 최적값: x=2, y=1
