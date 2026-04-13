"""Tests for PriceHistoryLoader with an injected fake Quote factory."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from vietfrontier.models import PortfolioDataError
from vietfrontier.services.price_loader import PriceHistoryLoader


def _make_history(symbol: str, rows: int = 60) -> pd.DataFrame:
    """Return a fake vnstock history DataFrame for a symbol."""
    base = datetime(2024, 1, 1)
    return pd.DataFrame(
        {
            "time": [base + timedelta(days=i) for i in range(rows)],
            "open": [100.0 + i for i in range(rows)],
            "high": [101.0 + i for i in range(rows)],
            "low": [99.0 + i for i in range(rows)],
            "close": [100.0 + i + (0.5 if symbol == "BBB" else 0.0) for i in range(rows)],
            "volume": [1000 + i for i in range(rows)],
        }
    )


class _FakeQuote:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def history(self, **kwargs: object) -> pd.DataFrame:
        return _make_history(self.symbol)


def _factory(_source: str, symbol: str) -> _FakeQuote:
    return _FakeQuote(symbol)


def test_load_returns_wide_dataframe_with_close_columns() -> None:
    loader = PriceHistoryLoader(quote_factory=_factory)

    prices = loader.load(
        symbols=["AAA", "BBB"],
        source="VCI",
        start="2024-01-01",
        end="2024-03-01",
    )

    assert list(prices.columns) == ["AAA", "BBB"]
    assert len(prices) == 60
    assert prices.index.is_monotonic_increasing
    assert prices["AAA"].iloc[0] == pytest.approx(100.0)
    assert prices["BBB"].iloc[0] == pytest.approx(100.5)


def test_load_rejects_single_symbol() -> None:
    loader = PriceHistoryLoader(quote_factory=_factory)
    with pytest.raises(PortfolioDataError, match="at least 2 symbols"):
        loader.load(symbols=["AAA"], source="VCI", start="2024-01-01", end="2024-03-01")


def test_load_rejects_short_history() -> None:
    class _ShortQuote(_FakeQuote):
        def history(self, **kwargs: object) -> pd.DataFrame:
            return _make_history(self.symbol, rows=10)

    loader = PriceHistoryLoader(quote_factory=lambda _s, sym: _ShortQuote(sym))
    with pytest.raises(PortfolioDataError, match="at least 30"):
        loader.load(
            symbols=["AAA", "BBB"],
            source="VCI",
            start="2024-01-01",
            end="2024-01-15",
        )


def test_load_surfaces_provider_errors_as_portfolio_data_error() -> None:
    class _BrokenQuote:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, **kwargs: object) -> pd.DataFrame:
            raise RuntimeError("provider boom")

    loader = PriceHistoryLoader(quote_factory=lambda _s, sym: _BrokenQuote(sym))
    with pytest.raises(PortfolioDataError, match="provider boom"):
        loader.load(
            symbols=["AAA", "BBB"],
            source="VCI",
            start="2024-01-01",
            end="2024-03-01",
        )
