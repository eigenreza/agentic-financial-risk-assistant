"""Daily and annualised volatility calculations."""

import numpy as np
import pandas as pd
from src.risk.returns import log_returns

TRADING_DAYS = 252


def daily_volatility(prices: pd.Series) -> float:
    """Standard deviation of log returns."""
    return float(log_returns(prices).std())


def annualised_volatility(prices: pd.Series) -> float:
    """Daily volatility scaled to annual: sigma_daily * sqrt(252)."""
    return daily_volatility(prices) * np.sqrt(TRADING_DAYS)


def rolling_volatility(prices: pd.Series, window: int = 21) -> pd.Series:
    """Rolling annualised volatility of log returns over the given window."""
    lr = log_returns(prices)
    return lr.rolling(window).std() * np.sqrt(TRADING_DAYS)
