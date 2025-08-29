# System Architecture

## Overview

The Agentic Financial Risk Assistant is a production-style agentic AI prototype for uncertainty-aware financial risk analysis. It is built around a deliberate architectural principle: **the LLM acts as an orchestrator, not a calculator**. Every numerical result comes from a verified Python tool call. Every methodological answer comes from a retrieved document. Every output carries explicit assumptions, limitations, and safety metadata.

This document describes all system layers, their responsibilities, and how they interact.

---

## System diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ question / CSV upload
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Streamlit App  (app/)                          │
│  sidebar · risk summary · charts · agent panel · citations UI   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Safety Layer  (src/agent/safety.py)                 │
│  classify question → allow / block / flag for human review       │
│  EU AI Act risk-tier assignment · refusal templates              │
└──────────┬──────────────────────────────────┬───────────────────┘
           │ allowed                           │ blocked
           ▼                                   ▼
┌──────────────────────┐             ┌─────────────────────────┐
│  LangChain Agent     │             │  Refusal response        │
│  (src/agent/)        │             │  (no LLM call made)      │
│  the language model    │             └─────────────────────────┘
│  tool-calling ReAct  │
└──────┬───────────────┘
       │
       ├──────────────────────────────┐
       │                              │
       ▼                              ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│  MCP Tool/Data       │   │  RAG Retriever                    │
│  Access Layer        │   │  (src/rag/)                       │
│  (src/mcp/)          │   │  FAISS · all-MiniLM-L6-v2         │
│  5 structured tools  │   │  4 source documents               │
│  5 resource accessors│   │  top-k chunks + source names      │
└──────┬───────────────┘   └──────────────┬───────────────────┘
       │                                   │
       ▼                                   ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│  Risk Engine         │   │  Documentation                    │
