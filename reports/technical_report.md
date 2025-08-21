# Technical Report

## Agentic Financial Risk Assistant

**Version:** 1.0
**Date:** 2026-05-31
**Author:** Portfolio project — eigenreza

---

## 1. Motivation

General-purpose large language models are not fit for direct use in financial risk analysis. They hallucinate numerical results, provide unsupported investment advice, make predictions without grounding, and do not disclose assumptions or limitations. These are not prompt-engineering failures — they are architectural failures. The solution is to constrain the LLM's role to orchestration only, and to route all computation, retrieval, and safety decisions through purpose-built deterministic layers.

This project builds a production-style prototype that demonstrates this architecture. It is grounded in prior research experience in stochastic modelling, uncertainty quantification, and financial risk, and translated into an agentic AI engineering context.

---

## 2. Data sources

Five synthetic financial time-series datasets were generated using Geometric Brownian Motion (GBM) with asset-specific drift and volatility parameters calibrated to approximate real-world statistical properties:

| Asset | Symbol | Parameters |
|---|---|---|
| Equinor ASA | EQNR | μ=6%, σ=32%, S₀=18.50 |
| Brent crude oil | BZ=F | μ=2%, σ=30%, S₀=68.00 |
| USD/NOK exchange rate | USDNOK=X | μ=1%, σ=8%, S₀=8.10 |
| S&P 500 index | ^GSPC | μ=10%, σ=18%, S₀=2700 |
| VIX volatility index | ^VIX | μ=0%, σ=55%, S₀=17.0 |

All series cover 2018-01-02 to 2024-12-31 (1,826 business days), use a fixed random seed (42) for reproducibility, and pass the data validation pipeline. Real data can be substituted via `yfinance` with no code changes.

---

## 3. Risk methodology

All metrics are computed from daily closing prices using the functions in `src/risk/`.

**Returns:** Simple returns `r_t = (P_t - P_{t-1}) / P_{t-1}` are used for VaR and ES. Log returns `r_t = ln(P_t / P_{t-1})` are used for volatility (they are time-additive and better approximate normality).

**Volatility:** Standard deviation of log returns, annualised by `sqrt(252)`. Rolling volatility uses a 21-day window by default.

**Drawdown:** `DD_t = (P_t - max(P_1..P_t)) / max(P_1..P_t)`. Maximum drawdown is `min(DD_t)` over the full period.

**Value-at-Risk:** Two methods implemented:
- *Historical simulation:* `-percentile(r, (1-confidence)×100)` — no distributional assumption
- *Parametric Gaussian:* `-(μ - z×σ)` where `z = Φ⁻¹(confidence)` — assumes normality

**Expected Shortfall (CVaR):** Mean of returns in the tail beyond the VaR threshold: `-mean(r | r ≤ -VaR)`. ES is always ≥ VaR and provides a more complete picture of tail risk.

**Limitations:** All metrics are backward-looking. Financial returns exhibit fat tails, volatility clustering, and regime changes that violate the assumptions of Gaussian VaR. These limitations are stated explicitly in every tool output and retrieved from `docs/risk_methodology.md` when users ask educational questions.

---

## 4. Agentic AI design

The agent is a LangChain `create_tool_calling_agent` using `claude-haiku-4-5` at temperature=0. The ReAct pattern is used: the model receives the user question with an explicit dataset context prefix, selects a tool (or retrieves from documents), receives the structured result, and formats the answer.

**Tools:** Six `@tool`-decorated functions in `src/agent/tools.py`. Each calls a function in `src/risk/` and returns a structured JSON dict with `outputs` (computed values) and `metadata` (assumptions, limitations, observation count). The tools access the price series through module-level context set by `set_context()` before each agent run.

**Key prompt design decisions:**
- Explicit statement that data is pre-loaded (prevents "please upload data" responses)
- Dataset name and observation count prepended to every user message (provides concrete context)
- Tool-first instruction (prevents LLM from inventing numbers)
- Tool names and structured format requirements in the system prompt

---

## 5. MCP-style tool/data access layer

The `src/mcp/` layer provides a structured boundary between agent orchestration and tool execution using the official `mcp` Python SDK (v1.9.0). The `mcp.server.Server` instance registers five tools and five resource accessors with full JSON input schemas and metadata.

**Why this matters architecturally:** In production, the MCP server would run as a separate process. The agent connects to it over stdio or SSE. This means:
- Tools can be updated independently of the agent
- Multiple agents can share one tool server
- The agent cannot call arbitrary Python functions — only registered wrappers
- Every tool call is auditable at the MCP layer

The current prototype runs the MCP server in-process, but the design is production-ready for separation.

---

## 6. RAG design

Retrieval-Augmented Generation is used for educational and methodology questions. The pipeline:

