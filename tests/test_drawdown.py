import numpy as np
import pandas as pd
import pytest
from src.risk.drawdown import wealth_index, drawdown_series, max_drawdown, max_drawdown_date


@pytest.fixture
def rising_prices():
    return pd.Series([100.0, 110.0, 120.0, 130.0], name="Close")


@pytest.fixture
def crash_prices():
    # rises to 200, crashes back to 100
    return pd.Series([100.0, 150.0, 200.0, 100.0], name="Close")


def test_wealth_index_starts_at_one(rising_prices):
    wi = wealth_index(rising_prices)
    assert abs(wi.iloc[0] - 1.0) < 1e-10


def test_drawdown_series_non_positive(rising_prices):
    dd = drawdown_series(rising_prices)
    assert (dd <= 0).all()


def test_drawdown_zero_for_rising_prices(rising_prices):
    dd = drawdown_series(rising_prices)
    assert (dd == 0).all()


def test_max_drawdown_negative(crash_prices):
    mdd = max_drawdown(crash_prices)
    assert mdd < 0


def test_max_drawdown_known_value(crash_prices):
    # peak is 200, trough is 100 → drawdown = (100 - 200) / 200 = -0.5
    mdd = max_drawdown(crash_prices)
    assert abs(mdd - (-0.5)) < 1e-10


def test_max_drawdown_date_type(crash_prices):
    prices_with_index = crash_prices.copy()
    prices_with_index.index = pd.date_range("2020-01-01", periods=4, freq="D")
    date = max_drawdown_date(prices_with_index)
    assert isinstance(date, pd.Timestamp)


def test_max_drawdown_range(crash_prices):
    mdd = max_drawdown(crash_prices)
    assert -1.0 <= mdd <= 0.0
