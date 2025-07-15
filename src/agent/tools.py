"""LangChain tool wrappers around the core risk engine functions."""

import json
import pandas as pd
from langchain.tools import tool

from src.risk.returns import simple_returns, log_returns, cumulative_returns
from src.risk.volatility import daily_volatility, annualised_volatility
from src.risk.drawdown import drawdown_series, max_drawdown, max_drawdown_date
from src.risk.var import historical_var, parametric_var, expected_shortfall
from src.risk.rolling import rolling_volatility, rolling_var


# Module-level price series — set by the agent before each run
_prices: pd.Series | None = None
_dataset_label: str = "Unknown dataset"
_confidence: float = 0.95
_rolling_window: int = 21


def set_context(prices: pd.Series, label: str, confidence: float = 0.95, window: int = 21) -> None:
    """Inject the current price series and metadata before invoking the agent."""
    global _prices, _dataset_label, _confidence, _rolling_window
    _prices = prices
    _dataset_label = label
    _confidence = confidence
    _rolling_window = window


def _require_prices() -> pd.Series:
    # DEBUG — remove after confirming context is wired correctly
    print(f"DEBUG _require_prices: _prices is None={_prices is None}, "
          f"module id={id(__import__('src.agent.tools', fromlist=['_prices']))}, "
          f"len={len(_prices) if _prices is not None else 'n/a'}")
    if _prices is None:
        raise ValueError("No dataset loaded. Upload or select a dataset first.")
    return _prices


@tool
def calculate_returns(return_type: str = "simple") -> str:
    """
    Calculate returns from the loaded price series.
    return_type: 'simple' (default), 'log', or 'cumulative'.
    Returns summary statistics of the return series.
    """
    prices = _require_prices()
    if return_type == "log":
        r = log_returns(prices)
        label = "Log returns"
    elif return_type == "cumulative":
        r = cumulative_returns(prices)
        label = "Cumulative returns"
    else:
        r = simple_returns(prices)
        label = "Simple returns"

    result = {
        "tool": "calculate_returns",
        "dataset": _dataset_label,
        "return_type": return_type,
        "label": label,
        "mean": round(float(r.mean()), 6),
        "std": round(float(r.std()), 6),
        "min": round(float(r.min()), 6),
        "max": round(float(r.max()), 6),
        "observations": len(r),
        "assumptions": "Returns computed from closing prices. Simple returns: (P_t-P_{t-1})/P_{t-1}.",
    }
    return json.dumps(result)


@tool
def calculate_volatility(annualise: bool = True) -> str:
    """
    Calculate volatility of the loaded price series.
    annualise: if True (default), returns annualised volatility (daily * sqrt(252)).
    """
    prices = _require_prices()
    dv = daily_volatility(prices)
    av = annualised_volatility(prices)

    result = {
        "tool": "calculate_volatility",
        "dataset": _dataset_label,
        "daily_volatility": round(dv, 6),
        "annualised_volatility": round(av, 4),
        "annualised_volatility_pct": f"{av:.2%}",
        "trading_days_per_year": 252,
        "assumptions": (
            "Volatility is the standard deviation of log returns. "
            "Annualised by multiplying daily volatility by sqrt(252). "
            "This is a backward-looking measure based on historical data."
        ),
        "limitations": "Does not account for volatility clustering or regime changes.",
    }
    return json.dumps(result)


@tool
def calculate_drawdown() -> str:
    """
    Calculate the drawdown series and maximum drawdown of the loaded price series.
    Drawdown measures peak-to-trough decline in value.
    """
    prices = _require_prices()
    mdd = max_drawdown(prices)

    result = {
        "tool": "calculate_drawdown",
        "dataset": _dataset_label,
        "max_drawdown": round(mdd, 6),
        "max_drawdown_pct": f"{mdd:.2%}",
        "assumptions": (
            "Drawdown = (current_price - running_peak) / running_peak. "
            "Maximum drawdown is the worst peak-to-trough decline over the full period."
        ),
        "limitations": "Backward-looking. Past drawdowns are not predictive of future drawdowns.",
    }
    return json.dumps(result)


