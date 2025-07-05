"""Load and clean financial time-series CSV files."""

import pandas as pd
from pathlib import Path


def load_csv(path: str | Path, date_col: str = "Date", price_col: str = "Close") -> pd.DataFrame:
    """
    Load a CSV, parse dates, validate columns, sort, and return a clean DataFrame
    with exactly two columns: date_col and price_col.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path)

    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found. Available: {list(df.columns)}")
    if price_col not in df.columns:
        raise ValueError(f"Price column '{price_col}' not found. Available: {list(df.columns)}")

    df[date_col] = pd.to_datetime(df[date_col])
    df = df[[date_col, price_col]].copy()
    df = df.dropna(subset=[date_col, price_col])
    df = df.sort_values(date_col).reset_index(drop=True)
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[price_col])

    return df
