"""Rich-based portfolio report tables."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from vietfrontier.models import OptimizationResult


class RichPortfolioReport:
    """Print portfolio weights and performance as rich tables."""

    def __init__(self, console: Console) -> None:
        """Initialize the report with a shared rich Console."""
        self._console = console

    def print_result(self, result: OptimizationResult) -> None:
        """Render two tables: weights per ticker and aggregate performance."""
        weights_table = Table(title=f"Portfolio Weights ({result.method_name})")
        weights_table.add_column("Ticker", style="bold cyan")
        weights_table.add_column("Weight", justify="right")
        weights_table.add_column("Allocation", justify="right")
        for ticker, weight in sorted(
            result.weights.items(), key=lambda item: item[1], reverse=True
        ):
            weights_table.add_row(
                ticker, f"{weight:.4f}", f"{weight * 100:.2f}%"
            )

        perf_table = Table(title="Performance")
        perf_table.add_column("Metric", style="bold")
        perf_table.add_column("Value", justify="right")
        perf_table.add_row("Expected Return", f"{result.expected_return * 100:.2f}%")
        perf_table.add_row("Volatility", f"{result.volatility * 100:.2f}%")
        perf_table.add_row("Sharpe", f"{result.sharpe:.3f}")
        perf_table.add_row("Method", result.method_name)

        self._console.print(weights_table)
        self._console.print(perf_table)
