"""Integration-style tests for AppController using fakes for all collaborators."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd

from vietfrontier.controller import AppController
from vietfrontier.models import (
    FrontierData,
    OptimizationResult,
    PortfolioDataError,
    PortfolioRequest,
    PromptAction,
)


def _request() -> PortfolioRequest:
    return PortfolioRequest(
        symbols=("AAA", "BBB"),
        source="VCI",
        start="2023-01-01",
        end="2023-12-31",
        return_model="mean_historical",
        use_log_returns=False,
        ema_span=500,
        risk_model="sample_cov",
        objective="max_sharpe",
        n_samples=100,
        scatter_cmap="copper",
    )


class _FakePrompt:
    def __init__(
        self,
        requests: list[PortfolioRequest],
        actions: list[PromptAction],
    ) -> None:
        self._requests: Iterator[PortfolioRequest] = iter(requests)
        self._actions: Iterator[PromptAction] = iter(actions)
        self.errors: list[str] = []
        self.infos: list[str] = []

    def collect_request(self) -> PortfolioRequest:
        return next(self._requests)

    def collect_next_action(self) -> PromptAction:
        return next(self._actions)

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_info(self, message: str) -> None:
        self.infos.append(message)


class _FakeLoader:
    def __init__(self, prices: pd.DataFrame, error: Exception | None = None) -> None:
        self._prices = prices
        self._error = error
        self.calls = 0

    def load(self, **_kwargs: object) -> pd.DataFrame:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._prices


class _FakeOptimizer:
    def __init__(self, result: OptimizationResult, data: FrontierData) -> None:
        self._result = result
        self._data = data
        self.optimize_calls = 0

    def optimize(self, _prices: pd.DataFrame, _request: PortfolioRequest) -> OptimizationResult:
        self.optimize_calls += 1
        return self._result

    def build_frontier_data(
        self,
        _prices: pd.DataFrame,
        _request: PortfolioRequest,
        _result: OptimizationResult,
    ) -> FrontierData:
        return self._data


class _FakeRenderer:
    def __init__(self) -> None:
        self.renders: list[tuple[FrontierData, str, str]] = []
        self.weight_renders: list[tuple[dict[str, float], str]] = []

    def render(self, data: FrontierData, title: str, scatter_cmap: str) -> None:
        self.renders.append((data, title, scatter_cmap))

    def render_weights(self, weights: dict[str, float], title: str) -> None:
        self.weight_renders.append((weights, title))


class _FakeReport:
    def __init__(self) -> None:
        self.results: list[OptimizationResult] = []

    def print_result(self, result: OptimizationResult) -> None:
        self.results.append(result)


def _result() -> OptimizationResult:
    return OptimizationResult(
        weights={"AAA": 0.6, "BBB": 0.4},
        expected_return=0.12,
        volatility=0.15,
        sharpe=0.7,
        method_name="max_sharpe",
    )


def _frontier() -> FrontierData:
    return FrontierData(
        frontier_vols=[0.1, 0.2],
        frontier_rets=[0.05, 0.12],
        mc_vols=[0.15],
        mc_rets=[0.08],
        optimal_vol=0.15,
        optimal_ret=0.12,
    )


def test_controller_runs_once_then_quits() -> None:
    prices = pd.DataFrame({"AAA": [1, 2, 3], "BBB": [1.1, 2.1, 3.1]})
    loader = _FakeLoader(prices)
    optimizer = _FakeOptimizer(_result(), _frontier())
    renderer = _FakeRenderer()
    report = _FakeReport()
    prompt = _FakePrompt([_request()], [PromptAction.QUIT])

    controller = AppController(
        prompt_session=prompt,
        price_loader=loader,
        optimizer=optimizer,
        frontier_renderer=renderer,
        report=report,
    )
    controller.run()

    assert loader.calls == 1
    assert optimizer.optimize_calls == 1
    assert len(renderer.renders) == 1
    assert renderer.renders[0][2] == "copper"
    assert renderer.renders[0][1].startswith(
        "AAA,BBB | mean_historical | log=off | sample_cov | max_sharpe |"
    )
    assert len(report.results) == 1


def test_controller_shows_error_on_data_failure_and_reconfigures() -> None:
    prices = pd.DataFrame({"AAA": [1, 2, 3], "BBB": [1.1, 2.1, 3.1]})

    class _FlakyLoader:
        def __init__(self) -> None:
            self.calls = 0

        def load(self, **_kwargs: object) -> pd.DataFrame:
            self.calls += 1
            if self.calls == 1:
                raise PortfolioDataError("boom")
            return prices

    loader = _FlakyLoader()
    optimizer = _FakeOptimizer(_result(), _frontier())
    renderer = _FakeRenderer()
    report = _FakeReport()
    prompt = _FakePrompt(
        [_request(), _request()],
        [PromptAction.QUIT],
    )

    controller = AppController(
        prompt_session=prompt,
        price_loader=loader,
        optimizer=optimizer,
        frontier_renderer=renderer,
        report=report,
    )
    controller.run()

    assert any("boom" in err for err in prompt.errors)
    assert any("PortfolioDataError" in err for err in prompt.errors)
    assert loader.calls == 2
    assert len(renderer.renders) == 1


def test_controller_renders_weights_for_hrp_objective() -> None:
    prices = pd.DataFrame({"AAA": [1, 2, 3], "BBB": [1.1, 2.1, 3.1]})
    hrp_result = OptimizationResult(
        weights={"AAA": 0.55, "BBB": 0.45},
        expected_return=0.10,
        volatility=0.14,
        sharpe=0.5,
        method_name="hrp",
    )
    hrp_request = PortfolioRequest(
        symbols=("AAA", "BBB"),
        source="VCI",
        start="2023-01-01",
        end="2023-12-31",
        return_model="mean_historical",
        use_log_returns=False,
        ema_span=500,
        risk_model="sample_cov",
        objective="hrp",
        n_samples=100,
        scatter_cmap="copper",
    )
    loader = _FakeLoader(prices)
    optimizer = _FakeOptimizer(hrp_result, _frontier())
    renderer = _FakeRenderer()
    report = _FakeReport()
    prompt = _FakePrompt([hrp_request], [PromptAction.QUIT])

    controller = AppController(
        prompt_session=prompt,
        price_loader=loader,
        optimizer=optimizer,
        frontier_renderer=renderer,
        report=report,
    )
    controller.run()

    assert len(renderer.weight_renders) == 1
    assert renderer.weight_renders[0][0] == {"AAA": 0.55, "BBB": 0.45}
    assert "sample_cov" not in renderer.weight_renders[0][1]
    assert renderer.weight_renders[0][1].startswith("AAA,BBB | hrp |")
    assert len(renderer.renders) == 0
