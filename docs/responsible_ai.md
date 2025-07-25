# Responsible AI Policy

This document describes the responsible AI principles and safety controls implemented in the Agentic Financial Risk Assistant. It is included in the RAG source set so the agent can cite it when answering questions about system behaviour, limitations, and safety rules.

---

## 1. Purpose and scope

This system is a **technical risk-analysis demonstration tool**. It is designed to help users understand the statistical risk properties of financial time-series data through controlled, verifiable calculations.

It is **not** a regulated financial advice system. It does not provide investment recommendations, portfolio management services, or financial planning.

---

## 2. Core safety rules

The following rules are enforced by the agent's system prompt and safety layer. They apply to every response.

| Rule | Description |
|---|---|
| No investment advice | The agent never says "buy", "sell", or "hold". It never recommends a course of action regarding a financial instrument. |
| No unsupported predictions | The agent never predicts future prices, returns, or market movements. All statements about the future include explicit uncertainty language. |
| Tool-first answers | Every numerical result must come from a verified Python tool call. The agent does not invent numbers. |
| Source attribution | Every answer states the tool used, the data source, and the key assumptions. |
| Uncertainty language | Every response includes backward-looking caveats: results describe past behaviour, not future outcomes. |
| Human-review flag | Questions that could lead to consequential financial decisions are flagged for human review. |
| Fallback mode | If no LLM API key is available, the system runs in deterministic mode. The risk dashboard remains fully functional without the agent. |

---

## 3. Answer metadata

Every agent response includes structured metadata fields:

- **Basis of answer** — `calculation` (tool was called), `reasoning` (LLM reasoning without tool), or `error`
- **Tools called** — the names of all tools invoked to produce the answer
- **Confidence level** — the VaR/ES confidence level used (where applicable)
- **Limitations** — backward-looking caveats, sample-period warnings, and model assumptions

---

## 4. What the system will not do

- Recommend buying, selling, or holding any financial instrument
- Predict future prices or returns
- Assert that any investment strategy is safe or profitable
- Claim that past risk metrics guarantee future outcomes
- Provide tax, legal, or regulatory advice
- Operate without disclosing that it is an AI system

---

## 5. Human-review flagging

The agent flags a response for human review when the question:

- Involves a consequential financial decision (e.g. "Should I invest my savings in this asset?")
- Requests a prediction about future market behaviour
- Involves regulatory or legal interpretation
- Falls into an ambiguous risk category where the agent cannot confidently determine the appropriate safety boundary

A human-review flag does not mean the question is refused — it means the answer should be reviewed by a qualified professional before being acted upon.

---

## 6. EU AI Act alignment

This system applies an EU AI Act-inspired risk-tier framework:

| AI Act risk concept | Project interpretation | Control applied |
|---|---|---|
| Unacceptable risk | Manipulative or deceptive financial recommendations | Refusal |
| High-risk-style concern | User may rely on output for consequential financial decisions | Human-review flag + limitations |
| Transparency risk | User may not realise AI is involved | Visible AI disclaimer on every page |
| Minimal-risk use | Educational or statistical analysis of uploaded data | Allowed with assumptions shown |

See `docs/eu_ai_act_mapping.md` for the full mapping.

---

## 7. Data handling

- The system processes only the data the user uploads or selects. No data is transmitted to external servers beyond the LLM API call.
- The LLM API receives the user's question and the agent's tool outputs. Raw price series are not sent to the LLM — only the computed statistical results.
- No user data is stored between sessions.
- Synthetic sample data is generated with a fixed random seed (42) for full reproducibility. It does not represent real market data.

---

## 8. Limitations statement

This tool has the following known limitations:

1. All risk metrics are backward-looking. They describe past price behaviour, not future risk.
2. Synthetic sample data does not represent real market conditions.
3. Single-asset analysis only — no portfolio effects are modelled.
4. The LLM may misinterpret ambiguous questions. Always review tool-call traces.
5. The system has not been validated for regulated financial use cases.
6. Model outputs should not be used as the sole basis for any financial decision.

---

## 9. Disclaimer

> **This tool is for technical risk-analysis demonstration only. It does not provide investment advice. All results are based on historical data and statistical models which have inherent limitations. Past performance is not indicative of future results.**
