"""Rolling risk metrics and stress-period detection."""

import numpy as np
import pandas as pd
from src.risk.returns import simple_returns, log_returns
from src.risk.volatility import TRADING_DAYS


def rolling_mean_return(prices: pd.Series, window: int = 21) -> pd.Series:
    """Rolling mean of simple returns, annualised."""
    r = simple_returns(prices)
    return r.rolling(window).mean() * TRADING_DAYS


def rolling_volatility(prices: pd.Series, window: int = 21) -> pd.Series:
    """Rolling annualised volatility of log returns."""
    lr = log_returns(prices)
    return lr.rolling(window).std() * np.sqrt(TRADING_DAYS)


def rolling_var(prices: pd.Series, window: int = 63, confidence: float = 0.95) -> pd.Series:
    """
    Rolling historical VaR using a lookback window of simple returns.
    Returns a positive number (loss threshold) at each date.
    """
    r = simple_returns(prices)

    def _var(x: np.ndarray) -> float:
        return float(-np.percentile(x, (1 - confidence) * 100))

    return r.rolling(window).apply(_var, raw=True)


def stress_period_flag(
    prices: pd.Series, window: int = 21, threshold_multiplier: float = 1.5
) -> pd.Series:
    """
    Boolean series: True where rolling volatility exceeds threshold_multiplier
    times the full-period mean rolling volatility.
    """
    rv = rolling_volatility(prices, window).dropna()
    avg = rv.mean()
    flag = rv > (avg * threshold_multiplier)
    return flag.reindex(prices.index, fill_value=False)
