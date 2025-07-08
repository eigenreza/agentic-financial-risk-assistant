"""Streamlit sidebar: data source selection and analysis controls."""

import streamlit as st
import pandas as pd
from src.data.sample_data import list_available, get_label


def render_sidebar() -> dict:
    """
    Render the sidebar and return a dict of user selections:
      {
        "source": "upload" | "sample",
        "uploaded_file": UploadedFile | None,
        "sample_name": str | None,
        "date_col": str,
        "price_col": str,
        "confidence": float,
        "rolling_window": int,
        "analyses": list[str],
      }
    """
    st.sidebar.title("Financial Risk Assistant")
    st.sidebar.markdown("---")

    # --- Data source ---
    st.sidebar.subheader("Data source")
    source = st.sidebar.radio(
        "Choose data source",
        options=["Sample dataset", "Upload CSV"],
        index=0,
        label_visibility="collapsed",
    )

    uploaded_file = None
    sample_name = None

    if source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader(
            "Upload a CSV file", type=["csv"], help="Must contain a date column and a price column."
        )
    else:
        available = list_available()
        labels = {name: get_label(name) for name in available}
        sample_name = st.sidebar.selectbox(
            "Select sample dataset",
            options=available,
            format_func=lambda n: labels[n],
        )

    st.sidebar.markdown("---")

    # --- Column mapping (shown for uploads) ---
    st.sidebar.subheader("Column mapping")
    date_col = st.sidebar.text_input("Date column name", value="Date")
    price_col = st.sidebar.text_input("Price column name", value="Close")

    st.sidebar.markdown("---")

    # --- Risk parameters ---
    st.sidebar.subheader("Risk parameters")
    confidence = st.sidebar.slider(
        "VaR confidence level",
        min_value=0.90,
        max_value=0.99,
        value=0.95,
        step=0.01,
        format="%.2f",
    )
    rolling_window = st.sidebar.slider(
        "Rolling window (trading days)",
        min_value=5,
        max_value=63,
        value=21,
        step=1,
    )

    st.sidebar.markdown("---")

    # --- Analysis selection ---
    st.sidebar.subheader("Analyses")
    all_analyses = [
        "Price series",
        "Daily returns",
        "Rolling volatility",
        "Drawdown",
        "VaR chart",
    ]
    analyses = st.sidebar.multiselect(
        "Select charts to display",
        options=all_analyses,
        default=all_analyses,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "This tool is for technical risk-analysis demonstration only. "
        "It does not provide investment advice."
    )

    return {
        "source": "upload" if source == "Upload CSV" else "sample",
        "uploaded_file": uploaded_file,
        "sample_name": sample_name,
        "date_col": date_col,
        "price_col": price_col,
        "confidence": confidence,
        "rolling_window": rolling_window,
        "analyses": analyses,
    }
