"""Simple, log, and cumulative return calculations."""

import numpy as np
import pandas as pd


def simple_returns(prices: pd.Series) -> pd.Series:
    """Percentage price change: (P_t - P_{t-1}) / P_{t-1}."""
    return prices.pct_change().dropna()


def log_returns(prices: pd.Series) -> pd.Series:
    """Continuously compounded log return: ln(P_t / P_{t-1})."""
    return np.log(prices / prices.shift(1)).dropna()


def cumulative_returns(prices: pd.Series) -> pd.Series:
    """Cumulative simple return rebased from the first observed price."""
    r = simple_returns(prices)
    return (1 + r).cumprod() - 1
