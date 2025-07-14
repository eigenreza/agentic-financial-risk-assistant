# Project Log

## Current phase
Phase 4 — LangChain agent with controlled Python tools — COMPLETE

## Current status
- Completed:
  - Phase 1: project skeleton, synthetic CSVs, tracker files
  - Phase 2: risk engine — 39 tests passing
  - Phase 3: Streamlit dashboard — confirmed running at localhost:8501
  - Phase 4:
    - src/agent/prompts.py — system prompt (strict rules: no advice, no predictions, tool-first), fallback/no-data message templates
    - src/agent/tools.py — 6 LangChain tools wrapping real risk functions: calculate_returns, calculate_volatility, calculate_drawdown, calculate_var, calculate_expected_shortfall, generate_risk_summary; each returns structured JSON with assumptions and limitations
    - src/agent/langchain_agent.py — ReAct agent using claude-haiku-4-5; set_context() injects prices before each run; run_agent() returns structured dict with answer, tool_calls, basis, error; api_key_available() for fallback detection
    - app/streamlit_app.py — agent panel added below charts: question input, "Run agent" button, answer + tool-calls + basis display; fallback warning shown when no API key
    - All 6 tools verified against real Equinor prices (annualised vol 32.13%, VaR 3.40%, ES 4.21%)
    - 39/39 tests still passing
- In progress: nothing
- Blocked: nothing

## Files created
- src/agent/prompts.py
- src/agent/tools.py
- src/agent/langchain_agent.py

## Files modified
- app/streamlit_app.py — agent panel added

## Commands run
- .venv\Scripts\pip install langchain==0.3.25 langchain-anthropic==0.3.15 langchain-community==0.3.24 anthropic==0.52.0
- .venv\Scripts\python smoke_test_agent.py (all 6 tools OK, fallback mode OK)
- .venv\Scripts\pytest ... → 39 passed

## Errors / issues
None

## Decisions made
- Model: claude-haiku-4-5-20251001 (fast, cost-efficient for tool-calling)
- temperature=0 for deterministic tool selection
- Tool context injected via module-level set_context() before each agent run
- Agent returns structured dict so the UI can display tool calls and basis separately
- Fallback: ui shows warning with setup instructions, dashboard still fully functional

## Next exact task
Phase 4B — Minimal MCP-style tool/data access layer
Build src/mcp/server.py, src/mcp/tools.py, src/mcp/resources.py using official mcp SDK.
Then tests/test_mcp_tools.py and docs/mcp_architecture.md.

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
