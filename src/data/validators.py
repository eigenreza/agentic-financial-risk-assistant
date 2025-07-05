"""Validate a loaded financial time-series DataFrame before risk calculations."""

import pandas as pd

MIN_OBSERVATIONS = 30


def validate(
    df: pd.DataFrame,
    date_col: str = "Date",
    price_col: str = "Close",
    allow_negative: bool = False,
) -> list[str]:
    """
    Return a list of validation error messages.
    An empty list means the DataFrame passed all checks.
    """
    errors: list[str] = []

    if date_col not in df.columns:
        errors.append(f"Missing date column: '{date_col}'")
    if price_col not in df.columns:
        errors.append(f"Missing price column: '{price_col}'")

    if errors:
        return errors

    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        errors.append(f"Date column '{date_col}' is not datetime type")

    if not pd.api.types.is_numeric_dtype(df[price_col]):
        errors.append(f"Price column '{price_col}' is not numeric")

    n_missing = df[price_col].isna().sum()
    if n_missing > 0:
        errors.append(f"Price column has {n_missing} missing value(s)")

    if not allow_negative and (df[price_col] <= 0).any():
        errors.append("Price column contains zero or negative values")

    if len(df) < MIN_OBSERVATIONS:
        errors.append(
            f"Too few observations: {len(df)} (minimum {MIN_OBSERVATIONS} required)"
        )

    return errors


def assert_valid(
    df: pd.DataFrame,
    date_col: str = "Date",
    price_col: str = "Close",
    allow_negative: bool = False,
) -> None:
    """Raise ValueError if the DataFrame fails any validation check."""
    errors = validate(df, date_col, price_col, allow_negative)
    if errors:
        raise ValueError("Data validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
