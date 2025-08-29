# EU AI Act Risk-Tier Mapping

## System context

The Agentic Financial Risk Assistant is a **technical financial risk-analysis demonstration tool**. It is not a regulated investment-advice system, a credit-scoring system, or a system used in employment or critical infrastructure decisions.

This document maps the system's features and behaviours to the EU AI Act risk-tier framework, and documents the safety controls implemented at each tier.

---

## Risk-tier mapping table

| AI Act risk concept | Project interpretation | Safety control implemented |
|---|---|---|
| **Unacceptable risk** | Manipulative or deceptive financial recommendations; unsupported price predictions | Hard refusal in `safety.py`, request blocked before reaching the LLM |
| **High-risk-style concern** | User may rely on output for a consequential financial decision (e.g. investing savings) | Human-review flag prepended to answer; warning shown in UI |
| **Transparency risk** | User may not realise AI is involved in generating the answer | Visible AI disclaimer on every page; basis-of-answer field in every response |
| **Minimal-risk use** | Educational or statistical analysis of uploaded data; deterministic tool calculation | Allowed with assumptions, limitations, and data source shown |

---

## Risk categories (implemented in `src/agent/safety.py`)

The safety layer classifies every user question into one of six categories before the LLM is invoked:

| Category | Description | Action |
|---|---|---|
| `safe_educational` | Questions about methodology, data sources, system design, or responsible AI | Allowed, RAG retrieval triggered |
| `technical_calculation` | Requests for specific risk metrics (volatility, VaR, drawdown, ES) | Allowed, tool call triggered |
| `interpretive_risk` | Questions asking for interpretation of risk results | Allowed, answer includes backward-looking caveats |
| `high_risk_advice` | Direct investment advice ("should I buy/sell?") | **Blocked**, refusal message returned, LLM not called |
| `unsupported_prediction` | Future price or return predictions | **Blocked**, refusal message returned, LLM not called |
| `ambiguous_decision` | Questions that may support a consequential financial decision | Allowed, **human-review flag** prepended to answer |

---

## Safety controls by tier

### Unacceptable risk, blocked

Questions that request direct investment advice or unsupported predictions are blocked deterministically in Python before the LLM is invoked. The agent returns a structured refusal that:

- Explains what the system can and cannot do
- Does not call any tool or LLM
- Logs the risk category for audit purposes

Example blocked questions:
- *"Should I buy Equinor stock?"*
- *"Will the price go up tomorrow?"*
- *"Is this a good investment?"*
- *"Recommend whether to invest"*

Refusal template:
> *"I cannot provide direct investment advice. I can provide a technical risk analysis of the uploaded data, for example, volatility, drawdown, or Value-at-Risk. For investment decisions, please consult a qualified financial adviser."*

### High-risk-style concern, human-review flag

Questions that may support consequential financial decisions receive a human-review flag. The agent still answers but prepends a warning:

> *"⚠️ Human review recommended. This question may involve a consequential financial decision. The output should be reviewed by a qualified professional before being acted upon."*

### Transparency, AI disclosure

Every response includes:
- A visible disclaimer: *"This tool is for technical risk-analysis demonstration only. It does not provide investment advice."*
- A **basis-of-answer** field: `calculation`, `rag`, `mixed`, or `reasoning`, so the user always knows whether the answer came from a tool, a document, or the LLM
- Tool names called (if any)
- Document sources retrieved (if any)

### Minimal-risk, allowed with metadata

Technical calculations and educational questions are answered with:
- The tool used and its inputs
- The data source and observation count
- Key assumptions (e.g. 252 trading days, normal distribution assumption for parametric VaR)
- Backward-looking limitations

---

## Answer metadata fields

Every agent response includes the following safety metadata fields:

| Field | Type | Description |
|---|---|---|
| `risk_category` | str | Classified risk category (e.g. `technical_calculation`) |
| `human_review_required` | bool | True if the question is in the `ambiguous_decision` category |
| `eu_ai_act_tier` | str | Mapped EU AI Act tier label |
| `confidence_note` | str | One-line note on the basis of confidence in the answer |
| `basis` | str | `calculation`, `rag`, `mixed`, `reasoning`, `no_data`, or `error` |
| `tool_calls` | list[str] | Names of tools called to produce the answer |
| `rag_sources` | list[str] | Names of documents retrieved |

---

## Fallback behaviour

If no LLM API key is available:
- The system runs in deterministic mode
- The full risk dashboard (volatility, drawdown, VaR, ES, charts) remains functional
- The agent panel is replaced by a clear message explaining how to enable the LLM
- No safety controls are bypassed, the deterministic risk calculations apply the same limitations

---

## What this system is not

This system does **not** fall into the EU AI Act's mandatory high-risk categories (Annex III), which include:
- AI systems used in critical infrastructure
- AI systems for education and vocational training that determine access
- AI systems for employment and worker management
- AI systems for access to essential services (credit scoring, insurance)
- AI systems used in law enforcement
- AI systems for migration, asylum, and border control management
- AI systems used in the administration of justice

It is a technical demonstration tool used for portfolio and educational purposes. It is not deployed in any regulated context.

---

## Production extensions

In a production system subject to EU AI Act obligations, additional controls would include:
- Formal conformity assessment and CE marking (for high-risk systems)
- Post-market monitoring and incident reporting
- Human oversight mechanism with documented override procedures
- Data governance documentation including data provenance and bias assessment
- Technical documentation maintained throughout the system lifecycle
- Registration in the EU AI Act database (for high-risk systems)