@tool
def calculate_var(confidence: float = 0.0, method: str = "historical") -> str:
    """
    Calculate Value-at-Risk (VaR) for the loaded price series.
    confidence: confidence level between 0.90 and 0.99 (0.0 uses the session default).
    method: 'historical' (default) or 'parametric'.
    VaR is the maximum daily loss not exceeded with the given confidence probability.
    """
    prices = _require_prices()
    conf = confidence if confidence > 0 else _confidence

    if method == "parametric":
        var_value = parametric_var(prices, conf)
        method_note = "Gaussian parametric (assumes normally distributed returns)"
    else:
        var_value = historical_var(prices, conf)
        method_note = "Historical simulation (empirical return distribution)"

    result = {
        "tool": "calculate_var",
        "dataset": _dataset_label,
        "confidence_level": conf,
        "method": method,
        "var": round(var_value, 6),
        "var_pct": f"{var_value:.2%}",
        "interpretation": (
            f"With {int(conf*100)}% confidence, the daily loss will not exceed "
            f"{var_value:.2%} on any given trading day (based on historical data)."
        ),
        "method_note": method_note,
        "limitations": (
            "VaR does not describe losses beyond the threshold. "
            "Historical VaR assumes future returns follow the same distribution as the sample period. "
            "This is a one-day, single-asset estimate."
        ),
    }
    return json.dumps(result)


@tool
def calculate_expected_shortfall(confidence: float = 0.0) -> str:
    """
    Calculate Expected Shortfall (CVaR) for the loaded price series.
    confidence: confidence level between 0.90 and 0.99 (0.0 uses the session default).
    ES is the mean loss in the tail beyond the VaR threshold.
    """
    prices = _require_prices()
    conf = confidence if confidence > 0 else _confidence
    es = expected_shortfall(prices, conf)
    var = historical_var(prices, conf)

    result = {
        "tool": "calculate_expected_shortfall",
        "dataset": _dataset_label,
        "confidence_level": conf,
        "expected_shortfall": round(es, 6),
        "expected_shortfall_pct": f"{es:.2%}",
        "var_pct": f"{var:.2%}",
        "interpretation": (
            f"On the {int((1-conf)*100)}% of worst trading days, "
            f"the average loss is {es:.2%}. "
            f"This exceeds the {int(conf*100)}% VaR of {var:.2%}."
        ),
        "limitations": (
            "Historical ES assumes the sample period is representative of future tail behaviour. "
            "ES is more sensitive to extreme observations than VaR."
        ),
    }
    return json.dumps(result)


@tool
def generate_risk_summary() -> str:
    """
    Generate a full risk summary for the loaded price series covering returns,
    volatility, drawdown, VaR, and expected shortfall.
    """
    prices = _require_prices()
    r = simple_returns(prices)
    conf = _confidence

    result = {
        "tool": "generate_risk_summary",
        "dataset": _dataset_label,
        "observations": len(prices),
        "mean_daily_return": round(float(r.mean()), 6),
        "mean_daily_return_pct": f"{r.mean():.4%}",
        "daily_volatility": round(daily_volatility(prices), 6),
        "annualised_volatility_pct": f"{annualised_volatility(prices):.2%}",
        "max_drawdown_pct": f"{max_drawdown(prices):.2%}",
        "historical_var_pct": f"{historical_var(prices, conf):.2%}",
        "parametric_var_pct": f"{parametric_var(prices, conf):.2%}",
        "expected_shortfall_pct": f"{expected_shortfall(prices, conf):.2%}",
        "confidence_level": conf,
        "assumptions": (
            "All metrics computed from daily closing prices. "
            f"VaR and ES at {int(conf*100)}% confidence. "
            "Volatility annualised using sqrt(252) trading days."
        ),
        "limitations": (
            "All metrics are backward-looking statistical summaries. "
            "They describe past behaviour and are not forecasts. "
            "This analysis does not constitute investment advice."
        ),
    }
    return json.dumps(result)


def get_all_tools() -> list:
    """Return all registered risk tools for the agent."""
    return [
        calculate_returns,
        calculate_volatility,
        calculate_drawdown,
        calculate_var,
        calculate_expected_shortfall,
        generate_risk_summary,
    ]
