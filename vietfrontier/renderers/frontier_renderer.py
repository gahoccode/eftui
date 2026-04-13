"""Render efficient frontier charts and weight bar charts in the terminal via plotext."""

from __future__ import annotations

from importlib import import_module
from typing import cast

from vietfrontier.models import FrontierData


class PlotextFrontierRenderer:
    """Draw the efficient frontier chart directly into the terminal via plotext."""

    def __init__(self, plotext_module: object | None = None) -> None:
        """Initialize the renderer with an injectable plotext module."""
        self._plt = plotext_module

    def render(self, data: FrontierData, title: str, scatter_cmap: str = "copper") -> None:
        """Render the random-portfolio cloud, frontier curve, and optimal marker."""
        plt = self._plt or import_module("plotext")

        plt.clear_figure()
        plt.theme("dark")

        if data.mc_vols:
            plt.scatter(
                list(data.mc_vols),
                list(data.mc_rets),
                marker="braille",
                color=self._scatter_colors(data, scatter_cmap),
                label="Random",
            )
        if data.frontier_vols:
            plt.plot(
                list(data.frontier_vols),
                list(data.frontier_rets),
                marker="hd",
                color="white",
                label="Frontier",
            )
        plt.scatter(
            [data.optimal_vol],
            [data.optimal_ret],
            marker="*",
            color="red",
            label="Optimal",
        )

        plt.title(title)
        plt.xlabel("Volatility (σ)")
        plt.ylabel("Expected Return")

        width = max(int(plt.tw()) - 4, 60)
        height = max(int(plt.th()) - 18, 18)
        plt.plotsize(width, height)
        plt.show()

    def render_weights(self, weights: dict[str, float], title: str) -> None:
        """Render portfolio weights as a horizontal bar chart in the terminal."""
        plt = self._plt or import_module("plotext")

        sorted_items = sorted(weights.items(), key=lambda item: item[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] * 100 for item in sorted_items]

        plt.clear_figure()
        plt.theme("dark")
        plt.bar(labels, values, orientation="h", width=3 / 5)
        plt.title(title)
        plt.xlabel("Weight (%)")

        width = max(int(plt.tw()) - 4, 60)
        available_height = int(plt.th()) - 18
        compact_height = len(labels) + 5
        height = max(8, min(available_height, compact_height))
        plt.plotsize(width, height)
        plt.show()

    @staticmethod
    def _scatter_colors(data: FrontierData, scatter_cmap: str) -> list[tuple[int, int, int]]:
        """Sample one terminal RGB color per Monte Carlo point from a Matplotlib colormap."""
        colormaps = import_module("matplotlib").colormaps
        cmap = colormaps[scatter_cmap]
        point_count = len(data.mc_vols)
        if point_count == 1:
            samples = [0.5]
        else:
            samples = [index / (point_count - 1) for index in range(point_count)]
        return [PlotextFrontierRenderer._to_plotext_rgb(cmap(sample)) for sample in samples]

    @staticmethod
    def _to_plotext_rgb(color: object) -> tuple[int, int, int]:
        """Convert a Matplotlib RGBA color to a plotext RGB tuple."""
        red, green, blue, _alpha = cast(tuple[float, float, float, float], color)
        return (int(red * 255), int(green * 255), int(blue * 255))
