"""
Safety layer for the Agentic Financial Risk Assistant.

Responsibilities:
  1. Classify every user question into a risk category
  2. Block requests that cross hard safety boundaries (investment advice, predictions)
  3. Flag requests that require human review
  4. Attach safety metadata to every response

This module is called by run_agent() before the LLM is invoked, so safety
decisions are made deterministically in Python — not by the LLM.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Risk categories
# ---------------------------------------------------------------------------

class RiskCategory(str, Enum):
    SAFE_EDUCATIONAL        = "safe_educational"
    TECHNICAL_CALCULATION   = "technical_calculation"
    INTERPRETIVE_RISK       = "interpretive_risk"
    HIGH_RISK_ADVICE        = "high_risk_advice"
    UNSUPPORTED_PREDICTION  = "unsupported_prediction"
    AMBIGUOUS_DECISION      = "ambiguous_decision"


# ---------------------------------------------------------------------------
# Safety decision dataclass
# ---------------------------------------------------------------------------

@dataclass
class SafetyDecision:
    allowed: bool
    risk_category: RiskCategory
    human_review_required: bool
    refusal_reason: str | None          # set only when allowed=False
    warning: str | None                 # soft warning, allowed but flagged
    confidence_note: str                # always present
    eu_ai_act_tier: str                 # mapped EU AI Act tier label
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Keyword banks
# ---------------------------------------------------------------------------

_INVESTMENT_ADVICE_PATTERNS = (
    "should i buy", "should i sell", "should i invest", "should i hold",
    "is it a good time to buy", "is it a good time to sell",
    "recommend", "what should i do", "is it worth buying",
    "is it worth investing", "is this a good investment",
    "should i put money", "should i allocate",
    "tell me to buy", "tell me to sell",
)

_PREDICTION_PATTERNS = (
    "will the price", "will it go up", "will it go down",
    "price prediction", "price forecast", "predict the",
    "what will happen", "where will the price", "future price",
    "price target", "price tomorrow", "next week price",
    "will the stock", "will the market", "forecast",
    "going to increase", "going to decrease", "going to rise", "going to fall",
)

_HIGH_RISK_DECISION_PATTERNS = (
    "my savings", "my portfolio", "my retirement", "my pension",
    "all my money", "how much should i", "should i put all",
    "my life savings", "how much to invest",
)

_TECHNICAL_CALCULATION_PATTERNS = (
    "volatility", "var", "value-at-risk", "value at risk",
    "drawdown", "maximum drawdown", "expected shortfall", "cvar",
    "returns", "log returns", "simple returns", "cumulative",
    "rolling", "annualised", "annualized", "calculate", "compute",
    "what is the", "show me the", "give me the",
)

_EDUCATIONAL_PATTERNS = (
    "what is", "how does", "how is", "explain", "define", "definition",
    "what does", "can you explain", "describe", "methodology",
    "formula", "how do you calculate", "what are the limitations",
    "what assumptions", "data source", "where did the data",
    "what safety", "safety rules", "mcp", "architecture",
    "responsible ai", "eu ai act",
)


# ---------------------------------------------------------------------------
# EU AI Act tier mapping
# ---------------------------------------------------------------------------

_EU_AI_ACT_TIERS: dict[RiskCategory, str] = {
    RiskCategory.SAFE_EDUCATIONAL:       "Minimal risk — educational/statistical analysis",
    RiskCategory.TECHNICAL_CALCULATION:  "Minimal risk — deterministic tool-based calculation",
    RiskCategory.INTERPRETIVE_RISK:      "Limited risk — AI-generated interpretation, assumptions stated",
    RiskCategory.HIGH_RISK_ADVICE:       "Unacceptable risk — direct financial advice, blocked",
    RiskCategory.UNSUPPORTED_PREDICTION: "Unacceptable risk — unsupported prediction, blocked",
    RiskCategory.AMBIGUOUS_DECISION:     "High-risk-style concern — human review required",
}

_REFUSAL_TEMPLATES: dict[RiskCategory, str] = {
    RiskCategory.HIGH_RISK_ADVICE: (
        "I cannot provide direct investment advice. "
        "I can provide a technical risk analysis of the uploaded data — "
        "for example, volatility, drawdown, or Value-at-Risk. "
        "For investment decisions, please consult a qualified financial adviser."
    ),
    RiskCategory.UNSUPPORTED_PREDICTION: (
        "I cannot predict future prices or returns. "
        "All risk metrics I compute are backward-looking statistical summaries "
        "based on historical data. They do not forecast future market behaviour."
    ),
}

_HUMAN_REVIEW_WARNING = (
    "⚠️ **Human review recommended.** This question may involve a consequential "
    "financial decision. The output should be reviewed by a qualified professional "
    "before being acted upon."
)

_CONFIDENCE_NOTES: dict[RiskCategory, str] = {
    RiskCategory.SAFE_EDUCATIONAL:      "Answer is grounded in retrieved documentation.",
    RiskCategory.TECHNICAL_CALCULATION: "Answer is based on a verified Python tool calculation.",
    RiskCategory.INTERPRETIVE_RISK:     "Answer involves statistical interpretation. Results are backward-looking.",
    RiskCategory.HIGH_RISK_ADVICE:      "Request blocked — direct investment advice not provided.",
    RiskCategory.UNSUPPORTED_PREDICTION:"Request blocked — unsupported predictions not provided.",
    RiskCategory.AMBIGUOUS_DECISION:    "Answer requires human review before being acted upon.",
}


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify(question: str) -> RiskCategory:
    """
    Classify a user question into a RiskCategory.
    Rules are evaluated in priority order: hard blocks first.
    """
    q = question.lower()

    # Hard blocks (highest priority)
    if any(p in q for p in _INVESTMENT_ADVICE_PATTERNS):
        return RiskCategory.HIGH_RISK_ADVICE

    if any(p in q for p in _PREDICTION_PATTERNS):
        return RiskCategory.UNSUPPORTED_PREDICTION

    # High-risk decision support
    if any(p in q for p in _HIGH_RISK_DECISION_PATTERNS):
        return RiskCategory.AMBIGUOUS_DECISION

    # Educational intent takes priority over metric keyword match.
    # "Explain the VaR methodology" is educational even though it mentions VaR.
    if any(p in q for p in _EDUCATIONAL_PATTERNS):
        return RiskCategory.SAFE_EDUCATIONAL

    # Pure calculation requests (no educational intent keyword present)
    if any(p in q for p in _TECHNICAL_CALCULATION_PATTERNS):
        return RiskCategory.TECHNICAL_CALCULATION

    # Default: treat as interpretive (allowed with caveats)
    return RiskCategory.INTERPRETIVE_RISK


# ---------------------------------------------------------------------------
# Main safety check
# ---------------------------------------------------------------------------

def check(question: str) -> SafetyDecision:
    """
    Run the full safety check for a question.
    Returns a SafetyDecision with allowed, risk_category, flags, and metadata.
    """
    category = classify(question)
    tier = _EU_AI_ACT_TIERS[category]
    confidence_note = _CONFIDENCE_NOTES[category]

    # Hard blocks
    if category in (RiskCategory.HIGH_RISK_ADVICE, RiskCategory.UNSUPPORTED_PREDICTION):
        return SafetyDecision(
            allowed=False,
            risk_category=category,
            human_review_required=False,
            refusal_reason=_REFUSAL_TEMPLATES[category],
            warning=None,
            confidence_note=confidence_note,
            eu_ai_act_tier=tier,
            metadata={"question_length": len(question)},
        )

    # Human review required
    human_review = category == RiskCategory.AMBIGUOUS_DECISION
    warning = _HUMAN_REVIEW_WARNING if human_review else None

    return SafetyDecision(
        allowed=True,
        risk_category=category,
        human_review_required=human_review,
        refusal_reason=None,
        warning=warning,
        confidence_note=confidence_note,
        eu_ai_act_tier=tier,
        metadata={"question_length": len(question)},
    )


# ---------------------------------------------------------------------------
# Attach safety metadata to an agent response dict
# ---------------------------------------------------------------------------

def annotate_response(response: dict, decision: SafetyDecision) -> dict:
    """
    Merge safety metadata into an agent response dict (in-place + returned).
    """
    response["risk_category"]        = decision.risk_category.value
    response["human_review_required"] = decision.human_review_required
    response["eu_ai_act_tier"]        = decision.eu_ai_act_tier
    response["confidence_note"]       = decision.confidence_note
    if decision.warning:
        # Prepend human-review warning to the answer text
        response["answer"] = decision.warning + "\n\n" + response.get("answer", "")
    return response
