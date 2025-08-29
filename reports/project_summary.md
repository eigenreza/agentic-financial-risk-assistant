# Project Summary

## Agentic Financial Risk Assistant

**Type:** Production-style portfolio prototype
**Stack:** Python 3.11, LangChain, the LLM API, MCP SDK, FAISS, Streamlit, Docker, Kubernetes, Azure, GitHub Actions
**Status:** Complete

---

## What was built

A cloud-deployable agentic AI prototype for uncertainty-aware financial risk analysis. The system lets a user upload or select financial time-series data and ask natural-language questions. Every numerical answer comes from a verified Python tool call. Every methodological answer comes from a retrieved document. Every response carries explicit assumptions, limitations, and safety metadata.

---

## Why it was built

General-purpose LLMs hallucinate numbers, make unsupported predictions, and provide investment advice when they should not. These are architectural problems, not prompt-engineering problems. This project demonstrates how to address all three through system design: by routing every calculation through a tested Python tool, every methodology question through a RAG retriever, and every safety decision through a deterministic Python classifier that runs before the LLM is ever invoked.

---

## Key design decisions

**LLM as orchestrator, not calculator.** The model never computes a risk metric. It selects a tool, calls it, receives a structured result, and formats an explanation. Numerical hallucination is eliminated by design, not by instruction.

**Deterministic safety before the LLM.** The safety layer is Python keyword matching. Blocked requests never reach the model. The behaviour is testable, reproducible, and fully explainable.

**MCP as a structured boundary.** The MCP layer separates agent orchestration from tool execution. The agent can only call registered, versioned wrappers -- it cannot touch the underlying risk functions directly. This makes the system auditable and straightforward to extend.

**EU AI Act-inspired governance.** Every response carries a risk-tier label. This is not just a label -- it drives concrete controls: hard refusals for investment advice, human-review flags for consequential questions, and transparent basis-of-answer metadata for every output.

---

## Technical competencies demonstrated

| Competency | Evidence |
|---|---|
| Agentic AI architecture | LangChain tool-calling agent, MCP layer, RAG, and safety layer all integrated and working end-to-end |
| Production engineering | 141 tests, CI/CD, confirmed Docker build, Kubernetes manifests, Azure Container Apps documentation |
| Responsible AI | Deterministic safety refusals, human-review flagging, EU AI Act risk-tier mapping, source-grounded answers |
| Financial domain knowledge | Volatility, VaR, expected shortfall, drawdown, and rolling metrics all correctly implemented and documented |
| Documentation quality | Architecture doc, risk methodology, responsible AI policy, evaluation report, and failure-mode analysis |

---

## Results

- 141 tests passing across risk engine, MCP tools, safety layer, EU AI Act mapping, and data validation
- 30/30 evaluation questions passed across calculation, RAG, safety, and metadata categories
- Docker build confirmed working end-to-end
- All safety refusals fire correctly and blocked questions never reach the LLM
- RAG retrieves the correct source document for all methodology and data-source questions
