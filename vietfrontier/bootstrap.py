"""Application bootstrap wiring all DI dependencies together."""

from __future__ import annotations

from rich.console import Console

from vietfrontier.controller import AppController
from vietfrontier.renderers.frontier_renderer import PlotextFrontierRenderer
from vietfrontier.services.optimizer import PortfolioOptimizer
from vietfrontier.services.price_loader import PriceHistoryLoader
from vietfrontier.ui.prompts import PromptSession
from vietfrontier.ui.report import RichPortfolioReport


def build_application() -> AppController:
    """Build a fully wired AppController for the VietFrontier TUI."""
    console = Console()
    return AppController(
        prompt_session=PromptSession(console=console),
        price_loader=PriceHistoryLoader(),
        optimizer=PortfolioOptimizer(),
        frontier_renderer=PlotextFrontierRenderer(),
        report=RichPortfolioReport(console=console),
    )
