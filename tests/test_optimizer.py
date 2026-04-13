"""Tests for PortfolioOptimizer using a deterministic synthetic price panel."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vietfrontier.models import OptimizationError, PortfolioRequest
from vietfrontier.services.optimizer import PortfolioOptimizer


def _make_prices(seed: int = 7, rows: int = 400) -> pd.DataFrame:
    """Build a synthetic 4-asset price panel with distinct drifts."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-03", periods=rows, freq="B")
    drifts = np.array([0.0004, 0.0006, 0.0002, 0.0008])
    vols = np.array([0.012, 0.015, 0.009, 0.018])
    noise = rng.standard_normal((rows, 4)) * vols
    log_ret = drifts + noise
    prices = 100.0 * np.exp(np.cumsum(log_ret, axis=0))
    return pd.DataFrame(prices, index=dates, columns=["AAA", "BBB", "CCC", "DDD"])


def _request(**overrides: object) -> PortfolioRequest:
    defaults: dict[str, object] = dict(
        symbols=("AAA", "BBB", "CCC", "DDD"),
        source="VCI",
        start="2022-01-03",
        end="2023-08-03",
        return_model="mean_historical",
        use_log_returns=False,
        ema_span=500,
        risk_model="sample_cov",
        objective="max_sharpe",
        n_samples=500,
        risk_free_rate=0.02,
        risk_aversion=1.0,
    )
    defaults.update(overrides)
    return PortfolioRequest(**defaults)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("return_model", "risk_model"),
    [
        ("mean_historical", "sample_cov"),
        ("mean_historical", "exp_cov"),
        ("mean_historical", "semicovariance"),
        ("mean_historical", "ledoit_wolf"),
        ("mean_historical", "oracle_approximating"),
        ("ema_historical", "sample_cov"),
    ],
)
def test_build_inputs_supports_return_and_risk_models(
    return_model: str,
    risk_model: str,
) -> None:
    opt = PortfolioOptimizer()
    mu, S = opt.build_inputs(
        _make_prices(),
        return_model,
        risk_model,
        use_log_returns=False,
        ema_span=500,
    )
    assert list(mu.index) == ["AAA", "BBB", "CCC", "DDD"]
    assert S.shape == (4, 4)


def test_build_inputs_rejects_unknown_risk_model() -> None:
    opt = PortfolioOptimizer()
    with pytest.raises(OptimizationError, match="unknown risk model"):
        opt.build_inputs(
            _make_prices(),
            "mean_historical",
            "nonsense",
            use_log_returns=False,
            ema_span=500,
        )


def test_build_inputs_rejects_unknown_return_model() -> None:
    opt = PortfolioOptimizer()
    with pytest.raises(OptimizationError, match="unknown return model"):
        opt.build_inputs(
            _make_prices(),
            "nonsense",
            "sample_cov",
            use_log_returns=False,
            ema_span=500,
        )


def test_build_inputs_log_return_toggle_changes_expected_returns() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    mu_simple, _ = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    mu_log, _ = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=True,
        ema_span=500,
    )

    assert not mu_simple.equals(mu_log)


def test_build_inputs_ema_span_changes_expected_returns() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    mu_fast, _ = opt.build_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=60,
    )
    mu_slow, _ = opt.build_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )

    assert not mu_fast.equals(mu_slow)


def test_build_inputs_log_return_toggle_changes_covariance() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    _, cov_simple = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    _, cov_log = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=True,
        ema_span=500,
    )

    assert not cov_simple.equals(cov_log)


def test_build_inputs_log_return_toggle_changes_shrinkage_covariance() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    _, cov_simple = opt.build_inputs(
        prices,
        "mean_historical",
        "ledoit_wolf",
        use_log_returns=False,
        ema_span=500,
    )
    _, cov_log = opt.build_inputs(
        prices,
        "mean_historical",
        "ledoit_wolf",
        use_log_returns=True,
        ema_span=500,
    )

    assert not cov_simple.equals(cov_log)


@pytest.mark.parametrize(
    "objective",
    ["max_sharpe", "min_volatility", "max_quadratic_utility", "hrp"],
)
def test_optimize_returns_valid_weights_for_every_objective(objective: str) -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()
    result = opt.optimize(prices, _request(objective=objective))

    assert result.method_name == objective
    assert set(result.weights.keys()) == {"AAA", "BBB", "CCC", "DDD"}
    assert sum(result.weights.values()) == pytest.approx(1.0, abs=1e-4)
    assert all(w >= -1e-6 for w in result.weights.values())
    assert result.volatility > 0.0


def test_build_frontier_returns_monotone_increasing_vols_and_rets() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()
    mu, S = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    vols, rets = opt.build_frontier(mu, S, n_points=25)
    assert len(vols) == len(rets) >= 5
    assert rets == sorted(rets)


def test_monte_carlo_vectorized_shapes_and_bounds() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()
    mu, S = opt.build_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    vols, rets = opt.monte_carlo(mu, S, n_samples=300)
    assert vols.shape == rets.shape == (300,)
    assert np.all(vols > 0.0)
    assert np.all(np.isfinite(rets))


def test_build_frontier_data_bundles_everything() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()
    request = _request(n_samples=200)
    result = opt.optimize(prices, request)
    data = opt.build_frontier_data(prices, request, result)

    assert len(data.mc_vols) == 200
    assert len(data.frontier_vols) == len(data.frontier_rets) > 0
    assert data.optimal_vol == pytest.approx(result.volatility)
    assert data.optimal_ret == pytest.approx(result.expected_return)


def test_cached_inputs_respects_return_model_and_log_return_flags() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    mu_mean, cov_mean = opt._cached_inputs(
        prices,
        "mean_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    mu_ema, _ = opt._cached_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )
    mu_log, cov_log = opt._cached_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=True,
        ema_span=500,
    )

    assert not mu_mean.equals(mu_ema)
    assert not mu_ema.equals(mu_log)
    assert not cov_mean.equals(cov_log)


def test_cached_inputs_respects_ema_span() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    mu_fast, _ = opt._cached_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=60,
    )
    mu_slow, _ = opt._cached_inputs(
        prices,
        "ema_historical",
        "sample_cov",
        use_log_returns=False,
        ema_span=500,
    )

    assert not mu_fast.equals(mu_slow)


def test_optimize_log_return_toggle_changes_non_hrp_result() -> None:
    opt = PortfolioOptimizer()
    prices = _make_prices()

    simple_result = opt.optimize(prices, _request(use_log_returns=False))
    log_result = opt.optimize(prices, _request(use_log_returns=True))

    assert simple_result.weights != log_result.weights
