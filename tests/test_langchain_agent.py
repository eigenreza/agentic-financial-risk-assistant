"""Tests for the LangChain agent's tool-call attribution and RAG basis logic."""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.agent import langchain_agent


@pytest.fixture
def sample_prices():
    return pd.Series([100.0, 101.0, 99.5, 102.0, 103.5], name="Close")


def test_build_agent_requests_intermediate_steps(monkeypatch):
    """
    AgentExecutor only populates intermediate_steps (and therefore tool_calls)
    when return_intermediate_steps=True is passed at construction. Regression
    test for a bug where this flag was missing, causing every response to
    report "Tools called: None" even when a tool genuinely ran.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    executor = langchain_agent._build_agent()
    assert executor.return_intermediate_steps is True


def _fake_tool_action(tool_name: str):
    class _Action:
        tool = tool_name
    return _Action()


def test_run_agent_reports_calculation_when_tool_called(sample_prices):
    fake_result = {
        "output": "The annualised volatility is 32.13%.",
        "intermediate_steps": [
            (_fake_tool_action("calculate_volatility"), "0.3213"),
        ],
    }

    class _FakeExecutor:
        def invoke(self, input_dict):
            return fake_result

    with patch.object(langchain_agent, "_build_agent", return_value=_FakeExecutor()):
        response = langchain_agent.run_agent(
            question="What is the annualised volatility?",
            prices=sample_prices,
            dataset_label="test-dataset",
        )

    assert response["tool_calls"] == ["calculate_volatility"]
    assert response["basis"] in ("calculation", "mixed")


def test_run_agent_reports_none_when_no_tool_called(sample_prices):
    fake_result = {
        "output": "Volatility measures the dispersion of returns.",
        "intermediate_steps": [],
    }

    class _FakeExecutor:
        def invoke(self, input_dict):
            return fake_result

    with patch.object(langchain_agent, "_build_agent", return_value=_FakeExecutor()):
        response = langchain_agent.run_agent(
            question="What is volatility?",
            prices=sample_prices,
            dataset_label="test-dataset",
        )

    assert response["tool_calls"] == []
    assert response["basis"] in ("rag", "reasoning")
