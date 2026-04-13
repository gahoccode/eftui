"""Portfolio optimization wrapping PyPortfolioOpt with plotting-friendly outputs."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, HRPOpt, expected_returns, risk_models
from pypfopt.risk_models import CovarianceShrinkage

from vietfrontier.models import (
    FrontierData,
    OptimizationError,
    OptimizationResult,
    PortfolioRequest,
)

_RiskModelFn = Callable[[pd.DataFrame, bool], pd.DataFrame]
_ReturnModelFn = Callable[[pd.DataFrame, bool, int], pd.Series]


def _mean_historical_return(
    prices: pd.DataFrame,
    use_log_returns: bool,
    ema_span: int,
) -> pd.Series:
    """Historical annualized return estimator."""
    _ = ema_span
    return expected_returns.mean_historical_return(
        prices,
        log_returns=use_log_returns,
    )


def _ema_historical_return(
    prices: pd.DataFrame,
    use_log_returns: bool,
    ema_span: int,
) -> pd.Series:
    """Exponentially weighted annualized return estimator."""
    return expected_returns.ema_historical_return(
        prices,
        span=ema_span,
        log_returns=use_log_returns,
    )


def _sample_cov(prices: pd.DataFrame, use_log_returns: bool) -> pd.DataFrame:
    """Plain sample covariance estimator."""
    return risk_models.sample_cov(prices, log_returns=use_log_returns)


def _exp_cov(prices: pd.DataFrame, use_log_returns: bool) -> pd.DataFrame:
    """Exponentially weighted covariance estimator."""
    return risk_models.exp_cov(prices, log_returns=use_log_returns)


def _semicov(prices: pd.DataFrame, use_log_returns: bool) -> pd.DataFrame:
    """Semicovariance estimator (downside risk only)."""
    return risk_models.semicovariance(
        prices,
        benchmark=0,
        log_returns=use_log_returns,
    )


def _ledoit_wolf(prices: pd.DataFrame, use_log_returns: bool) -> pd.DataFrame:
    """Ledoit-Wolf shrinkage covariance estimator."""
    return CovarianceShrinkage(prices, log_returns=use_log_returns).ledoit_wolf()


def _oracle(prices: pd.DataFrame, use_log_returns: bool) -> pd.DataFrame:
    """Oracle approximating shrinkage covariance estimator."""
    return CovarianceShrinkage(
        prices,
        log_returns=use_log_returns,
    ).oracle_approximating()


class PortfolioOptimizer:
    """Run PyPortfolioOpt objectives and build frontier/Monte-Carlo payloads."""

    RETURN_MODELS: dict[str, _ReturnModelFn] = {
        "mean_historical": _mean_historical_return,
        "ema_historical": _ema_historical_return,
    }
    RISK_MODELS: dict[str, _RiskModelFn] = {
        "sample_cov": _sample_cov,
        "exp_cov": _exp_cov,
        "semicovariance": _semicov,
        "ledoit_wolf": _ledoit_wolf,
        "oracle_approximating": _oracle,
    }
    OBJECTIVES: tuple[str, ...] = (
        "max_sharpe",
        "min_volatility",
        "max_quadratic_utility",
        "hrp",
    )

    def __init__(self) -> None:
        """Initialize an empty input cache to avoid recomputing mu/S within a run."""
        self._cache_key: tuple[int, str, str, bool, int] | None = None
        self._cache_value: tuple[pd.Series, pd.DataFrame] | None = None

    def build_inputs(
        self,
        prices: pd.DataFrame,
        return_model: str,
        risk_model: str,
        use_log_returns: bool,
        ema_span: int,
    ) -> tuple[pd.Series, pd.DataFrame]:
        """Return (expected returns, covariance) using the chosen risk model."""
        if return_model not in self.RETURN_MODELS:
            raise OptimizationError(f"unknown return model: {return_model}")
        if risk_model not in self.RISK_MODELS:
            raise OptimizationError(f"unknown risk model: {risk_model}")
        mu = self.RETURN_MODELS[return_model](prices, use_log_returns, ema_span)
        S = self.RISK_MODELS[risk_model](prices, use_log_returns)
        return mu, S

    def _cached_inputs(
        self,
        prices: pd.DataFrame,
        return_model: str,
        risk_model: str,
        use_log_returns: bool,
        ema_span: int,
    ) -> tuple[pd.Series, pd.DataFrame]:
        """Return memoized mu/S for the current input configuration."""
        key = (id(prices), return_model, risk_model, use_log_returns, ema_span)
        if self._cache_key != key or self._cache_value is None:
            self._cache_value = self.build_inputs(
                prices,
                return_model,
                risk_model,
                use_log_returns,
                ema_span,
            )
            self._cache_key = key
        return self._cache_value

    def optimize(
        self,
        prices: pd.DataFrame,
        request: PortfolioRequest,
    ) -> OptimizationResult:
        """Dispatch to the requested optimization objective and return the result."""
        if request.objective not in self.OBJECTIVES:
            raise OptimizationError(f"unknown objective: {request.objective}")

        if request.objective == "hrp":
            return self._run_hrp(prices, request)

        mu, S = self._cached_inputs(
            prices,
            request.return_model,
            request.risk_model,
            request.use_log_returns,
            request.ema_span,
        )
        ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
        try:
            if request.objective == "max_sharpe":
                ef.max_sharpe(risk_free_rate=request.risk_free_rate)
            elif request.objective == "min_volatility":
                ef.min_volatility()
            else:
                ef.max_quadratic_utility(risk_aversion=request.risk_aversion)
        except Exception as exc:
            raise OptimizationError(str(exc)) from exc

        ret, vol, sharpe = ef.portfolio_performance(risk_free_rate=request.risk_free_rate)
        return OptimizationResult(
            weights=dict(ef.clean_weights()),
            expected_return=float(ret),
            volatility=float(vol),
            sharpe=float(sharpe),
            method_name=request.objective,
        )

    def _run_hrp(
        self,
        prices: pd.DataFrame,
        request: PortfolioRequest,
    ) -> OptimizationResult:
        """Run Hierarchical Risk Parity on the daily return panel."""
        returns = prices.pct_change().dropna()
        hrp = HRPOpt(returns=returns)
        try:
            hrp.optimize()
            ret, vol, sharpe = hrp.portfolio_performance(
                risk_free_rate=request.risk_free_rate
            )
        except Exception as exc:
            raise OptimizationError(str(exc)) from exc
        return OptimizationResult(
            weights=dict(hrp.clean_weights()),
            expected_return=float(ret),
            volatility=float(vol),
            sharpe=float(sharpe),
            method_name="hrp",
        )

    def build_frontier(
        self,
        mu: pd.Series,
        S: pd.DataFrame,
        n_points: int = 50,
    ) -> tuple[list[float], list[float]]:
        """Sweep target returns and collect (vol, ret) pairs along the frontier."""
        try:
            base = EfficientFrontier(mu, S, weight_bounds=(0, 1))
            base.min_volatility()
            lo_ret, _, _ = base.portfolio_performance()
        except Exception as exc:
            raise OptimizationError(f"frontier anchor failed: {exc}") from exc

        hi_ret = float(mu.max()) * 0.999
        if hi_ret <= lo_ret:
            return [], []

        targets = np.linspace(lo_ret, hi_ret, n_points)
        vols: list[float] = []
        rets: list[float] = []
        for target in targets:
            try:
                ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
                ef.efficient_return(target_return=float(target))
                ret, vol, _ = ef.portfolio_performance()
            except Exception:
                continue
            rets.append(float(ret))
            vols.append(float(vol))
        return vols, rets

    def monte_carlo(
        self,
        mu: pd.Series,
        S: pd.DataFrame,
        n_samples: int,
        rng: np.random.Generator | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Sample random long-only portfolios and return (vols, rets)."""
        rng = rng or np.random.default_rng()
        n_assets = len(mu)
        weights = rng.dirichlet(np.ones(n_assets), n_samples)
        rets = weights @ mu.values
        vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, S.values, weights))
        return vols, rets

    def build_frontier_data(
        self,
        prices: pd.DataFrame,
        request: PortfolioRequest,
        result: OptimizationResult,
    ) -> FrontierData:
        """Assemble the FrontierData payload for the terminal renderer."""
        mu, S = self._cached_inputs(
            prices,
            request.return_model,
            request.risk_model,
            request.use_log_returns,
            request.ema_span,
        )
        frontier_vols, frontier_rets = self.build_frontier(mu, S)
        mc_vols, mc_rets = self.monte_carlo(mu, S, n_samples=request.n_samples)
        return FrontierData(
            frontier_vols=frontier_vols,
            frontier_rets=frontier_rets,
            mc_vols=mc_vols.tolist(),
            mc_rets=mc_rets.tolist(),
            optimal_vol=result.volatility,
            optimal_ret=result.expected_return,
        )
