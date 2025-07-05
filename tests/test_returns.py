import numpy as np
import pandas as pd
import pytest
from src.risk.returns import simple_returns, log_returns, cumulative_returns


@pytest.fixture
def flat_prices():
    return pd.Series([100.0, 110.0, 121.0, 133.1], name="Close")


@pytest.fixture
def known_prices():
    return pd.Series([100.0, 200.0], name="Close")


def test_simple_returns_length(flat_prices):
    r = simple_returns(flat_prices)
    assert len(r) == len(flat_prices) - 1


def test_simple_returns_known(known_prices):
    r = simple_returns(known_prices)
    assert abs(r.iloc[0] - 1.0) < 1e-10


def test_log_returns_length(flat_prices):
    lr = log_returns(flat_prices)
    assert len(lr) == len(flat_prices) - 1


def test_log_returns_known(known_prices):
    lr = log_returns(known_prices)
    assert abs(lr.iloc[0] - np.log(2)) < 1e-10


def test_cumulative_returns_monotone(flat_prices):
    cr = cumulative_returns(flat_prices)
    assert (cr.diff().dropna() >= 0).all(), "Cumulative returns should be non-decreasing for rising prices"


def test_cumulative_returns_final(flat_prices):
    cr = cumulative_returns(flat_prices)
    expected = flat_prices.iloc[-1] / flat_prices.iloc[0] - 1
    assert abs(cr.iloc[-1] - expected) < 1e-10


def test_simple_returns_no_nan(flat_prices):
    r = simple_returns(flat_prices)
    assert not r.isna().any()


def test_log_returns_no_nan(flat_prices):
    lr = log_returns(flat_prices)
    assert not lr.isna().any()
