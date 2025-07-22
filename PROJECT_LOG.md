# Project Log

## Current phase
Phase 4B — MCP-style tool/data access layer — COMPLETE

## Current status
- Completed:
  - Phase 1: project skeleton, synthetic CSVs, tracker files
  - Phase 2: risk engine — 39 tests
  - Phase 3: Streamlit dashboard
  - Phase 4: LangChain agent (claude-haiku-4-5, tool-calling, fallback mode)
  - Phase 4B:
    - src/mcp/tools.py — 5 structured tool wrappers (volatility, drawdown, VaR, ES, risk summary); each returns typed output dict with inputs, outputs, metadata (assumptions, limitations, observations_used)
    - src/mcp/resources.py — resource registry for 5 documents (data/README.md, risk_methodology.md, responsible_ai.md, mcp_architecture.md, eu_ai_act_mapping.md); read_resource() and list_resources()
    - src/mcp/server.py — official mcp SDK Server; registers all 5 tools and 5 resources; handle_list_tools, handle_call_tool, handle_list_resources, handle_read_resource; runnable via stdio
    - tests/test_mcp_tools.py — 29 tests across all 5 tools and resource layer; all pass
    - docs/mcp_architecture.md — full architecture document covering rationale, tool/resource tables, separation-of-concerns diagram, production extension paths
    - 68/68 tests passing (39 Phase 2 + 29 Phase 4B)
- In progress: nothing
- Blocked: nothing

## Files created
- src/mcp/tools.py
- src/mcp/resources.py
- src/mcp/server.py
- tests/test_mcp_tools.py
- docs/mcp_architecture.md

## Files modified
None beyond Phase 4B files

## Commands run
- .venv\Scripts\pip install mcp==1.9.0
- .venv\Scripts\pytest tests/test_mcp_tools.py -v → 29 passed
- .venv\Scripts\pytest tests/ -q → 68 passed

## Errors / issues
None

## Decisions made
- MCP tools call src/risk/ directly (not via LangChain tools) — clean separation of layers
- Server stub uses Equinor sample data as default price series; production would use session reference
- Resources are keyed by logical name (e.g. "data_readme") not raw file path — decouples client from file layout
- docs/mcp_architecture.md included in resource registry so the agent can retrieve it via RAG (Phase 5)

## Next exact task
Phase 5 — RAG over methodology documents
Build src/rag/ingest.py, src/rag/retriever.py, src/rag/documents.py
Create docs/risk_methodology.md and docs/responsible_ai.md
Connect RAG to agent for methodology/data-source questions
Show citations in Streamlit app

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
