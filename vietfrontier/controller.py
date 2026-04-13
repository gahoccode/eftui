"""Main controller coordinating prompts, data loading, optimization, and rendering."""

from __future__ import annotations

from vietfrontier.models import (
    OptimizationError,
    OptimizationResult,
    PortfolioDataError,
    PortfolioRequest,
    PromptAction,
)


class AppController:
    """Drive the prompt → load → optimize → render → next-action loop."""

    def __init__(
        self,
        *,
        prompt_session: object,
        price_loader: object,
        optimizer: object,
        frontier_renderer: object,
        report: object,
    ) -> None:
        """Initialize the controller with all injected collaborators."""
        self._prompts = prompt_session
        self._loader = price_loader
        self._optimizer = optimizer
        self._renderer = frontier_renderer
        self._report = report

    def run(self) -> None:
        """Run the interactive loop until the user chooses to quit."""
        try:
            request = self._prompts.collect_request()
        except ModuleNotFoundError as exc:
            self._show_missing_dependency(exc)
            return

        while True:
            try:
                prices = self._loader.load(
                    symbols=list(request.symbols),
                    source=request.source,
                    start=request.start,
                    end=request.end,
                )
                result = self._optimizer.optimize(prices, request)
                title = self._build_title(request, result)
                if request.objective == "hrp":
                    self._renderer.render_weights(result.weights, title=title)
                else:
                    frontier = self._optimizer.build_frontier_data(prices, request, result)
                    self._renderer.render(
                        frontier,
                        title=title,
                        scatter_cmap=request.scatter_cmap,
                    )
                self._report.print_result(result)
            except (PortfolioDataError, OptimizationError) as exc:
                self._prompts.show_error(f"{type(exc).__name__}: {exc}")
                request = self._try_reprompt()
                if request is None:
                    return
                continue
            except ModuleNotFoundError as exc:
                self._show_missing_dependency(exc)
                return

            try:
                action = self._prompts.collect_next_action()
            except ModuleNotFoundError as exc:
                self._show_missing_dependency(exc)
                return
            if action is PromptAction.QUIT:
                return
            request = self._prompts.collect_request()

    def _try_reprompt(self) -> PortfolioRequest | None:
        """Re-prompt for configuration after a recoverable error."""
        try:
            return self._prompts.collect_request()
        except ModuleNotFoundError as exc:
            self._show_missing_dependency(exc)
            return None
        except StopIteration:
            return None

    @staticmethod
    def _build_title(request: PortfolioRequest, result: OptimizationResult) -> str:
        """Build a one-line chart title summarizing the run."""
        tickers = ",".join(request.symbols)
        title_parts = [tickers, result.method_name]
        if request.objective != "hrp":
            return_label = request.return_model
            if request.return_model == "ema_historical":
                return_label = f"{return_label}(span={request.ema_span})"
            title_parts[1:1] = [
                return_label,
                f"log={'on' if request.use_log_returns else 'off'}",
                request.risk_model,
            ]
        metrics = (
            f"ret={result.expected_return * 100:.1f}% "
            f"vol={result.volatility * 100:.1f}% "
            f"sharpe={result.sharpe:.2f}"
        )
        return " | ".join([*title_parts, metrics])

    def _show_missing_dependency(self, exc: ModuleNotFoundError) -> None:
        """Surface a consistent message when a runtime dependency is absent."""
        name = exc.name or str(exc)
        self._prompts.show_error(
            f"Missing runtime dependency: {name}. Run `uv sync` and retry."
        )
