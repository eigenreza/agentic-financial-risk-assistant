# Agentic Financial Risk Assistant

> Production-style agentic AI prototype for financial risk and uncertainty analysis.

![Tests](https://img.shields.io/badge/tests-141%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

This project builds on previous research experience in uncertainty modelling and financial risk analysis.

The Agentic Financial Risk Assistant lets a user upload or select financial time-series data and ask natural-language questions — *What is the volatility of this asset? What was the maximum drawdown? What is the Value-at-Risk?* — and receive answers grounded in controlled Python tools, retrieved methodology documents, and explicit uncertainty disclosures.

**The LLM acts as an orchestrator, not a calculator.** Every numerical result comes from a verified Python tool call. Every methodological answer comes from a retrieved document. Every output carries explicit assumptions, limitations, and safety metadata.

---

## Screenshots

| Risk dashboard | Agent answer with tool trace |
|---|---|
| *(add screenshot)* | *(add screenshot)* |

| Safety refusal | RAG citation |
|---|---|
| *(add screenshot)* | *(add screenshot)* |

> Screenshots to be added after final review. See `docs/screenshots/`.

---

## Key features

- **Controlled tool execution** — volatility, drawdown, Value-at-Risk, Expected Shortfall, rolling risk — all computed by verified, tested Python functions; the LLM never invents numbers
- **MCP-style tool/data access layer** — structured boundary between agent orchestration and tool execution using the official `mcp` Python SDK; 5 tools, 5 resource accessors, runnable server stub
- **RAG over methodology documents** — FAISS retrieval over `risk_methodology.md`, `data/README.md`, `responsible_ai.md`, and `mcp_architecture.md`; source citations shown in UI
- **Deterministic safety layer** — investment advice and price predictions blocked in Python before the LLM is invoked; never depends on LLM judgement for safety decisions
- **EU AI Act-inspired risk-tier mapping** — every response carries `risk_category` and `eu_ai_act_tier` metadata; unacceptable-risk questions are refused, high-risk questions are flagged for human review
- **Uncertainty-aware answers** — every response includes basis of answer, tools called, documents retrieved, confidence note, and human-review flag
- **Fallback mode** — full risk dashboard works without an API key; agent panel is disabled with a clear message
- **141 tests passing** — risk engine, MCP tools, safety layer, EU AI Act mapping, data validation
- **Docker-ready** — multi-stage `python:3.11-slim` image; API key at runtime only; confirmed working
- **Kubernetes manifests** — Deployment, Service, Ingress (WebSocket), HPA; apply directly to AKS
- **Azure deployment** — Container Apps (scale-to-zero) and AKS paths documented; `az acr build` script included
- **GitHub Actions CI** — test + lint + Docker build on every push and PR

---

## Architecture

```
User
  │
  ▼
Streamlit App
  │
  ▼
Safety Layer (deterministic Python — runs before LLM)
  │ allowed              │ blocked → refusal
  ▼                      ▼
LangChain Agent       Structured refusal
  │
  ├── MCP Tool/Data Access Layer (src/mcp/)
  │       └── Risk Engine (src/risk/)
  │               └── Financial data (data/raw/)
  │
  └── RAG Retriever (FAISS, all-MiniLM-L6-v2)
          └── Methodology docs (docs/, data/README.md)
  │
  ▼
Response: answer + tool calls + RAG sources + risk_category + eu_ai_act_tier + human_review_required
```

See [`docs/architecture.md`](docs/architecture.md) for the full layer-by-layer description with data-flow examples.

---

## Data sources

| Dataset | Ticker | Source | Period |
|---|---|---|---|
| Equinor ASA stock price | EQNR | Yahoo Finance / synthetic sample | 2018–2024 |
| Brent crude oil price | BZ=F | Yahoo Finance / synthetic sample | 2018–2024 |
| USD/NOK exchange rate | USDNOK=X | Stooq / synthetic sample | 2018–2024 |
| S&P 500 index | ^GSPC | Yahoo Finance / synthetic sample | 2018–2024 |
| VIX volatility index | ^VIX | Yahoo Finance / synthetic sample | 2018–2024 |

Current version uses synthetic GBM sample data (seed 42) for full reproducibility. See [`data/README.md`](data/README.md) for real data download instructions via `yfinance`.

---

## Quickstart

```bash
# Clone
git clone https://github.com/eigenreza/agentic-financial-risk-assistant.git
cd agentic-financial-risk-assistant

# Create virtual environment (Python 3.11 required)
py -3.11 -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set API key (optional — app runs in fallback mode without it)
set ANTHROPIC_API_KEY=your_key_here        # Windows
# export ANTHROPIC_API_KEY=your_key_here  # Linux/Mac

# Run
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`.

---

## Docker

```bash
# Build
docker build -t agentic-financial-risk-assistant .

# Run (fallback mode — no API key)
docker run -p 8501:8501 agentic-financial-risk-assistant

# Run with agent enabled
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key agentic-financial-risk-assistant

# Via Compose
docker compose up --build
```

---

## Tests

```bash
pytest tests/ -v
# 141 passed
```

Test coverage: risk engine (39), MCP tools (29), safety layer (38), EU AI Act mapping (35).

---

## MCP-style tool and data access

The `src/mcp/` layer uses the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) to expose a structured tool and resource access interface. The agent never calls `src/risk/` directly — it goes through versioned MCP wrappers. In production, this server would run as a separate process and could connect to enterprise APIs, Azure-hosted models, or managed data sources.

