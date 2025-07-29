"""Tests for the safety classification and decision layer."""

import pytest
from src.agent.safety import (
    classify,
    check,
    annotate_response,
    RiskCategory,
    SafetyDecision,
)


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

class TestClassify:
    def test_buy_advice_blocked(self):
        assert classify("Should I buy this stock?") == RiskCategory.HIGH_RISK_ADVICE

    def test_sell_advice_blocked(self):
        assert classify("Should I sell my shares?") == RiskCategory.HIGH_RISK_ADVICE

    def test_invest_advice_blocked(self):
        assert classify("Should I invest in Equinor?") == RiskCategory.HIGH_RISK_ADVICE

    def test_recommend_blocked(self):
        assert classify("Can you recommend whether to buy?") == RiskCategory.HIGH_RISK_ADVICE

    def test_good_investment_blocked(self):
        assert classify("Is this a good investment?") == RiskCategory.HIGH_RISK_ADVICE

    def test_price_prediction_blocked(self):
        assert classify("Will the price go up tomorrow?") == RiskCategory.UNSUPPORTED_PREDICTION

    def test_forecast_blocked(self):
        assert classify("What is the price forecast for next week?") == RiskCategory.UNSUPPORTED_PREDICTION

    def test_future_price_blocked(self):
        assert classify("Where will the price be next month?") == RiskCategory.UNSUPPORTED_PREDICTION

    def test_savings_flagged(self):
        assert classify("Should I put my savings in this?") == RiskCategory.AMBIGUOUS_DECISION

    def test_retirement_flagged(self):
        assert classify("Is this safe for my retirement portfolio?") == RiskCategory.AMBIGUOUS_DECISION

    def test_volatility_allowed(self):
        assert classify("Calculate the volatility") == RiskCategory.TECHNICAL_CALCULATION

    def test_var_allowed(self):
        assert classify("Calculate the Value-at-Risk") == RiskCategory.TECHNICAL_CALCULATION

    def test_drawdown_allowed(self):
        assert classify("What was the maximum drawdown?") == RiskCategory.TECHNICAL_CALCULATION

    def test_expected_shortfall_allowed(self):
        assert classify("Calculate expected shortfall") == RiskCategory.TECHNICAL_CALCULATION

    def test_methodology_educational(self):
        assert classify("Explain the VaR methodology") == RiskCategory.SAFE_EDUCATIONAL

    def test_data_source_educational(self):
        assert classify("Where did the data come from?") == RiskCategory.SAFE_EDUCATIONAL

    def test_safety_rules_educational(self):
        assert classify("What safety rules does this system follow?") == RiskCategory.SAFE_EDUCATIONAL

    def test_case_insensitive(self):
        assert classify("SHOULD I BUY THIS STOCK?") == RiskCategory.HIGH_RISK_ADVICE


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------

class TestCheck:
    def test_buy_question_not_allowed(self):
        decision = check("Should I buy Equinor stock?")
        assert decision.allowed is False

    def test_buy_question_has_refusal(self):
        decision = check("Should I buy Equinor stock?")
        assert decision.refusal_reason is not None
        assert len(decision.refusal_reason) > 20

    def test_prediction_not_allowed(self):
        decision = check("Will the price go up tomorrow?")
        assert decision.allowed is False

    def test_prediction_has_refusal(self):
        decision = check("Will the price go up tomorrow?")
        assert decision.refusal_reason is not None

    def test_volatility_allowed(self):
        decision = check("What is the volatility?")
        assert decision.allowed is True

    def test_volatility_no_refusal(self):
        decision = check("What is the volatility?")
        assert decision.refusal_reason is None

    def test_educational_allowed(self):
        decision = check("Explain Value-at-Risk")
        assert decision.allowed is True

    def test_ambiguous_allowed_with_flag(self):
        decision = check("Is this safe for my retirement portfolio?")
        assert decision.allowed is True
        assert decision.human_review_required is True

    def test_ambiguous_has_warning(self):
        decision = check("Should I put my savings in this?")
        assert decision.warning is not None
        assert "human review" in decision.warning.lower()

    def test_technical_no_human_review(self):
        decision = check("Calculate the maximum drawdown")
        assert decision.human_review_required is False

    def test_returns_safety_decision(self):
        decision = check("What is VaR?")
        assert isinstance(decision, SafetyDecision)

    def test_eu_ai_act_tier_present(self):
        decision = check("What is the volatility?")
        assert decision.eu_ai_act_tier is not None
        assert len(decision.eu_ai_act_tier) > 0

    def test_confidence_note_present(self):
        decision = check("What is the drawdown?")
        assert decision.confidence_note is not None

    def test_blocked_has_correct_tier(self):
        decision = check("Should I buy this stock?")
        assert "unacceptable" in decision.eu_ai_act_tier.lower()

    def test_calculation_has_minimal_risk_tier(self):
        decision = check("Calculate volatility")
        assert "minimal" in decision.eu_ai_act_tier.lower()


# ---------------------------------------------------------------------------
# annotate_response()
# ---------------------------------------------------------------------------

class TestAnnotateResponse:
    def test_adds_risk_category(self):
        response = {"answer": "The volatility is 32%.", "basis": "calculation"}
        decision = check("What is the volatility?")
        annotate_response(response, decision)
        assert "risk_category" in response

    def test_adds_human_review_field(self):
        response = {"answer": "...", "basis": "calculation"}
        decision = check("What is the volatility?")
        annotate_response(response, decision)
        assert "human_review_required" in response
        assert response["human_review_required"] is False

    def test_adds_eu_ai_act_tier(self):
        response = {"answer": "...", "basis": "calculation"}
        decision = check("Calculate drawdown")
        annotate_response(response, decision)
        assert "eu_ai_act_tier" in response

    def test_human_review_warning_prepended(self):
        response = {"answer": "The risk metrics are...", "basis": "calculation"}
        decision = check("Is this safe for my retirement portfolio?")
        annotate_response(response, decision)
        assert "human review" in response["answer"].lower()

    def test_no_warning_for_safe_question(self):
        original_answer = "The volatility is 32%."
        response = {"answer": original_answer, "basis": "calculation"}
        decision = check("What is the volatility?")
        annotate_response(response, decision)
        assert response["answer"] == original_answer
