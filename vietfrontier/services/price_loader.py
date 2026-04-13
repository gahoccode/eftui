"""Load daily close-price histories for multiple tickers via vnstock."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from importlib import import_module
from io import StringIO

import pandas as pd

from vietfrontier.models import PortfolioDataError

_MIN_ROWS = 30
_REQUIRED_COLUMNS = {"time", "close"}


class PriceHistoryLoader:
    """Fetch and align close-price series for a basket of symbols."""

    def __init__(
        self,
        quote_factory: Callable[[str, str], object] | None = None,
    ) -> None:
        """Initialize the loader with an injectable vnstock Quote factory."""
        self._quote_factory = quote_factory or self._build_quote
        self._quote_class: object | None = None

    def load(
        self,
        *,
        symbols: list[str],
        source: str,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Return a wide-format DataFrame of daily closes indexed by date."""
        if len(symbols) < 2:
            raise PortfolioDataError(
                "Need at least 2 symbols to run portfolio optimization."
            )

        with self._suppress_provider_output():
            with ThreadPoolExecutor(max_workers=min(len(symbols), 8)) as pool:
                series = list(
                    pool.map(
                        lambda sym: self._fetch_one(
                            symbol=sym, source=source, start=start, end=end
                        ),
                        symbols,
                    )
                )

        prices = pd.concat(series, axis=1).dropna()
        if len(prices) < _MIN_ROWS:
            raise PortfolioDataError(
                f"Need at least {_MIN_ROWS} aligned trading days; got {len(prices)}."
            )
        return prices

    def _fetch_one(
        self,
        *,
        symbol: str,
        source: str,
        start: str,
        end: str,
    ) -> pd.Series:
        """Fetch one symbol's close series and return it named by the ticker."""
        try:
            client = self._quote_factory(source, symbol)
            dataframe = client.history(
                symbol=symbol,
                start=start,
                end=end,
                interval="1D",
            )
        except ModuleNotFoundError:
            raise
        except Exception as exc:
            raise PortfolioDataError(f"{symbol}: {exc}") from exc

        if not _REQUIRED_COLUMNS.issubset(dataframe.columns):
            raise PortfolioDataError(
                f"{symbol}: provider response is missing 'time'/'close' columns."
            )

        frame = dataframe.loc[:, ["time", "close"]].copy()
        frame["time"] = pd.to_datetime(frame["time"])
        frame = frame.sort_values("time").drop_duplicates("time")
        series = pd.Series(
            frame["close"].astype(float).values,
            index=pd.DatetimeIndex(frame["time"].values, name="date"),
            name=symbol,
        )
        if series.empty:
            raise PortfolioDataError(f"{symbol}: provider returned no rows.")
        return series

    def _build_quote(self, source: str, symbol: str) -> object:
        """Instantiate the vnstock Quote client, caching the class after first import."""
        if self._quote_class is None:
            self._quote_class = import_module("vnstock").Quote
        return self._quote_class(source=source, symbol=symbol, show_log=False)

    @staticmethod
    @contextmanager
    def _suppress_provider_output():
        """Silence vnstock startup banners and notices (process-level stdio redirect)."""
        sink = StringIO()
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(sink))
            stack.enter_context(redirect_stderr(sink))
            yield
