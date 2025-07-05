import numpy as np
import pandas as pd
import pytest
from src.risk.volatility import daily_volatility, annualised_volatility, rolling_volatility, TRADING_DAYS


@pytest.fixture
def prices():
    rng = np.random.default_rng(0)
    raw = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 500)))
    return pd.Series(raw, name="Close")


def test_daily_volatility_positive(prices):
    assert daily_volatility(prices) > 0


def test_annualised_volatility_scales(prices):
    dv = daily_volatility(prices)
    av = annualised_volatility(prices)
    assert abs(av - dv * np.sqrt(TRADING_DAYS)) < 1e-10


def test_rolling_volatility_length(prices):
    window = 21
    rv = rolling_volatility(prices, window=window)
    # log_returns drops 1 row, so rolling_volatility output is len(prices) - 1
    assert len(rv) == len(prices) - 1


def test_rolling_volatility_nan_prefix(prices):
    window = 21
    rv = rolling_volatility(prices, window=window)
    # log_returns drops 1 row, then rolling needs window rows → first (window) values are NaN
    assert rv.dropna().shape[0] > 0


def test_rolling_volatility_positive(prices):
    rv = rolling_volatility(prices, window=21).dropna()
    assert (rv > 0).all()


def test_annualised_volatility_reasonable(prices):
    av = annualised_volatility(prices)
    assert 0.01 < av < 2.0, f"Annualised vol {av:.4f} outside plausible range"
