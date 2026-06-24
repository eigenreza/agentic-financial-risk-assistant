"""Agentic Financial Risk Assistant: Streamlit application entry point."""

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

# Bump the base font size site-wide so body text, captions, and widget labels
# all scale together instead of just the headings.
st.markdown(
    """
    <style>
    html, body, [class*="st-"], .stMarkdown, .stCaption, .stTextInput label,
    .stExpander, p, li, span {
        font-size: 1.15rem !important;
        line-height: 1.6 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Agentic Financial Risk Assistant")
st.markdown(
    "Built by **Reza Azad Gholami** &middot; "
    "[GitHub repository](https://github.com/eigenreza/agentic-financial-risk-assistant)"
)
st.markdown(
    "> Uncertainty-aware financial risk analysis using controlled Python tools. "
    "Not investment advice."
)

with st.expander("What is this and how do I use it?", expanded=True):
    st.markdown(
        """
This is a small risk analysis assistant built around five sample datasets: Equinor stock,
Brent crude oil, the USD/NOK exchange rate, the S&P 500, and the VIX, all covering 2018
to 2024. The data here is synthetic, generated from a geometric Brownian motion model with
a fixed random seed, so the numbers won't match the real market history for these assets,
but the statistical behaviour (drift, volatility clustering, the shape of the return
distribution) is realistic enough to demonstrate the analysis properly. If you want to plug
in real prices instead, the data module supports pulling them from Yahoo Finance.

Pick a dataset from the sidebar and the dashboard fills in straight away with the price
chart, daily returns, rolling volatility, drawdown, and Value at Risk. From there you can
ask the agent questions in plain English. It never invents a number: every calculation
goes through a tested Python function (the same ones backing the charts), and every
explanation of methodology is pulled from the project's own documentation rather than the
model's memory.

A few things worth trying:

- *What is the annualised volatility of this asset?*
- *What was the maximum drawdown and when did it happen?*
- *What is the 95% Value at Risk?*
- *Can you walk me through the math behind annualised volatility, with the formula?*
- *Should I buy this stock?* (the agent will politely refuse, this falls under investment
  advice and gets blocked before the model is even called)

That fourth question is a good one to try if you're curious about the mechanics. Ask the
agent to show its work and it will lay out the actual formula, something like

$$\\sigma_{\\text{annual}} = \\sigma_{\\text{daily}} \\times \\sqrt{252}$$

where $\\sigma_{\\text{daily}}$ is the standard deviation of daily log returns and 252 is
the standard count of trading days in a year. Every answer also comes labelled with which
tool was called, which documents were retrieved, and an EU AI Act risk tier, so you can see
exactly where the answer came from.

Go ahead and give it a try.
        """
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
            source_note = "Synthetic sample data (GBM, seed 42): see data/README.md"
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
        st.caption(f"{len(df):,} rows total: showing first 50")

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

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Basis of answer**")
                st.info(response["basis"])
            with col2:
                st.markdown("**Tools called**")
                st.info(", ".join(response["tool_calls"]) if response["tool_calls"] else "None")
            with col3:
                st.markdown("**Documents retrieved**")
                st.info(", ".join(response.get("rag_sources", [])) or "None")

            col4, col5, col6 = st.columns(3)
            with col4:
                st.markdown("**Risk category**")
                st.info(response.get("risk_category", "—"))
            with col5:
                st.markdown("**EU AI Act tier**")
                st.info(response.get("eu_ai_act_tier", "—"))
            with col6:
                st.markdown("**Human review required**")
                flag = response.get("human_review_required", False)
                if flag:
                    st.warning("Yes")
                else:
                    st.info("No")

            if response.get("rag_chunks"):
                with st.expander("Retrieved document excerpts"):
                    source_labels = {
                        "data_readme":      "Data Source Documentation",
                        "risk_methodology": "Risk Methodology",
                        "responsible_ai":   "Responsible AI Policy",
                        "mcp_architecture": "MCP Architecture",
                        "eu_ai_act_mapping":"EU AI Act Mapping",
                    }
                    for chunk in response["rag_chunks"]:
                        label = source_labels.get(chunk["source"], chunk["source"])
                        st.caption(f"**{label}** (score: {chunk['score']:.2f})")
                        excerpt = chunk["text"][:400]
                        st.text(excerpt + ("..." if len(chunk["text"]) > 400 else ""))

            if response.get("error"):
                st.error(f"Agent error: {response['error']}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "**Disclaimer:** This tool is for technical risk-analysis demonstration only. "
    "It does not provide investment advice. Results are based on historical data "
    "and statistical models which have inherent limitations."
)
