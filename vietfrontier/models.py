"""Domain models and error types for the efficient-frontier TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class PortfolioDataError(RuntimeError):
    """Raised when price history cannot be fetched or aligned."""


class OptimizationError(RuntimeError):
    """Raised when the optimizer cannot produce a feasible portfolio."""


class PromptAction(StrEnum):
    """Possible actions the user can pick after a run."""

    RECONFIGURE = "reconfigure"
    QUIT = "quit"


@dataclass(frozen=True)
class PortfolioRequest:
    """User-supplied configuration for one optimization run."""

    symbols: tuple[str, ...]
    source: str
    start: str
    end: str
    risk_model: str
    objective: str
    n_samples: int
    return_model: str = "mean_historical"
    use_log_returns: bool = False
    ema_span: int = 500
    scatter_cmap: str = "copper"
    risk_free_rate: float = 0.03
    risk_aversion: float = 1.0


@dataclass(frozen=True)
class OptimizationResult:
    """Chosen portfolio weights and performance metrics."""

    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float
    method_name: str


@dataclass(frozen=True)
class FrontierData:
    """Data payload for the terminal chart renderer."""

    frontier_vols: list[float] = field(default_factory=list)
    frontier_rets: list[float] = field(default_factory=list)
    mc_vols: list[float] = field(default_factory=list)
    mc_rets: list[float] = field(default_factory=list)
    optimal_vol: float = 0.0
    optimal_ret: float = 0.0
