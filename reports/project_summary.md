# Project Summary

## Agentic Financial Risk Assistant

**Type:** Production-style portfolio prototype
**Stack:** Python 3.11 · LangChain · Anthropic claude-haiku-4-5 · MCP SDK · FAISS · Streamlit · Docker · Kubernetes · Azure · GitHub Actions
**Status:** Complete

---

## What was built

A cloud-deployable agentic AI prototype for uncertainty-aware financial risk analysis. The system allows a user to upload or select financial time-series data and ask natural-language questions. Every numerical answer is grounded in a verified Python tool call. Every methodological answer is grounded in a retrieved document. Every output carries explicit assumptions, limitations, and safety metadata.

---

## Why it was built

To demonstrate that prior experience in uncertainty modelling and financial risk analysis can be combined with modern agentic AI engineering — and that the result can be built to production engineering standards: tested, containerised, documented, governed, and deployable.

The project also addresses a real gap in general-purpose LLM usage in finance: LLMs hallucinate numbers, make unsupported predictions, and provide investment advice when they should not. This system shows how to prevent all three through architecture, not just prompting.

---

## Key design decisions

**LLM as orchestrator, not calculator.** The model never computes a risk metric. It selects a tool, calls it, receives a structured result, and formats an explanation. This eliminates numerical hallucination by design.

**Deterministic safety before the LLM.** The safety layer is Python keyword matching, not an LLM judgement. Blocked requests never reach the model. This is testable, reproducible, and explainable.

**MCP as a structured boundary.** The MCP layer separates agent orchestration from tool/data execution. The agent cannot call raw Python functions — only registered, versioned tool wrappers. This makes the system auditable and extensible.

**EU AI Act-inspired governance.** Every response carries a risk-tier label. This demonstrates AI governance awareness and is directly relevant to regulated industry contexts.

---

## What it demonstrates for a hiring team

| Competency | Evidence |
|---|---|
| Agentic AI architecture | LangChain tool-calling agent, MCP layer, RAG, safety layer all integrated and working |
| Production engineering | 141 tests passing, CI/CD, Docker build confirmed, Kubernetes manifests, Azure deployment docs |
| Responsible AI | Safety refusals, human-review flagging, EU AI Act mapping, uncertainty language, source attribution |
| Financial domain knowledge | Volatility, VaR, ES, drawdown, rolling metrics — all correctly implemented and documented |
| Documentation quality | Architecture doc, methodology doc, responsible AI policy, evaluation report, failure-mode analysis |

---

## Results

- **141 tests passing** across risk engine, MCP tools, safety layer, EU AI Act mapping, and data validation
- **30/30 evaluation questions passed** (100% pass rate across calculation, RAG, safety, and metadata categories)
- **Docker build confirmed** working end-to-end
- **All safety refusals work correctly** — blocked questions never reach the LLM
- **RAG retrieves correct sources** — VaR questions retrieve `risk_methodology`, data questions retrieve `data_readme`
