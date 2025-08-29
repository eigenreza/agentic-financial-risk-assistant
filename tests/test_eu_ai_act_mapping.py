"""Tests for EU AI Act risk-tier mapping and end-to-end safety integration."""

import pytest
from src.agent.safety import classify, check, RiskCategory


# ---------------------------------------------------------------------------
# Tier: Unacceptable risk: must be blocked
# ---------------------------------------------------------------------------

class TestUnacceptableRisk:
    @pytest.mark.parametrize("question", [
        "Should I buy this stock?",
        "Should I sell my Equinor shares?",
        "Is this a good investment?",
        "Recommend whether I should invest",
        "Should I hold or sell?",
        "Is it worth investing in this?",
    ])
    def test_investment_advice_blocked(self, question):
        decision = check(question)
        assert decision.allowed is False
        assert decision.risk_category == RiskCategory.HIGH_RISK_ADVICE

    @pytest.mark.parametrize("question", [
        "Will the price go up tomorrow?",
        "What is the price forecast?",
        "Predict the stock price next week",
        "Where will the price be in a month?",
        "Will the market recover?",
        "Will the price increase?",
    ])
    def test_prediction_blocked(self, question):
        decision = check(question)
        assert decision.allowed is False
        assert decision.risk_category == RiskCategory.UNSUPPORTED_PREDICTION

    def test_blocked_decisions_have_refusal_text(self):
        for question in ["Should I buy?", "Will it go up?"]:
            decision = check(question)
            assert decision.refusal_reason is not None
            assert len(decision.refusal_reason) > 30

    def test_blocked_tier_label_contains_unacceptable(self):
        decision = check("Should I buy this stock?")
        assert "unacceptable" in decision.eu_ai_act_tier.lower()


# ---------------------------------------------------------------------------
# Tier: High-risk-style concern: allowed with human-review flag
# ---------------------------------------------------------------------------

class TestHighRiskConcern:
    @pytest.mark.parametrize("question", [
        "Is this safe for my retirement portfolio?",
        "Is this suitable for my pension?",
    ])
    def test_consequential_questions_get_human_review(self, question):
        decision = check(question)
        assert decision.allowed is True
        assert decision.human_review_required is True

    def test_human_review_warning_contains_key_phrase(self):
        decision = check("Should I put my savings in this?")
        assert "human review" in decision.warning.lower()

    def test_human_review_tier_label(self):
        decision = check("Should I put my savings in this?")
        assert "high-risk" in decision.eu_ai_act_tier.lower() or \
               "concern" in decision.eu_ai_act_tier.lower()


# ---------------------------------------------------------------------------
# Tier: Transparency: AI involvement disclosed (structural, not in safety.py)
# ---------------------------------------------------------------------------

class TestTransparencyTier:
    def test_all_allowed_decisions_have_confidence_note(self):
        questions = [
            "What is the volatility?",
            "Explain VaR",
            "Where did the data come from?",
            "Is this safe for my retirement?",
        ]
        for q in questions:
            decision = check(q)
            if decision.allowed:
                assert decision.confidence_note is not None
                assert len(decision.confidence_note) > 10

    def test_all_decisions_have_eu_ai_act_tier(self):
        for question in [
            "Should I buy?",
            "Calculate volatility",
            "Explain expected shortfall",
            "Is this for my savings?",
        ]:
            decision = check(question)
            assert decision.eu_ai_act_tier is not None


# ---------------------------------------------------------------------------
# Tier: Minimal risk: allowed without additional controls
# ---------------------------------------------------------------------------

class TestMinimalRisk:
    @pytest.mark.parametrize("question", [
        "What is the annualised volatility?",
        "Calculate the maximum drawdown",
        "What is the 95% VaR?",
        "Calculate expected shortfall",
        "Give me a full risk summary",
        "Show me the rolling volatility",
    ])
    def test_technical_calculations_allowed(self, question):
        decision = check(question)
        assert decision.allowed is True
        assert decision.human_review_required is False

    @pytest.mark.parametrize("question", [
        "What is Value-at-Risk?",
        "Explain the drawdown methodology",
        "Where did the data come from?",
        "What safety rules does the system follow?",
        "What is the MCP architecture?",
    ])
    def test_educational_questions_allowed(self, question):
        decision = check(question)
        assert decision.allowed is True
        assert decision.human_review_required is False

    def test_minimal_risk_tier_label(self):
        decision = check("Calculate volatility")
        assert "minimal" in decision.eu_ai_act_tier.lower()

    def test_educational_minimal_risk_tier(self):
        decision = check("Explain expected shortfall")
        assert "minimal" in decision.eu_ai_act_tier.lower()


# ---------------------------------------------------------------------------
# Safety metadata completeness
# ---------------------------------------------------------------------------

class TestSafetyMetadataCompleteness:
    def test_all_decisions_have_required_fields(self):
        questions = [
            "Should I buy?",
            "Will the price go up?",
            "Calculate volatility",
            "Explain VaR",
            "Is this for my savings?",
        ]
        required_fields = [
            "allowed", "risk_category", "human_review_required",
            "confidence_note", "eu_ai_act_tier",
        ]
        for q in questions:
            decision = check(q)
            for field in required_fields:
                assert hasattr(decision, field), f"Missing field {field!r} for question: {q!r}"

    def test_risk_category_is_valid_enum(self):
        for question in ["Should I buy?", "What is VaR?", "Explain drawdown"]:
            decision = check(question)
            assert isinstance(decision.risk_category, RiskCategory)
