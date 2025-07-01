"""
Generate and load synthetic financial time-series sample data.

Synthetic prices use geometric Brownian motion with asset-specific parameters
calibrated to approximate real-world statistical properties (2018-2024).
All series use a fixed random seed (42) for reproducibility.
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

_ASSET_PARAMS = {
    "equinor_stock_sample": {
        "label": "Equinor ASA (EQNR)",
        "s0": 18.50,
        "mu": 0.06,
        "sigma": 0.32,
        "seed_offset": 0,
    },
    "brent_crude_sample": {
        "label": "Brent Crude Oil (USD/bbl)",
        "s0": 68.00,
        "mu": 0.02,
        "sigma": 0.30,
        "seed_offset": 1,
    },
    "usd_nok_sample": {
        "label": "USD/NOK Exchange Rate",
        "s0": 8.10,
        "mu": 0.01,
        "sigma": 0.08,
        "seed_offset": 2,
    },
    "sp500_sample": {
        "label": "S&P 500 Index",
        "s0": 2700.0,
        "mu": 0.10,
        "sigma": 0.18,
        "seed_offset": 3,
    },
    "vix_sample": {
        "label": "VIX Volatility Index",
        "s0": 17.0,
        "mu": 0.00,
        "sigma": 0.55,
        "seed_offset": 4,
    },
}


def _generate_gbm_series(
    s0: float, mu: float, sigma: float, dates: pd.DatetimeIndex, rng: np.random.Generator
) -> np.ndarray:
    n = len(dates)
    dt = 1 / 252
    shocks = rng.standard_normal(n)
    log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shocks
    prices = s0 * np.exp(np.cumsum(log_returns))
    prices = np.insert(prices[:-1], 0, s0)
    return np.maximum(prices, 0.01)


def generate_sample(name: str) -> pd.DataFrame:
    """Return a DataFrame with Date and Close columns for the named asset."""
    if name not in _ASSET_PARAMS:
        raise ValueError(f"Unknown sample dataset: {name!r}. Available: {list_available()}")

    params = _ASSET_PARAMS[name]
    dates = pd.bdate_range(start="2018-01-02", end="2024-12-31")
    rng = np.random.default_rng(42 + params["seed_offset"])
    prices = _generate_gbm_series(params["s0"], params["mu"], params["sigma"], dates, rng)

    df = pd.DataFrame({"Date": dates, "Close": prices})
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def save_all_samples() -> None:
    """Write all synthetic CSVs to data/raw/ (idempotent)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in _ASSET_PARAMS:
        path = DATA_DIR / f"{name}.csv"
        generate_sample(name).to_csv(path, index=False)


def load_sample(name: str) -> pd.DataFrame:
    """Load a sample CSV, generating it on disk if it does not exist."""
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        save_all_samples()
    df = pd.read_csv(path, parse_dates=["Date"])
    return df.sort_values("Date").reset_index(drop=True)


def list_available() -> list[str]:
    return list(_ASSET_PARAMS.keys())


def get_label(name: str) -> str:
    return _ASSET_PARAMS[name]["label"]
