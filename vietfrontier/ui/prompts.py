"""Interactive questionary-backed prompt session for the portfolio TUI."""

from __future__ import annotations

from importlib import import_module

from rich.console import Console

from vietfrontier.models import PortfolioRequest, PromptAction
from vietfrontier.services.optimizer import PortfolioOptimizer

_SOURCES = ["VCI", "KBS"]
_SCATTER_CMAPS: list[str] = [
    "copper",
    "gist_heat",
    "Greys",
    "gist_yarg",
    "gist_gray",
    "cividis",
    "magma",
    "inferno",
    "plasma",
    "viridis",
]
_DEFAULT_SCATTER_CMAP = "copper"
_DEFAULT_RETURN_MODEL = "mean_historical"
_DEFAULT_RISK_MODEL = "ledoit_wolf"
_DEFAULT_EMA_SPAN = 500
_MIN_EMA_SPAN = 2
_LOG_RETURN_CHOICES = ["no", "yes"]


def _validate_ema_span(value: str) -> bool | str:
    """Return a questionary-compatible validation result for EMA span input."""
    try:
        span = int(value)
    except ValueError:
        return "EMA smoothing span must be an integer."
    if span < _MIN_EMA_SPAN:
        return f"EMA smoothing span must be an integer >= {_MIN_EMA_SPAN}."
    return True


class PromptSession:
    """Collect user configuration via questionary and render messages via rich."""

    def __init__(
        self,
        console: Console,
        questionary_module: object | None = None,
    ) -> None:
        """Initialize the session with an injectable questionary module."""
        self._console = console
        self._questionary = questionary_module

    def collect_request(self) -> PortfolioRequest:
        """Prompt the user for every field needed to run one optimization."""
        q = self._questionary or import_module("questionary")
        return_models = list(PortfolioOptimizer.RETURN_MODELS)
        risk_models = list(PortfolioOptimizer.RISK_MODELS)
        objectives = list(PortfolioOptimizer.OBJECTIVES)

        raw_symbols = str(
            q.text("Symbols (comma-separated)", default="ACB,VCB,FPT,HPG,MWG").ask()
        )
        symbols = tuple(s.strip().upper() for s in raw_symbols.split(",") if s.strip())

        source = str(q.select("Source", choices=_SOURCES, default="VCI").ask()).upper()
        start = str(q.text("Start date (YYYY-MM-DD)", default="2023-01-01").ask())
        end = str(q.text("End date (YYYY-MM-DD)", default="2024-12-31").ask())

        objective = str(
            q.select("Objective", choices=objectives, default="max_sharpe").ask()
        )
        if objective == "hrp":
            return_model = _DEFAULT_RETURN_MODEL
            use_log_returns = False
            ema_span = _DEFAULT_EMA_SPAN
            risk_model = _DEFAULT_RISK_MODEL
        else:
            return_model = str(
                q.select(
                    "Return method",
                    choices=return_models,
                    default=_DEFAULT_RETURN_MODEL,
                ).ask()
            )
            use_log_returns = (
                str(
                    q.select(
                        "Use log returns",
                        choices=_LOG_RETURN_CHOICES,
                        default="no",
                    ).ask()
                )
                == "yes"
            )
            if return_model == "ema_historical":
                while True:
                    raw_ema_span = str(
                        q.text(
                            "EMA smoothing span",
                            default=str(_DEFAULT_EMA_SPAN),
                            validate=_validate_ema_span,
                        ).ask()
                    )
                    validation_result = _validate_ema_span(raw_ema_span)
                    if validation_result is True:
                        ema_span = int(raw_ema_span)
                        break
                    self.show_error(str(validation_result))
            else:
                ema_span = _DEFAULT_EMA_SPAN
            risk_model = str(
                q.select(
                    "Risk model",
                    choices=risk_models,
                    default=_DEFAULT_RISK_MODEL,
                ).ask()
            )
        scatter_cmap = str(
            q.select(
                "Scatter colormap",
                choices=_SCATTER_CMAPS,
                default=_DEFAULT_SCATTER_CMAP,
            ).ask()
        )

        if objective == "max_quadratic_utility":
            risk_aversion = float(q.text("Risk aversion (δ)", default="1.0").ask())
        else:
            risk_aversion = 1.0
        risk_free_rate = float(q.text("Risk-free rate", default="0.03").ask())

        n_samples = int(q.text("Simulated portfolios", default="5000").ask())

        return PortfolioRequest(
            symbols=symbols,
            source=source,
            start=start,
            end=end,
            return_model=return_model,
            use_log_returns=use_log_returns,
            ema_span=ema_span,
            risk_model=risk_model,
            objective=objective,
            n_samples=n_samples,
            scatter_cmap=scatter_cmap,
            risk_free_rate=risk_free_rate,
            risk_aversion=risk_aversion,
        )

    def collect_next_action(self) -> PromptAction:
        """Ask whether to run another optimization or quit."""
        q = self._questionary or import_module("questionary")
        raw = str(
            q.select(
                "Next action",
                choices=[PromptAction.RECONFIGURE, PromptAction.QUIT],
                default=PromptAction.QUIT,
            ).ask()
        )
        return PromptAction(raw)

    def show_error(self, message: str) -> None:
        """Print a red error message."""
        self._console.print(f"[red]{message}[/red]")

    def show_info(self, message: str) -> None:
        """Print an informational message."""
        self._console.print(message)
