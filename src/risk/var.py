"""Value-at-Risk and Expected Shortfall calculations."""

import numpy as np
import pandas as pd
from scipy import stats
from src.risk.returns import simple_returns


def historical_var(prices: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical simulation VaR at the given confidence level.
    Returns a positive number: the loss not exceeded with `confidence` probability.
    E.g. 0.03 means a daily loss of 3% is not exceeded 95% of the time.
    """
    r = simple_returns(prices)
    return float(-np.percentile(r, (1 - confidence) * 100))


def parametric_var(prices: pd.Series, confidence: float = 0.95) -> float:
    """
    Gaussian parametric VaR: -(mu - z * sigma), positive number.
    Assumes returns are normally distributed.
    """
    r = simple_returns(prices)
    mu = r.mean()
    sigma = r.std()
    z = stats.norm.ppf(confidence)
    return float(-(mu - z * sigma))


def expected_shortfall(prices: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical Expected Shortfall (CVaR): mean loss in the tail beyond VaR.
    Returns a positive number.
    """
    r = simple_returns(prices)
    cutoff = np.percentile(r, (1 - confidence) * 100)
    tail = r[r <= cutoff]
    if tail.empty:
        return float(historical_var(prices, confidence))
    return float(-tail.mean())
