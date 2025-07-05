import pandas as pd
import pytest
from src.data.validators import validate, assert_valid
from src.data.loaders import load_csv
from src.data.sample_data import load_sample


def _make_df(n=100, date_start="2020-01-01", price_start=100.0, step=1.0):
    dates = pd.date_range(date_start, periods=n, freq="B")
    prices = [price_start + i * step for i in range(n)]
    return pd.DataFrame({"Date": dates, "Close": prices})


def test_valid_df_no_errors():
    df = _make_df()
    errors = validate(df)
    assert errors == []


def test_missing_date_column():
    df = _make_df().rename(columns={"Date": "date"})
    errors = validate(df)
    assert any("date column" in e.lower() for e in errors)


def test_missing_price_column():
    df = _make_df().rename(columns={"Close": "Price"})
    errors = validate(df)
    assert any("price column" in e.lower() for e in errors)


def test_negative_price_fails():
    df = _make_df()
    df.loc[0, "Close"] = -1.0
    errors = validate(df)
    assert any("negative" in e.lower() or "zero" in e.lower() for e in errors)


def test_negative_price_allowed_when_flagged():
    df = _make_df()
    df.loc[0, "Close"] = -1.0
    errors = validate(df, allow_negative=True)
    neg_errors = [e for e in errors if "negative" in e.lower() or "zero" in e.lower()]
    assert neg_errors == []


def test_too_few_observations():
    df = _make_df(n=5)
    errors = validate(df)
    assert any("few" in e.lower() for e in errors)


def test_assert_valid_raises_on_bad_data():
    df = _make_df(n=5)
    with pytest.raises(ValueError):
        assert_valid(df)


def test_assert_valid_passes_on_good_data():
    df = _make_df()
    assert_valid(df)  # should not raise


def test_load_csv_returns_dataframe(tmp_path):
    df = _make_df()
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    result = load_csv(path)
    assert "Date" in result.columns
    assert "Close" in result.columns
    assert len(result) == 100


def test_load_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent/path.csv")


def test_load_sample_equinor():
    df = load_sample("equinor_stock_sample")
    assert "Date" in df.columns
    assert "Close" in df.columns
    assert len(df) > 100
    assert (df["Close"] > 0).all()