│  (src/risk/)         │   │  data/README.md                   │
│  returns · vol       │   │  docs/risk_methodology.md         │
│  drawdown · VaR · ES │   │  docs/responsible_ai.md           │
│  rolling metrics     │   │  docs/mcp_architecture.md         │
└──────┬───────────────┘   └──────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Financial Data      │
│  (data/raw/)         │
│  5 synthetic CSVs    │
│  (real via yfinance) │
└──────────────────────┘
```

---

## Layer descriptions

### 1. Data layer

**Location:** `data/raw/`, `src/data/`

**Responsibility:** Load, validate, and provide clean financial time-series data to the rest of the system.

| Component | File | Purpose |
|---|---|---|
| Sample data generator | `src/data/sample_data.py` | GBM synthetic CSVs (seed 42) for Equinor, Brent crude, USD/NOK, S&P 500, VIX |
| CSV loader | `src/data/loaders.py` | Loads local files and Streamlit UploadedFile objects; parses dates; sorts |
| Validator | `src/data/validators.py` | 5 checks: columns, dtype, missing values, negatives, minimum observations |
| Raw data | `data/raw/*.csv` | Five synthetic sample datasets; replaceable with real Yahoo Finance data |

**Design decision:** Static CSV files first. This ensures full reproducibility without API keys, rate limits, or external data availability. Real data is a drop-in replacement via `yfinance`.

---

### 2. Analytics layer

**Location:** `src/risk/`

**Responsibility:** Compute all risk metrics from verified, tested Python functions. The LLM never calculates anything directly.

| Module | Functions | Description |
|---|---|---|
| `returns.py` | `simple_returns`, `log_returns`, `cumulative_returns` | Return series calculations |
| `volatility.py` | `daily_volatility`, `annualised_volatility`, `rolling_volatility` | Volatility using log returns, sqrt(252) annualisation |
| `drawdown.py` | `drawdown_series`, `max_drawdown`, `max_drawdown_date` | Peak-to-trough decline series |
| `var.py` | `historical_var`, `parametric_var`, `expected_shortfall` | Historical simulation and Gaussian VaR; CVaR |
| `rolling.py` | `rolling_mean_return`, `rolling_volatility`, `rolling_var`, `stress_period_flag` | Rolling metrics and stress-period detection |

**Test coverage:** 39 tests across all modules (`tests/test_returns.py`, `test_volatility.py`, `test_drawdown.py`, `test_var.py`, `test_data_validation.py`).

---

### 3. Agent layer

**Location:** `src/agent/`

**Responsibility:** Orchestrate tool calls, retrieve documents, enforce safety, and assemble structured responses.

| Component | File | Purpose |
|---|---|---|
| Tool wrappers | `src/agent/tools.py` | 6 LangChain `@tool` functions wrapping `src/risk/`; structured JSON output with assumptions and limitations |
| Prompts | `src/agent/prompts.py` | System prompt with explicit data-is-loaded guarantee; answer format rules; fallback/no-data templates |
| Agent runner | `src/agent/langchain_agent.py` | ReAct agent (the language model, temp=0); safety check before LLM call; RAG context injection; structured response dict |
| Safety layer | `src/agent/safety.py` | `classify()` → 6 risk categories; `check()` → `SafetyDecision`; `annotate_response()` adds metadata |

**Response dict fields:** `answer`, `tool_calls`, `rag_sources`, `rag_chunks`, `basis`, `risk_category`, `human_review_required`, `eu_ai_act_tier`, `confidence_note`, `error`.

---

### 4. MCP-style tool/data access layer

**Location:** `src/mcp/`

**Responsibility:** Provide a structured, versioned interface between agent orchestration and tool/data execution, using the official `mcp` Python SDK.

| Component | File | Purpose |
|---|---|---|
| Tool wrappers | `src/mcp/tools.py` | 5 functions returning typed dicts with `inputs`, `outputs`, `metadata` |
| Resource accessors | `src/mcp/resources.py` | `read_resource()` and `list_resources()` for 5 documentation files |
| MCP server | `src/mcp/server.py` | `mcp.server.Server` with `list_tools`, `call_tool`, `list_resources`, `read_resource` handlers; runnable via stdio |

**Why this layer exists:** The MCP boundary ensures the agent cannot call raw Python functions directly. Every tool call is routed through a versioned wrapper that validates inputs, adds metadata, and returns structured output. This makes the system auditable, testable, and extensible to enterprise APIs.

**Test coverage:** 29 tests (`tests/test_mcp_tools.py`).

---

### 5. RAG layer

**Location:** `src/rag/`

**Responsibility:** Retrieve relevant document chunks for methodology, data-source, and governance questions.

| Component | File | Purpose |
|---|---|---|
| Document registry | `src/rag/documents.py` | 4 source documents registered by logical name |
| Ingestion pipeline | `src/rag/ingest.py` | Character-level chunking; `all-MiniLM-L6-v2` embeddings; FAISS `IndexFlatIP` (cosine similarity); persistent index |
| Retriever | `src/rag/retriever.py` | `retrieve_with_context()` → top-k chunks with source name and score; LRU-cached |

**Index:** 54 vectors, 384 dimensions, 4 source documents. Built on first run, cached in `data/processed/faiss_index/`.

**Routing:** The agent uses keyword matching (`_is_rag_question`) to decide whether to prepend retrieved context to the LLM input. Pure calculation questions skip RAG entirely.

**Source documents in RAG:**

| Name | File |
|---|---|
| `data_readme` | `data/README.md` |
| `risk_methodology` | `docs/risk_methodology.md` |
| `responsible_ai` | `docs/responsible_ai.md` |
| `mcp_architecture` | `docs/mcp_architecture.md` |

---

### 6. Safety layer

**Location:** `src/agent/safety.py`

**Responsibility:** Classify every user question and enforce safety boundaries **before** the LLM is invoked. Safety decisions are deterministic Python, not probabilistic LLM outputs.

**Risk categories:**

| Category | Action |
|---|---|
| `safe_educational` | Allowed, RAG triggered |
| `technical_calculation` | Allowed, tool call triggered |
| `interpretive_risk` | Allowed, backward-looking caveats added |
| `high_risk_advice` | **Blocked**, refusal returned, LLM not called |
| `unsupported_prediction` | **Blocked**, refusal returned, LLM not called |
| `ambiguous_decision` | Allowed, human-review flag prepended to answer |

---

### 7. EU AI Act risk-tier mapping

**Location:** `src/agent/safety.py`, `docs/eu_ai_act_mapping.md`

Every response carries an `eu_ai_act_tier` field:

| AI Act risk concept | Project interpretation | Control |
|---|---|---|
| Unacceptable risk | Direct financial advice; unsupported predictions | Hard refusal |
| High-risk-style concern | Consequential financial decisions | Human-review flag |
| Transparency risk | User unaware of AI involvement | Visible disclaimer on every page |
| Minimal-risk use | Educational or statistical analysis | Allowed with assumptions shown |

---

### 8. Deployment layer

| Artifact | File | Description |
|---|---|---|
| Docker image | `Dockerfile` | Multi-stage python:3.11-slim; no secrets baked in; HEALTHCHECK |
| Compose | `docker-compose.yml` | Local run; API key from host env; FAISS volume mount |
| Docker ignore | `.dockerignore` | LF-terminated; excludes venv, tests, processed data |
| K8s Deployment | `deployment/kubernetes/deployment.yaml` | 2 replicas; rolling update; resource limits; health probes |
| K8s Service | `deployment/kubernetes/service.yaml` | ClusterIP; port 80 → 8501 |
| K8s Ingress | `deployment/kubernetes/ingress.yaml` | nginx; WebSocket support; HTTPS redirect |
| K8s HPA | `deployment/kubernetes/hpa.yaml` | 2–8 replicas; CPU 70% + memory 80% |
| Azure Container Apps | `deployment/azure/deploy_container_apps.md` | Scale-to-zero; managed TLS; Key Vault secret |
| Azure CLI script | `deployment/azure/azure_cli_commands.sh` | `set -euo pipefail`; API key from env; `az acr build` |
| CI/CD | `.github/workflows/ci.yml` | Test + lint + Docker build on push/PR |

---

## Data flow: end-to-end example

**User asks:** *"What is the annualised volatility of this dataset?"*

```
1. Streamlit captures question, calls run_agent()
2. safety.check() → risk_category=technical_calculation, allowed=True
3. _is_rag_question() → False (pure calculation), RAG skipped
4. set_context() injects price series into tools module
5. LangChain agent invokes calculate_volatility tool
6. Tool calls src/risk/volatility.annualised_volatility()
7. Tool returns {"annualised_volatility_pct": "32.13%", "assumptions": ..., "limitations": ...}
8. Agent formats answer with tool output, assumptions, and limitations
9. annotate_response() adds risk_category, eu_ai_act_tier, confidence_note
10. Streamlit displays answer + tool name + basis + EU AI Act tier
```

**User asks:** *"Should I buy this stock?"*

```
1. Streamlit captures question, calls run_agent()
2. safety.check() → risk_category=high_risk_advice, allowed=False
3. run_agent() returns refusal immediately, LLM is never called
4. Streamlit displays refusal: "I cannot provide direct investment advice..."
5. eu_ai_act_tier = "Unacceptable risk, direct financial advice, blocked"
```

**User asks:** *"What is Expected Shortfall?"*

```
1. Streamlit captures question, calls run_agent()
2. safety.check() → risk_category=safe_educational, allowed=True
3. _is_rag_question() → True
4. retrieve_with_context() retrieves top-3 chunks from risk_methodology.md
5. Chunks prepended to LLM input as context
6. Agent answers using retrieved text (no tool called for definition questions)
7. rag_sources=["risk_methodology"] surfaced in UI with expandable excerpts
```

---

## Limitations

1. **Single-asset analysis.** No portfolio, correlation, or diversification effects.
2. **Backward-looking metrics.** All risk metrics describe past behaviour; none predict future outcomes.
3. **Synthetic sample data.** Does not represent real market conditions. Replace with `yfinance` data for realistic results.
4. **Single-user Streamlit.** Not designed for concurrent multi-user sessions in its current form.
5. **Module-level tool context.** `set_context()` uses module-level state, fine for single-user deployment; would need session isolation in a multi-user setup.
6. **FAISS on disk.** Suitable for a single-node deployment. Replace with Azure AI Search or Pinecone for multi-node or multi-user RAG.
7. **LLM dependency.** Agent requires an LLM API key. Fallback mode provides deterministic risk calculations but no natural language interface.

---

## Production extensions

| Concern | Current approach | Production extension |
|---|---|---|
| LLM provider | the LLM provider the language model | Azure OpenAI (single function change in `_build_agent`) |
| Vector store | FAISS on disk | Azure AI Search / Pinecone |
| Secrets | Env var / Kubernetes Secret | Azure Key Vault + Workload Identity |
| Multi-user sessions | Module-level state | Per-request context passing or session isolation |
| Observability | Streamlit UI trace | LangSmith, Azure Monitor, Application Insights |
| Data source | Static CSV / yfinance | Live market data API (Bloomberg, Refinitiv) via MCP tool |
| Authentication | None | Azure AD / Entra ID |
| Audit logging | Response dict | Append-only audit log per tool call |
| Model evaluation | Manual spot-checks against question bank | Automated evaluation pipeline run on each release |
