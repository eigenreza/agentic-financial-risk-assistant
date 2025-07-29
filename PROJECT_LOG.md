# Project Log

## Current phase
Phase 6 — Safety, uncertainty, human-review logic, and EU AI Act mapping — COMPLETE

## Current status
- Completed:
  - Phase 1: skeleton, data, trackers
  - Phase 2: risk engine — 39 tests
  - Phase 3: Streamlit dashboard
  - Phase 4: LangChain agent
  - Phase 4B: MCP layer — 29 tests
  - Phase 5: RAG (FAISS, 4 docs, 54 vectors)
  - Phase 6:
    - src/agent/safety.py — 6 RiskCategory enum values; classify() with priority-ordered keyword rules (educational before technical); check() returning SafetyDecision dataclass; annotate_response(); EU AI Act tier mapping; refusal templates; human-review warning
    - docs/eu_ai_act_mapping.md — full mapping table, 6 risk categories, tier descriptions, blocked examples, answer metadata fields, fallback behaviour, what system is not, production extensions
    - tests/test_safety.py — 38 tests covering classify, check, annotate_response
    - tests/test_eu_ai_act_mapping.py — 35 tests covering all four EU AI Act tiers with parametrize
    - src/agent/langchain_agent.py — safety check wired before LLM call; blocked requests return refusal without calling LLM or tools; allowed requests annotated with safety metadata
    - app/streamlit_app.py — second metadata row: risk_category, eu_ai_act_tier, human_review_required
    - 141/141 tests passing
- In progress: nothing
- Blocked: nothing

## Files created
- src/agent/safety.py
- docs/eu_ai_act_mapping.md
- tests/test_safety.py
- tests/test_eu_ai_act_mapping.py

## Files modified
- src/agent/langchain_agent.py — safety check integrated
- app/streamlit_app.py — safety metadata row added

## Commands run
- .venv\Scripts\pytest tests/test_safety.py tests/test_eu_ai_act_mapping.py -v → 73 passed (after 3 fixes)
- .venv\Scripts\pytest tests/ -q → 141 passed

## Errors / issues
- "Explain the VaR methodology" was classified as TECHNICAL_CALCULATION because technical patterns were checked before educational. Fixed: educational intent now has priority.
- "What is the Value-at-Risk?" ambiguously matches both educational and technical. Fixed test to use unambiguous "Calculate the Value-at-Risk".
- "How much of my retirement fund should I allocate here?" correctly blocked as HIGH_RISK_ADVICE (contains "should i allocate"). Fixed test expectation.

## Decisions made
- Safety check is deterministic Python — runs before LLM is invoked; blocked questions never reach the model
- Educational intent (explain, what is, define) has priority over metric keyword matching in classifier
- Safety metadata always returned in response dict regardless of path (blocked/allowed/no_data)

## Next exact task
Phase 8 — Dockerization (skipping Phase 7 to maintain runnable-core priority per project plan)
Build Dockerfile, docker-compose.yml, test local Docker build.

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
