"""Tests for PromptSession using a fake questionary module."""

from __future__ import annotations

from collections.abc import Iterator

from rich.console import Console

from vietfrontier.models import PortfolioRequest, PromptAction
from vietfrontier.ui.prompts import PromptSession, _validate_ema_span


class _FakeAnswer:
    def __init__(self, value: str) -> None:
        self._value = value

    def ask(self) -> str:
        return self._value


class _FakeQuestionary:
    def __init__(self, answers: list[str]) -> None:
        self._iter: Iterator[str] = iter(answers)
        self.text_calls: list[dict[str, object]] = []
        self.select_calls: list[dict[str, object]] = []

    def text(self, message: str, **kwargs: object) -> _FakeAnswer:
        self.text_calls.append({"message": message, **kwargs})
        return _FakeAnswer(next(self._iter))

    def select(self, message: str, **kwargs: object) -> _FakeAnswer:
        self.select_calls.append({"message": message, **kwargs})
        return _FakeAnswer(next(self._iter))


def test_collect_request_max_sharpe_flow() -> None:
    answers = [
        "ACB,VCB,FPT",  # symbols
        "VCI",  # source
        "2023-01-01",  # start
        "2024-12-31",  # end
        "max_sharpe",  # objective
        "mean_historical",  # return model
        "no",  # use log returns
        "ledoit_wolf",  # risk model
        "copper",  # scatter cmap
        "0.03",  # risk-free rate
        "2500",  # n_samples
    ]
    fake_questionary = _FakeQuestionary(answers)
    session = PromptSession(console=Console(), questionary_module=fake_questionary)
    request = session.collect_request()

    assert isinstance(request, PortfolioRequest)
    assert request.symbols == ("ACB", "VCB", "FPT")
    assert request.source == "VCI"
    assert request.return_model == "mean_historical"
    assert request.use_log_returns is False
    assert request.ema_span == 500
    assert request.risk_model == "ledoit_wolf"
    assert request.objective == "max_sharpe"
    assert request.scatter_cmap == "copper"
    assert request.risk_free_rate == 0.03
    assert request.n_samples == 2500

    cmap_select = next(
        call for call in fake_questionary.select_calls if call["message"] == "Scatter colormap"
    )
    assert cmap_select["default"] == "copper"
    assert cmap_select["choices"] == [
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


def test_collect_request_quadratic_utility_collects_extra_params() -> None:
    answers = [
        "AAA,BBB",
        "VCI",
        "2023-01-01",
        "2024-12-31",
        "max_quadratic_utility",
        "ema_historical",
        "yes",
        "180",
        "sample_cov",
        "viridis",
        "2.5",  # risk aversion
        "0.02",  # risk-free
        "1000",
    ]
    session = PromptSession(
        console=Console(), questionary_module=_FakeQuestionary(answers)
    )
    request = session.collect_request()

    assert request.objective == "max_quadratic_utility"
    assert request.return_model == "ema_historical"
    assert request.use_log_returns is True
    assert request.ema_span == 180
    assert request.scatter_cmap == "viridis"
    assert request.risk_aversion == 2.5
    assert request.risk_free_rate == 0.02
    assert request.n_samples == 1000


def test_collect_request_hrp_skips_risk_model_prompt() -> None:
    answers = [
        "AAA,BBB",
        "VCI",
        "2023-01-01",
        "2024-12-31",
        "hrp",
        "magma",
        "0.02",
        "1000",
    ]
    fake_questionary = _FakeQuestionary(answers)
    session = PromptSession(console=Console(), questionary_module=fake_questionary)

    request = session.collect_request()

    assert request.objective == "hrp"
    assert request.return_model == "mean_historical"
    assert request.use_log_returns is False
    assert request.ema_span == 500
    assert request.risk_model == "ledoit_wolf"
    assert [call["message"] for call in fake_questionary.select_calls].count("Return method") == 0
    assert [call["message"] for call in fake_questionary.select_calls].count("Use log returns") == 0
    assert (
        [call["message"] for call in fake_questionary.select_calls].count(
            "EMA smoothing span"
        )
        == 0
    )
    assert [call["message"] for call in fake_questionary.select_calls].count("Risk model") == 0


def test_collect_request_mean_historical_skips_ema_span_prompt() -> None:
    answers = [
        "AAA,BBB",
        "VCI",
        "2023-01-01",
        "2024-12-31",
        "max_sharpe",
        "mean_historical",
        "no",
        "sample_cov",
        "copper",
        "0.03",
        "1000",
    ]
    fake_questionary = _FakeQuestionary(answers)
    session = PromptSession(console=Console(), questionary_module=fake_questionary)

    request = session.collect_request()

    assert request.return_model == "mean_historical"
    assert request.ema_span == 500
    assert (
        [call["message"] for call in fake_questionary.select_calls].count(
            "EMA smoothing span"
        )
        == 0
    )


def test_collect_request_ema_span_reprompts_for_invalid_input() -> None:
    answers = [
        "AAA,BBB",
        "VCI",
        "2023-01-01",
        "2024-12-31",
        "max_sharpe",
        "ema_historical",
        "no",
        "abc",
        "1",
        "120",
        "sample_cov",
        "copper",
        "0.03",
        "1000",
    ]
    console = Console(record=True, width=100)
    fake_questionary = _FakeQuestionary(answers)
    session = PromptSession(console=console, questionary_module=fake_questionary)

    request = session.collect_request()

    assert request.ema_span == 120
    assert [call["message"] for call in fake_questionary.text_calls].count(
        "EMA smoothing span"
    ) == 3
    out = console.export_text()
    assert "integer" in out
    assert ">= 2" in out


def test_validate_ema_span_rejects_non_numeric_and_too_small_values() -> None:
    assert _validate_ema_span("abc") == "EMA smoothing span must be an integer."
    assert _validate_ema_span("1") == "EMA smoothing span must be an integer >= 2."
    assert _validate_ema_span("2") is True


def test_collect_next_action_returns_enum() -> None:
    session = PromptSession(
        console=Console(), questionary_module=_FakeQuestionary(["quit"])
    )
    assert session.collect_next_action() is PromptAction.QUIT
