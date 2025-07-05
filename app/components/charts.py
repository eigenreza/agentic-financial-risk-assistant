"""Plotly chart builders for the Streamlit risk dashboard."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.risk.returns import simple_returns, cumulative_returns
from src.risk.volatility import rolling_volatility
from src.risk.drawdown import drawdown_series
from src.risk.var import historical_var


def price_chart(df: pd.DataFrame, date_col: str = "Date", price_col: str = "Close", title: str = "Price") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[date_col], y=df[price_col], mode="lines", name=price_col, line=dict(color="#1f77b4")))
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Price", template="plotly_white", height=350)
    return fig


def returns_chart(df: pd.DataFrame, date_col: str = "Date", price_col: str = "Close") -> go.Figure:
    r = simple_returns(df[price_col])
    dates = df[date_col].iloc[1:].reset_index(drop=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=r.values, name="Daily Return", marker_color="#2ca02c"))
    fig.update_layout(title="Daily Simple Returns", xaxis_title="Date", yaxis_title="Return", template="plotly_white", height=350)
    return fig


def rolling_volatility_chart(df: pd.DataFrame, date_col: str = "Date", price_col: str = "Close", window: int = 21) -> go.Figure:
    rv = rolling_volatility(df[price_col], window=window).dropna()
    dates = df[date_col].iloc[-len(rv):].reset_index(drop=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rv.values, mode="lines", name=f"{window}d Rolling Vol", line=dict(color="#ff7f0e")))
    fig.update_layout(
        title=f"Rolling Annualised Volatility ({window}-day window)",
        xaxis_title="Date", yaxis_title="Annualised Volatility",
        template="plotly_white", height=350,
    )
    return fig


def drawdown_chart(df: pd.DataFrame, date_col: str = "Date", price_col: str = "Close") -> go.Figure:
    dd = drawdown_series(df[price_col])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[date_col], y=dd.values * 100,
        mode="lines", fill="tozeroy", name="Drawdown (%)",
        line=dict(color="#d62728"),
    ))
    fig.update_layout(title="Drawdown (%)", xaxis_title="Date", yaxis_title="Drawdown (%)", template="plotly_white", height=350)
    return fig


def var_chart(df: pd.DataFrame, date_col: str = "Date", price_col: str = "Close", confidence: float = 0.95) -> go.Figure:
    r = simple_returns(df[price_col])
    var_line = historical_var(df[price_col], confidence)
    dates = df[date_col].iloc[1:].reset_index(drop=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=r.values, name="Daily Return", marker_color="#aec7e8"))
    fig.add_hline(
        y=-var_line,
        line_dash="dash",
        line_color="red",
        annotation_text=f"VaR {int(confidence*100)}% = {var_line:.2%}",
    )
    fig.update_layout(
        title=f"Returns with {int(confidence*100)}% Historical VaR",
        xaxis_title="Date", yaxis_title="Return",
        template="plotly_white", height=350,
    )
    return fig
