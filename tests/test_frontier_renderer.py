"""Tests for PlotextFrontierRenderer using a recording fake plotext module."""

from __future__ import annotations

from typing import Any

import pytest
from rich.console import Console

from vietfrontier.models import FrontierData, OptimizationResult
from vietfrontier.renderers.frontier_renderer import PlotextFrontierRenderer
from vietfrontier.ui.report import RichPortfolioReport


class _FakePlotext:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, name: str) -> Any:
        def _recorder(*args: object, **kwargs: object) -> int:
            self.calls.append((name, args, kwargs))
            return 120

        return _recorder


def test_frontier_renderer_emits_three_series_and_labels_axes() -> None:
    fake = _FakePlotext()
    renderer = PlotextFrontierRenderer(plotext_module=fake)
    data = FrontierData(
        frontier_vols=[0.1, 0.15, 0.2],
        frontier_rets=[0.05, 0.08, 0.12],
        mc_vols=[0.12, 0.18],
        mc_rets=[0.06, 0.09],
        optimal_vol=0.14,
        optimal_ret=0.11,
    )
    renderer.render(data, title="Test")

    names = [c[0] for c in fake.calls]
    assert "clear_figure" in names
    assert names.count("scatter") >= 2  # cloud + optimal marker
    assert "plot" in names  # frontier line
    assert "title" in names
    assert "xlabel" in names
    assert "ylabel" in names
    assert "show" in names

    cloud_call = next(
        call for call in fake.calls if call[0] == "scatter" and call[2].get("label") == "Random"
    )
    assert isinstance(cloud_call[2]["color"], list)
    assert len(cloud_call[2]["color"]) == len(data.mc_vols)
    assert all(isinstance(color, tuple) and len(color) == 3 for color in cloud_call[2]["color"])


def test_frontier_renderer_uses_requested_scatter_cmap() -> None:
    fake = _FakePlotext()
    renderer = PlotextFrontierRenderer(plotext_module=fake)
    data = FrontierData(
        mc_vols=[0.10, 0.15, 0.20],
        mc_rets=[0.05, 0.07, 0.09],
        optimal_vol=0.14,
        optimal_ret=0.11,
    )

    renderer.render(data, title="Test", scatter_cmap="viridis")

    cloud_call = next(
        call for call in fake.calls if call[0] == "scatter" and call[2].get("label") == "Random"
    )
    assert cloud_call[2]["color"][0] != cloud_call[2]["color"][-1]


def test_weights_renderer_emits_horizontal_bar() -> None:
    fake = _FakePlotext()
    renderer = PlotextFrontierRenderer(plotext_module=fake)
    renderer.render_weights({"AAA": 0.4, "BBB": 0.35, "CCC": 0.25}, title="HRP Test")

    names = [c[0] for c in fake.calls]
    assert "clear_figure" in names
    assert "bar" in names
    bar_call = next(c for c in fake.calls if c[0] == "bar")
    assert bar_call[2].get("orientation") == "h"
    assert bar_call[1][0] == ["AAA", "BBB", "CCC"]
    assert abs(sum(bar_call[1][1]) - 100.0) < 1e-9
    assert "title" in names
    assert "xlabel" in names
    assert "show" in names


def test_weights_renderer_sorts_descending() -> None:
    fake = _FakePlotext()
    renderer = PlotextFrontierRenderer(plotext_module=fake)
    renderer.render_weights({"Z": 0.1, "A": 0.6, "M": 0.3}, title="Sort Test")

    bar_call = next(c for c in fake.calls if c[0] == "bar")
    assert bar_call[1][0] == ["A", "M", "Z"]
    assert bar_call[1][1] == pytest.approx([60.0, 30.0, 10.0])


def test_weights_renderer_uses_compact_plot_height() -> None:
    fake = _FakePlotext()
    renderer = PlotextFrontierRenderer(plotext_module=fake)

    renderer.render_weights({"AAA": 0.4, "BBB": 0.35, "CCC": 0.25}, title="Compact Test")

    plotsize_call = next(c for c in fake.calls if c[0] == "plotsize")
    assert plotsize_call[1][1] == 8


def test_rich_portfolio_report_prints_tables() -> None:
    console = Console(record=True, width=100)
    report = RichPortfolioReport(console=console)
    result = OptimizationResult(
        weights={"AAA": 0.4, "BBB": 0.6},
        expected_return=0.12,
        volatility=0.18,
        sharpe=0.55,
        method_name="max_sharpe",
    )
    report.print_result(result)
    out = console.export_text()
    assert "AAA" in out
    assert "BBB" in out
    assert "max_sharpe" in out
    assert "Sharpe" in out
