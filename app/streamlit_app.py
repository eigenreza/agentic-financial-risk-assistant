"""Agentic Financial Risk Assistant — Streamlit application entry point."""

import io
import streamlit as st
import pandas as pd

from app.components.sidebar import render_sidebar
from app.components.risk_summary import render_risk_summary
from app.components.charts import (
    price_chart,
    returns_chart,
    rolling_volatility_chart,
    drawdown_chart,
    var_chart,
)
from src.data.loaders import load_csv
from src.data.validators import validate
from src.data.sample_data import load_sample, get_label

st.set_page_config(
    page_title="Financial Risk Assistant",
    page_icon="📊",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Agentic Financial Risk Assistant")
st.markdown(
    "> Uncertainty-aware financial risk analysis using controlled Python tools. "
    "Not investment advice."
)
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
selections = render_sidebar()

# ── Load data ─────────────────────────────────────────────────────────────────
df: pd.DataFrame | None = None
dataset_label = ""
source_note = ""

if selections["source"] == "upload":
    if selections["uploaded_file"] is not None:
        try:
            df = load_csv(
                io.StringIO(selections["uploaded_file"].getvalue().decode("utf-8")),
                date_col=selections["date_col"],
                price_col=selections["price_col"],
            )
            dataset_label = selections["uploaded_file"].name
            source_note = "User-uploaded CSV"
        except Exception as e:
            st.error(f"Could not load file: {e}")
    else:
        st.info("Upload a CSV file in the sidebar to begin.")

else:
    sample_name = selections["sample_name"]
    if sample_name:
        try:
            df = load_sample(sample_name)
            dataset_label = get_label(sample_name)
            source_note = "Synthetic sample data (GBM, seed 42) — see data/README.md"
        except Exception as e:
            st.error(f"Could not load sample: {e}")

# ── Validate ──────────────────────────────────────────────────────────────────
if df is not None:
    errors = validate(
        df,
        date_col=selections["date_col"],
        price_col=selections["price_col"],
    )
    if errors:
        st.error("Data validation failed:\n" + "\n".join(f"- {e}" for e in errors))
        df = None

# ── Main content ──────────────────────────────────────────────────────────────
if df is not None:
    date_col = selections["date_col"]
    price_col = selections["price_col"]
    confidence = selections["confidence"]
    window = selections["rolling_window"]
    analyses = selections["analyses"]

    # Risk summary
    render_risk_summary(
        df,
        dataset_label=dataset_label,
        source_note=source_note,
        date_col=date_col,
        price_col=price_col,
        confidence=confidence,
    )

    st.markdown("---")

    # Charts — arranged in a two-column grid
    chart_map = {
        "Price series": lambda: price_chart(df, date_col, price_col, title=dataset_label),
        "Daily returns": lambda: returns_chart(df, date_col, price_col),
        "Rolling volatility": lambda: rolling_volatility_chart(df, date_col, price_col, window),
        "Drawdown": lambda: drawdown_chart(df, date_col, price_col),
        "VaR chart": lambda: var_chart(df, date_col, price_col, confidence),
    }

    selected_charts = [name for name in chart_map if name in analyses]

    for i in range(0, len(selected_charts), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(selected_charts):
                name = selected_charts[i + j]
                with col:
                    st.plotly_chart(chart_map[name](), use_container_width=True)

    st.markdown("---")

    # Raw data preview
    with st.expander("Raw data preview"):
        st.dataframe(df.head(50), use_container_width=True)
        st.caption(f"{len(df):,} rows total — showing first 50")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "**Disclaimer:** This tool is for technical risk-analysis demonstration only. "
    "It does not provide investment advice. Results are based on historical data "
    "and statistical models which have inherent limitations."
)
