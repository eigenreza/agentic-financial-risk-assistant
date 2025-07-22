"""Tests for the MCP-style tool and resource access layer."""

import pytest
import pandas as pd
import numpy as np
from src.mcp.tools import (
    mcp_calculate_volatility,
    mcp_calculate_drawdown,
    mcp_calculate_var,
    mcp_calculate_expected_shortfall,
    mcp_generate_risk_summary,
)
from src.mcp.resources import read_resource, list_resources
from src.data.sample_data import load_sample


@pytest.fixture
def prices():
    rng = np.random.default_rng(42)
    raw = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 500)))
    return pd.Series(raw, name="Close")


@pytest.fixture
def equinor_prices():
    return load_sample("equinor_stock_sample")["Close"]


# ── Tool: calculate_volatility ────────────────────────────────────────────────

class TestMcpVolatility:
    def test_returns_structured_output(self, prices):
        result = mcp_calculate_volatility(prices)
        assert result["tool"] == "calculate_volatility"
        assert "outputs" in result
        assert "metadata" in result

    def test_outputs_contain_required_fields(self, prices):
        out = mcp_calculate_volatility(prices)["outputs"]
        assert "daily_volatility" in out
        assert "annualised_volatility" in out
        assert "annualised_volatility_pct" in out

    def test_annualised_vol_positive(self, prices):
        out = mcp_calculate_volatility(prices)["outputs"]
        assert out["annualised_volatility"] > 0

    def test_metadata_present(self, prices):
        meta = mcp_calculate_volatility(prices)["metadata"]
        assert "assumptions" in meta
        assert "limitations" in meta
        assert meta["observations_used"] == len(prices)

    def test_equinor_vol_reasonable(self, equinor_prices):
        out = mcp_calculate_volatility(equinor_prices)["outputs"]
        assert 0.05 < out["annualised_volatility"] < 2.0


# ── Tool: calculate_drawdown ──────────────────────────────────────────────────

class TestMcpDrawdown:
    def test_returns_structured_output(self, prices):
        result = mcp_calculate_drawdown(prices)
        assert result["tool"] == "calculate_drawdown"
        assert "outputs" in result

    def test_max_drawdown_negative(self, prices):
        out = mcp_calculate_drawdown(prices)["outputs"]
        assert out["max_drawdown"] <= 0

    def test_max_drawdown_in_range(self, prices):
        out = mcp_calculate_drawdown(prices)["outputs"]
        assert -1.0 <= out["max_drawdown"] <= 0.0

    def test_metadata_observations(self, prices):
        meta = mcp_calculate_drawdown(prices)["metadata"]
        assert meta["observations_used"] == len(prices)


# ── Tool: calculate_var ───────────────────────────────────────────────────────

class TestMcpVar:
    def test_returns_structured_output(self, prices):
        result = mcp_calculate_var(prices)
        assert result["tool"] == "calculate_var"
        assert "outputs" in result

    def test_var_positive(self, prices):
        out = mcp_calculate_var(prices)["outputs"]
        assert out["var"] > 0

    def test_confidence_in_output(self, prices):
        out = mcp_calculate_var(prices, confidence=0.99)["outputs"]
        assert out["confidence_level"] == 0.99

    def test_historical_method_recorded(self, prices):
        out = mcp_calculate_var(prices, method="historical")["outputs"]
        assert out["method"] == "historical"

    def test_parametric_method_recorded(self, prices):
        out = mcp_calculate_var(prices, method="parametric")["outputs"]
        assert out["method"] == "parametric"

    def test_interpretation_string_present(self, prices):
        out = mcp_calculate_var(prices)["outputs"]
        assert isinstance(out["interpretation"], str)
        assert len(out["interpretation"]) > 10

    def test_invalid_input_handled(self):
        tiny = pd.Series([100.0, 101.0])  # too few for meaningful VaR
        result = mcp_calculate_var(tiny)
        # Should return a result dict, not raise
        assert "tool" in result


# ── Tool: calculate_expected_shortfall ───────────────────────────────────────

class TestMcpES:
    def test_returns_structured_output(self, prices):
        result = mcp_calculate_expected_shortfall(prices)
        assert result["tool"] == "calculate_expected_shortfall"

    def test_es_positive(self, prices):
        out = mcp_calculate_expected_shortfall(prices)["outputs"]
        assert out["expected_shortfall"] > 0

    def test_es_exceeds_var(self, prices):
        out = mcp_calculate_expected_shortfall(prices)["outputs"]
        es = out["expected_shortfall"]
        var_val = float(out["var_pct"].strip("%")) / 100
        assert es >= var_val - 1e-9


# ── Tool: generate_risk_summary ───────────────────────────────────────────────

class TestMcpRiskSummary:
    def test_returns_structured_output(self, prices):
        result = mcp_generate_risk_summary(prices)
        assert result["tool"] == "generate_risk_summary"

    def test_all_metrics_present(self, prices):
        out = mcp_generate_risk_summary(prices)["outputs"]
        for key in [
            "annualised_volatility_pct",
            "max_drawdown_pct",
            "historical_var_pct",
            "parametric_var_pct",
            "expected_shortfall_pct",
            "mean_daily_return_pct",
            "observations",
        ]:
            assert key in out, f"Missing key: {key}"

    def test_dataset_label_in_output(self, prices):
        out = mcp_generate_risk_summary(prices, dataset_label="Test Asset")["outputs"]
        assert out["dataset"] == "Test Asset"

    def test_limitations_present(self, prices):
        meta = mcp_generate_risk_summary(prices)["metadata"]
        assert "limitations" in meta
        assert "investment advice" in meta["limitations"]


# ── Resources ─────────────────────────────────────────────────────────────────

class TestMcpResources:
    def test_list_resources_returns_list(self):
        resources = list_resources()
        assert isinstance(resources, list)
        assert len(resources) > 0

    def test_list_resources_has_required_fields(self):
        for r in list_resources():
            assert "name" in r
            assert "uri" in r
            assert "description" in r
            assert "available" in r

    def test_data_readme_available(self):
        result = read_resource("data_readme")
        assert result["available"] is True
        assert result["content"] is not None
        assert len(result["content"]) > 100

    def test_data_readme_content_meaningful(self):
        result = read_resource("data_readme")
        assert "Equinor" in result["content"] or "dataset" in result["content"].lower()

    def test_unknown_resource_returns_error(self):
        result = read_resource("nonexistent_resource")
        assert result["available"] is False
        assert result["error"] is not None

    def test_resource_uri_present(self):
        result = read_resource("data_readme")
        assert result["uri"] is not None
        assert "README" in result["uri"]