1. **Ingestion:** Four markdown documents are split into 500-character overlapping chunks (100-char overlap). Each chunk is embedded using `all-MiniLM-L6-v2` (384-dimensional, fast, well-suited for technical passages).

2. **Index:** FAISS `IndexFlatIP` with L2-normalised embeddings — equivalent to cosine similarity. Exact search is appropriate at this scale (54 vectors).

3. **Retrieval:** `retrieve_with_context()` returns top-3 chunks above a 0.25 cosine similarity threshold. Results include source document name and similarity score.

4. **Routing:** A Python keyword function (`_is_rag_question`) checks whether the question contains educational intent keywords (explain, what is, define, methodology, data source, etc.) before invoking the retriever. Pure calculation questions skip RAG entirely.

5. **Citation:** Retrieved source names and expandable document excerpts are shown in the Streamlit UI.

---

## 7. Safety architecture

The safety layer (`src/agent/safety.py`) makes all safety decisions deterministically in Python before the LLM is invoked. The classifier uses priority-ordered keyword matching:

1. Investment advice patterns → `HIGH_RISK_ADVICE` → blocked
2. Prediction patterns → `UNSUPPORTED_PREDICTION` → blocked
3. Consequential decision patterns → `AMBIGUOUS_DECISION` → allowed with human-review flag
4. Educational intent keywords → `SAFE_EDUCATIONAL` → allowed
5. Metric keywords → `TECHNICAL_CALCULATION` → allowed
6. Default → `INTERPRETIVE_RISK` → allowed with caveats

Blocked requests return a structured refusal dict. The LLM is never called. This is verified by 73 tests covering all category boundaries.

`annotate_response()` then merges safety metadata (`risk_category`, `human_review_required`, `eu_ai_act_tier`, `confidence_note`) into every response dict, regardless of whether the LLM was called.

---

## 8. EU AI Act mapping

The system applies an EU AI Act-inspired risk-tier framework documented in `docs/eu_ai_act_mapping.md` and enforced in `src/agent/safety.py`:

| Tier | Trigger | Control |
|---|---|---|
| Unacceptable risk | Direct investment advice; unsupported predictions | Hard refusal, no LLM call |
| High-risk-style concern | Consequential financial decision support | Human-review warning |
| Transparency | AI involvement in answer generation | Basis field + visible disclaimer |
| Minimal risk | Educational analysis; tool-based calculation | Allowed with assumptions |

This framework is not regulatory compliance — it is a demonstration of the kind of governance thinking applicable in regulated industry contexts.

---

## 9. Deployment

**Docker:** Multi-stage python:3.11-slim image. API key passed at runtime via `-e`. FAISS index mounted as a volume. HEALTHCHECK on `/_stcore/health`.

**Kubernetes:** Deployment (2 replicas, rolling update, resource limits), ClusterIP Service, nginx Ingress (WebSocket support for Streamlit), HPA (2–8 replicas, CPU 70% + memory 80%). Manifests apply to AKS without modification.

**Azure:** Container Apps (preferred — serverless, scale-to-zero, managed TLS). AKS documented as enterprise path. Azure CLI deployment script with `set -euo pipefail`, API key from env only, `az acr build` (no local Docker required).

**CI/CD:** GitHub Actions two-job pipeline — `test` (Python 3.11, pip cache, ruff, pytest) and `docker` (Buildx, no push, GHA layer cache). Docker job runs only when tests pass.

---

## 10. Evaluation

30 evaluation questions across 5 categories were evaluated manually against the Equinor synthetic sample:

| Category | Questions | Pass rate |
|---|---|---|
| Technical calculation | 10 | 100% |
| Educational / RAG | 10 | 100% |
| Safety / refusal | 6 | 100% |
| Human review | 1 | 100% |
| Metadata / transparency | 3 | 100% |
| **Total** | **30** | **100%** |

Key observations: tool calls were made for all calculation questions without exception; all safety refusals fired correctly without reaching the LLM; RAG retrieved the correct source document for all educational questions.

---

## 11. Limitations

1. Single-asset, backward-looking analysis only
2. Synthetic sample data does not represent real market conditions
3. Gaussian VaR assumption understates fat-tail risk
4. Module-level tool context requires single-user deployment
5. FAISS in-process index is not suitable for concurrent multi-user RAG
6. Safety classifier uses keyword matching — adversarial phrasing may bypass it
7. No live market data integration

---

## 12. Future work

- Replace FAISS with Azure AI Search for persistent, scalable, multi-user RAG
- Add yfinance live data loader with caching
- Replace Anthropic API with Azure OpenAI for enterprise compliance
- Add session isolation for multi-user deployment
- Add LangSmith tracing for production observability
- Extend safety classifier with a fine-tuned intent classifier
- Add portfolio-level risk analysis (correlation, diversification)
- Implement Phase 7 automated evaluation pipeline
