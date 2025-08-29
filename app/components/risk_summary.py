"""Render a structured risk summary table for a loaded price series."""

import pandas as pd
import streamlit as st

from src.risk.returns import simple_returns, cumulative_returns
from src.risk.volatility import annualised_volatility, daily_volatility
from src.risk.drawdown import max_drawdown, max_drawdown_date
from src.risk.var import historical_var, parametric_var, expected_shortfall


def render_risk_summary(
    df: pd.DataFrame,
    dataset_label: str,
    source_note: str,
    date_col: str = "Date",
    price_col: str = "Close",
    confidence: float = 0.95,
) -> None:
    """Display a risk summary panel with key statistics."""

    prices = df[price_col]
    dates = df[date_col]
    r = simple_returns(prices)

    ann_vol = annualised_volatility(prices)
    mdd = max_drawdown(prices)
    hvar = historical_var(prices, confidence)
    pvar = parametric_var(prices, confidence)
    es = expected_shortfall(prices, confidence)
    cum_ret = cumulative_returns(prices).iloc[-1] if len(prices) > 1 else float("nan")

    try:
        mdd_date = max_drawdown_date(prices.set_axis(dates))
        mdd_date_str = mdd_date.strftime("%Y-%m-%d")
    except Exception:
        mdd_date_str = "n/a"

    st.subheader("Risk Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", dataset_label)
        st.metric("Observations", f"{len(df):,}")
        st.metric("Period start", dates.iloc[0].strftime("%Y-%m-%d"))
        st.metric("Period end", dates.iloc[-1].strftime("%Y-%m-%d"))

    with col2:
        st.metric("Cumulative return", f"{cum_ret:.2%}")
        st.metric("Avg daily return", f"{r.mean():.4%}")
        st.metric("Daily volatility", f"{daily_volatility(prices):.4%}")
        st.metric("Annualised volatility", f"{ann_vol:.2%}")

    with col3:
        st.metric("Maximum drawdown", f"{mdd:.2%}")
        st.metric("Max drawdown date", mdd_date_str)
        st.metric(f"Hist. VaR ({int(confidence*100)}%)", f"{hvar:.2%}")
        st.metric(f"Param. VaR ({int(confidence*100)}%)", f"{pvar:.2%}")
        st.metric(f"Exp. Shortfall ({int(confidence*100)}%)", f"{es:.2%}")

    with st.expander("Methodology and assumptions"):
        st.markdown(f"""
**Dataset:** {dataset_label}

**Source:** {source_note}

**Returns:** Simple percentage returns `(P_t - P_{{t-1}}) / P_{{t-1}}`

**Volatility:** Standard deviation of log returns, annualised by `sqrt(252)`

**Drawdown:** `(current_price - running_peak) / running_peak`

**Historical VaR ({int(confidence*100)}%):** Empirical quantile of the return distribution: the loss not exceeded on `{int(confidence*100)}%` of trading days

**Parametric VaR ({int(confidence*100)}%):** Gaussian assumption: `-(mean - z * std)` where `z = {confidence:.2f}` quantile

**Expected Shortfall ({int(confidence*100)}%):** Mean loss in the tail beyond the VaR threshold (also called CVaR)

**Limitations:** All metrics are backward-looking. Past volatility and drawdown are not predictive of future performance. This analysis does not constitute investment advice.
""")
