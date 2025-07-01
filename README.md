# Agentic Financial Risk Assistant

> Production-style agentic AI prototype for financial risk and uncertainty analysis.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

This project builds on previous research experience in uncertainty modelling and financial risk analysis.

The Agentic Financial Risk Assistant is a production-style prototype that lets a user upload or select real financial time-series data and ask natural-language questions — such as *What is the volatility of this asset?*, *What was the maximum drawdown?*, or *What is the Value-at-Risk?* — and receive answers grounded in controlled Python tools, retrieved methodology documents, and explicit uncertainty disclosures.

The system is not a black-box chatbot. The LLM acts as an **orchestrator** over:

- Controlled Python risk-analysis tools
- An MCP-style tool and data access layer
- A RAG retriever over methodology and data-source documents
- A safety and EU AI Act-inspired risk-tier classification layer

---

## Problem statement

Financial risk analysis requires transparency, reproducibility, and uncertainty awareness. General-purpose LLMs hallucinate numerical results and provide unsupported financial recommendations. This prototype demonstrates how an agentic AI system can be architected to avoid those failure modes: by grounding every numerical answer in a verifiable tool call, every methodological answer in a retrieved document, and every output in explicit assumptions and limitations.

---

## Key features

- **Controlled tool execution** — volatility, drawdown, Value-at-Risk, expected shortfall, rolling risk, all computed by verified Python functions
- **MCP-style tool/data access layer** — structured separation between agent orchestration and tool/resource access using the official `mcp` Python SDK
- **RAG over methodology documents** — grounded retrieval from risk methodology, data-source documentation, and responsible-AI notes
- **Safety guardrails** — no direct investment advice, no unsupported predictions, human-review flagging for consequential questions
- **EU AI Act-inspired risk-tier mapping** — questions classified into risk tiers with appropriate safety controls
- **Uncertainty-aware answers** — every response includes confidence level, basis of answer, limitations, and human-review flag
- **Fallback mode** — app runs in deterministic mode without an API key
- **Docker and Kubernetes ready** — reproducible containerised deployment
- **Azure deployment documentation** — Azure Container Apps and AKS extension notes

---

## Architecture overview

```
User
  ↓
Streamlit App
  ↓
LangChain Agent
  ↓
Safety Layer / EU AI Act Risk Classifier
  ↓
MCP-style Tool/Data Access Layer
  ↓
Risk Tools / RAG Retriever
  ↓
Financial Data / Methodology Documents / Data Documentation
  ↓
Response with metrics, sources, limitations, confidence, human-review flag
```

---

## Data sources

| Dataset | Source | Period |
|---|---|---|
| Equinor (EQNR) stock price | Yahoo Finance / synthetic sample | 2018–2024 |
| Brent crude oil price | Yahoo Finance / synthetic sample | 2018–2024 |
| USD/NOK exchange rate | Stooq / synthetic sample | 2018–2024 |
| S&P 500 index | Yahoo Finance / synthetic sample | 2018–2024 |
| VIX volatility index | Yahoo Finance / synthetic sample | 2018–2024 |

> Current version uses synthetic sample data for reproducibility. Real data download instructions are in `data/README.md`.

---

## Quickstart

```bash
# Clone repository
git clone https://github.com/eigenreza/agentic-financial-risk-assistant.git
cd agentic-financial-risk-assistant

# Create virtual environment with Python 3.11
py -3.11 -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set API key (optional — app runs in fallback mode without it)
set ANTHROPIC_API_KEY=your_key_here  # Windows
# export ANTHROPIC_API_KEY=your_key_here  # Linux/Mac

# Run app
streamlit run app/streamlit_app.py
```

---

## Docker

```bash
docker build -t agentic-financial-risk-assistant .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key agentic-financial-risk-assistant
```

---

## MCP-style tool and data access

The system includes an MCP-style tool and data access layer (`src/mcp/`) built with the official `mcp` Python SDK. This layer exposes structured wrappers around the risk-analysis tools and resource accessors for methodology and data-source documents. It demonstrates architectural separation between agent orchestration and tool/data execution — a pattern applicable to enterprise agentic AI systems.

See [`docs/mcp_architecture.md`](docs/mcp_architecture.md) for details.

---

## Responsible AI

- No direct investment advice
- Human-review flag for consequential questions
- Uncertainty and confidence fields in every response
- Source-grounded RAG answers
- Logging of tool calls and assumptions
- Refusal for unsupported predictions
- EU AI Act-inspired risk-tier mapping

> **Disclaimer:** This tool is for technical risk-analysis demonstration only. It does not provide investment advice.

---

## EU AI Act risk-tier summary

| AI Act risk concept | Project interpretation | Safety control |
|---|---|---|
| Unacceptable risk | Manipulative financial recommendations | Refusal |
| High-risk-style concern | Consequential financial decisions | Human-review flag |
| Transparency risk | User unaware of AI involvement | Visible disclaimer |
| Minimal-risk use | Educational/statistical analysis | Allowed with assumptions |

---

## Project status

Currently in development. Repository will be made public after the runnable core is complete, tests pass, and documentation is polished.
