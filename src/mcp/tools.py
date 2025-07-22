"""
MCP-style structured tool wrappers for the financial risk engine.

Each wrapper accepts a typed input dict, calls the existing risk functions,
and returns a structured output dict with metadata (tool name, assumptions,
limitations). This layer separates agent orchestration from tool execution —
the agent never calls risk functions directly; it goes through these wrappers.
"""

import json
import pandas as pd

from src.risk.volatility import daily_volatility, annualised_volatility
from src.risk.drawdown import max_drawdown, max_drawdown_date
from src.risk.var import historical_var, parametric_var, expected_shortfall
from src.risk.returns import simple_returns, log_returns, cumulative_returns
from src.risk.rolling import rolling_volatility, rolling_var, stress_period_flag


# ---------------------------------------------------------------------------
# Input / output types (plain dicts — no external dependency required)
# ---------------------------------------------------------------------------

def mcp_calculate_volatility(prices: pd.Series, annualise: bool = True) -> dict:
    """
    MCP tool: calculate volatility of a price series.

    Input:  prices (pd.Series), annualise (bool, default True)
    Output: structured dict with daily and annualised volatility, metadata
    """
    dv = daily_volatility(prices)
    av = annualised_volatility(prices)

    return {
        "tool": "calculate_volatility",
        "version": "1.0",
        "inputs": {"annualise": annualise},
        "outputs": {
            "daily_volatility": round(dv, 6),
            "annualised_volatility": round(av, 6),
            "annualised_volatility_pct": f"{av:.4%}",
        },
        "metadata": {
            "assumptions": (
                "Volatility is the standard deviation of log returns. "
                "Annualised by multiplying daily volatility by sqrt(252 trading days)."
            ),
            "limitations": (
                "Backward-looking. Does not model volatility clustering or regime changes."
            ),
            "observations_used": len(prices),
        },
    }


def mcp_calculate_drawdown(prices: pd.Series) -> dict:
    """
    MCP tool: calculate maximum drawdown and drawdown date.

    Input:  prices (pd.Series with DatetimeIndex or default index)
    Output: structured dict with max drawdown, trough date, metadata
    """
    mdd = max_drawdown(prices)

    try:
        trough_date = str(max_drawdown_date(prices))
    except Exception:
        trough_date = "unavailable"

    return {
        "tool": "calculate_drawdown",
        "version": "1.0",
        "inputs": {},
        "outputs": {
            "max_drawdown": round(mdd, 6),
            "max_drawdown_pct": f"{mdd:.4%}",
            "trough_date": trough_date,
        },
        "metadata": {
            "assumptions": (
                "Drawdown = (current_price - running_peak) / running_peak. "
                "Maximum drawdown is the worst peak-to-trough decline over the full period."
            ),
            "limitations": (
                "Backward-looking. Past drawdowns are not predictive of future drawdowns."
            ),
            "observations_used": len(prices),
        },
    }


def mcp_calculate_var(
    prices: pd.Series,
    confidence: float = 0.95,
    method: str = "historical",
) -> dict:
    """
    MCP tool: calculate Value-at-Risk.

    Input:  prices (pd.Series), confidence (float), method ('historical'|'parametric')
    Output: structured dict with VaR value, interpretation, metadata
    """
    if method == "parametric":
        var_value = parametric_var(prices, confidence)
        method_note = "Gaussian parametric (assumes normally distributed returns)"
    else:
        var_value = historical_var(prices, confidence)
        method_note = "Historical simulation (empirical return distribution)"

    return {
        "tool": "calculate_var",
        "version": "1.0",
        "inputs": {"confidence": confidence, "method": method},
        "outputs": {
            "var": round(var_value, 6),
            "var_pct": f"{var_value:.4%}",
            "confidence_level": confidence,
            "method": method,
            "interpretation": (
                f"With {int(confidence * 100)}% confidence, the one-day loss will not "
                f"exceed {var_value:.4%} (based on historical data)."
            ),
        },
        "metadata": {
            "method_note": method_note,
            "assumptions": (
                "One-day, single-asset VaR. Historical VaR assumes future returns "
                "follow the same distribution as the sample period."
            ),
            "limitations": (
                "VaR does not quantify losses beyond the threshold. "
                "Does not account for liquidity risk or fat tails (historical method)."
            ),
            "observations_used": len(prices),
        },
    }


def mcp_calculate_expected_shortfall(
    prices: pd.Series,
    confidence: float = 0.95,
) -> dict:
    """
    MCP tool: calculate Expected Shortfall (CVaR).

    Input:  prices (pd.Series), confidence (float)
    Output: structured dict with ES value, comparison to VaR, metadata
    """
    es = expected_shortfall(prices, confidence)
    var = historical_var(prices, confidence)

    return {
        "tool": "calculate_expected_shortfall",
        "version": "1.0",
        "inputs": {"confidence": confidence},
        "outputs": {
            "expected_shortfall": round(es, 6),
            "expected_shortfall_pct": f"{es:.4%}",
            "var_pct": f"{var:.4%}",
            "confidence_level": confidence,
            "interpretation": (
                f"On the worst {int((1 - confidence) * 100)}% of trading days, "
                f"the average loss is {es:.4%}, "
                f"exceeding the {int(confidence * 100)}% VaR of {var:.4%}."
            ),
        },
        "metadata": {
            "assumptions": (
                "Historical ES: mean of returns in the tail beyond the VaR threshold."
            ),
            "limitations": (
                "Sensitive to extreme observations. "
                "Assumes sample period is representative of future tail behaviour."
            ),
            "observations_used": len(prices),
        },
    }


def mcp_generate_risk_summary(
    prices: pd.Series,
    confidence: float = 0.95,
    dataset_label: str = "Unknown dataset",
) -> dict:
    """
    MCP tool: generate a full risk summary.

    Input:  prices (pd.Series), confidence (float), dataset_label (str)
    Output: structured dict with all key risk metrics and metadata
    """
    r = simple_returns(prices)
    av = annualised_volatility(prices)
    mdd = max_drawdown(prices)
    hvar = historical_var(prices, confidence)
    pvar = parametric_var(prices, confidence)
    es = expected_shortfall(prices, confidence)

    return {
        "tool": "generate_risk_summary",
        "version": "1.0",
        "inputs": {"confidence": confidence, "dataset_label": dataset_label},
        "outputs": {
            "dataset": dataset_label,
            "observations": len(prices),
            "mean_daily_return_pct": f"{r.mean():.4%}",
            "annualised_volatility_pct": f"{av:.4%}",
            "max_drawdown_pct": f"{mdd:.4%}",
            "historical_var_pct": f"{hvar:.4%}",
            "parametric_var_pct": f"{pvar:.4%}",
            "expected_shortfall_pct": f"{es:.4%}",
            "confidence_level": confidence,
        },
        "metadata": {
            "assumptions": (
                f"All metrics computed from daily closing prices. "
                f"VaR and ES at {int(confidence * 100)}% confidence. "
                "Volatility annualised using sqrt(252) trading days."
            ),
            "limitations": (
                "All metrics are backward-looking. "
                "They describe past behaviour and are not forecasts. "
                "This analysis does not constitute investment advice."
            ),
        },
    }
