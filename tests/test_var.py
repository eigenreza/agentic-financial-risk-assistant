import numpy as np
import pandas as pd
import pytest
from src.risk.var import historical_var, parametric_var, expected_shortfall


@pytest.fixture
def prices():
    rng = np.random.default_rng(42)
    raw = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 1000)))
    return pd.Series(raw, name="Close")


def test_historical_var_positive(prices):
    assert historical_var(prices) > 0


def test_parametric_var_positive(prices):
    assert parametric_var(prices) > 0


def test_expected_shortfall_positive(prices):
    assert expected_shortfall(prices) > 0


def test_es_exceeds_var(prices):
    # ES (CVaR) should always be >= VaR by definition
    var = historical_var(prices)
    es = expected_shortfall(prices)
    assert es >= var - 1e-10


def test_var_increases_with_confidence(prices):
    var_90 = historical_var(prices, confidence=0.90)
    var_99 = historical_var(prices, confidence=0.99)
    assert var_99 > var_90


def test_parametric_var_reasonable(prices):
    pv = parametric_var(prices)
    assert 0.001 < pv < 0.5, f"Parametric VaR {pv:.4f} outside plausible range"


def test_historical_var_reasonable(prices):
    hv = historical_var(prices)
    assert 0.001 < hv < 0.5, f"Historical VaR {hv:.4f} outside plausible range"
