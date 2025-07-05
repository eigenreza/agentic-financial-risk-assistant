"""Drawdown series and maximum drawdown calculations."""

import pandas as pd


def wealth_index(prices: pd.Series) -> pd.Series:
    """Normalised cumulative wealth starting at 1.0."""
    return prices / prices.iloc[0]


def running_maximum(prices: pd.Series) -> pd.Series:
    """Cumulative maximum of the wealth index up to each point."""
    return wealth_index(prices).cummax()


def drawdown_series(prices: pd.Series) -> pd.Series:
    """
    Drawdown at each point: (current_wealth - peak_wealth) / peak_wealth.
    Values are <= 0.
    """
    wi = wealth_index(prices)
    peak = wi.cummax()
    return (wi - peak) / peak


def max_drawdown(prices: pd.Series) -> float:
    """Maximum (most negative) drawdown value over the full series."""
    return float(drawdown_series(prices).min())


def max_drawdown_date(prices: pd.Series) -> pd.Timestamp:
    """Date at which the maximum drawdown trough occurred."""
    dd = drawdown_series(prices)
    return dd.idxmin()
