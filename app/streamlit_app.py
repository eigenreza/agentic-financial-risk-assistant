"""Agentic Financial Risk Assistant — Streamlit application entry point."""

import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of how streamlit is invoked.
sys.path.insert(0, str(Path(__file__).parent.parent))

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
from src.agent.langchain_agent import run_agent, api_key_available
from src.agent.tools import set_context
from src.agent.prompts import FALLBACK_MESSAGE

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
                selections["uploaded_file"],
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
    errors = validate(df, date_col=selections["date_col"], price_col=selections["price_col"])
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

    # Push current dataset into the agent tool context on every rerun so the
    # module-level _prices in tools.py is always fresh when the agent runs.
    set_context(df[price_col], dataset_label, confidence, window)

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

    # Charts
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

    st.markdown("---")

    # ── Agent panel ───────────────────────────────────────────────────────────
    st.subheader("Ask the Risk Agent")

    if not api_key_available():
        st.warning(FALLBACK_MESSAGE)
    else:
        st.caption(
            "The agent uses controlled Python tools for all numerical answers. "
            "It will not provide investment advice or make price predictions."
        )

        question = st.text_input(
            "Ask a question about this dataset",
            placeholder="e.g. What is the annualised volatility? What was the maximum drawdown?",
        )

        if st.button("Run agent", disabled=not question):
            with st.spinner("Agent running..."):
                response = run_agent(
                    question=question,
                    prices=df[price_col],
                    dataset_label=dataset_label,
                    confidence=confidence,
                    rolling_window=window,
                )

            st.markdown("#### Answer")
            st.markdown(response["answer"])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Basis of answer**")
                st.info(response["basis"])
            with col2:
                st.markdown("**Tools called**")
                if response["tool_calls"]:
                    st.info(", ".join(response["tool_calls"]))
                else:
                    st.info("No tools called")

            if response.get("error"):
                st.error(f"Agent error: {response['error']}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "**Disclaimer:** This tool is for technical risk-analysis demonstration only. "
    "It does not provide investment advice. Results are based on historical data "
    "and statistical models which have inherent limitations."
)