```bash
# Start the MCP server (stdio mode — for inspection)
python -m src.mcp.server
```

See [`docs/mcp_architecture.md`](docs/mcp_architecture.md) for design rationale and production extension paths.

---

## Kubernetes

```bash
kubectl apply -f deployment/kubernetes/
kubectl rollout status deployment/financial-risk-assistant
```

Manifests: `deployment.yaml` (2 replicas, rolling update, resource limits, health probes), `service.yaml` (ClusterIP), `ingress.yaml` (nginx, WebSocket support for Streamlit), `hpa.yaml` (2–8 replicas, CPU + memory).

See [`deployment/kubernetes/README.md`](deployment/kubernetes/README.md) for full instructions including AKS deployment.

---

## Azure deployment

**Azure Container Apps (preferred — serverless):**
```bash
# Set your API key in the environment, then:
cd deployment/azure
chmod +x azure_cli_commands.sh
./azure_cli_commands.sh
```

See [`deployment/azure/deploy_container_apps.md`](deployment/azure/deploy_container_apps.md) for step-by-step instructions and [`deployment/azure/aks_extension_note.md`](deployment/azure/aks_extension_note.md) for the AKS path.

---

## Evaluation

30 evaluation questions were run against the Equinor synthetic sample dataset:

| Category | Pass rate |
|---|---|
| Technical calculations (volatility, VaR, drawdown, ES) | 10/10 |
| Educational / RAG (methodology, data source, safety rules) | 10/10 |
| Safety / refusal (investment advice, predictions) | 6/6 |
| Human review flagging | 1/1 |
| Metadata / transparency | 3/3 |
| **Total** | **30/30** |

See [`evaluation/evaluation_results.md`](evaluation/evaluation_results.md) for full results and [`evaluation/failure_modes.md`](evaluation/failure_modes.md) for known limitations.

---

## Responsible AI

- No direct investment advice — blocked deterministically before the LLM is invoked
- No unsupported price predictions — blocked at the same layer
- Human-review flag for consequential financial questions
- Source-grounded answers — every RAG answer cites the retrieved document
- Tool-call trace — every calculation answer shows which tool was called
- Uncertainty language — every response includes backward-looking caveats
- Fallback mode — no degraded-mode hallucination when API is unavailable
- EU AI Act-inspired risk-tier mapping on every response

> **Disclaimer:** This tool is for technical risk-analysis demonstration only. It does not provide investment advice. Results are based on historical data and statistical models which have inherent limitations.

---

## EU AI Act risk-tier mapping

| AI Act risk concept | Project interpretation | Control |
|---|---|---|
| Unacceptable risk | Direct financial advice; unsupported predictions | Hard refusal — LLM not called |
| High-risk-style concern | Consequential financial decisions | Human-review warning prepended |
| Transparency risk | User unaware of AI involvement | Basis field + visible disclaimer |
| Minimal-risk use | Educational / statistical analysis | Allowed with assumptions shown |

See [`docs/eu_ai_act_mapping.md`](docs/eu_ai_act_mapping.md) for the full mapping.

---

## Documentation

| Document | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Full system architecture — all 8 layers, data-flow examples |
| [`docs/risk_methodology.md`](docs/risk_methodology.md) | Formulae and definitions for all risk metrics |
| [`docs/responsible_ai.md`](docs/responsible_ai.md) | Safety rules, human-review protocol, limitations |
| [`docs/mcp_architecture.md`](docs/mcp_architecture.md) | MCP layer design and production extensions |
| [`docs/eu_ai_act_mapping.md`](docs/eu_ai_act_mapping.md) | EU AI Act risk-tier mapping |
| [`data/README.md`](data/README.md) | Dataset documentation and download instructions |
| [`reports/technical_report.md`](reports/technical_report.md) | Full technical report |
| [`reports/project_summary.md`](reports/project_summary.md) | One-page project summary |

---

## Repository structure

```
agentic-financial-risk-assistant/
├── app/                    # Streamlit application
├── src/
│   ├── agent/              # LangChain agent, tools, prompts, safety
│   ├── mcp/                # MCP server, tools, resources
│   ├── data/               # Loaders, validators, sample data
│   ├── risk/               # Risk analytics engine
│   └── rag/                # FAISS RAG pipeline
├── data/raw/               # Synthetic sample CSVs
├── docs/                   # Architecture and methodology docs
├── deployment/
│   ├── kubernetes/         # K8s manifests
│   └── azure/              # Azure deployment docs and scripts
├── tests/                  # 141 tests
├── evaluation/             # Evaluation questions, results, failure modes
├── reports/                # Technical report and project summary
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/      # GitHub Actions CI
```
