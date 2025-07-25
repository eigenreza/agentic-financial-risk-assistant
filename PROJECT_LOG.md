# Project Log

## Current phase
Phase 5 — RAG over methodology documents — COMPLETE

## Current status
- Completed:
  - Phase 1: skeleton, data, trackers
  - Phase 2: risk engine — 39 tests
  - Phase 3: Streamlit dashboard
  - Phase 4: LangChain agent (claude-haiku-4-5, tool-calling, fallback)
  - Phase 4B: MCP layer (5 tools, 5 resources, server stub) — 29 tests
  - Phase 5:
    - docs/risk_methodology.md — full methodology doc (returns, vol, drawdown, VaR, ES, rolling, caveats)
    - docs/responsible_ai.md — responsible AI policy (safety rules, metadata fields, human-review, EU AI Act alignment, limitations)
    - src/rag/documents.py — document registry (4 docs: data_readme, risk_methodology, responsible_ai, mcp_architecture)
    - src/rag/ingest.py — FAISS ingestion pipeline (character chunking, all-MiniLM-L6-v2, IndexFlatIP/cosine, persistent index)
    - src/rag/retriever.py — retriever with lru_cache, retrieve() and retrieve_with_context() returning source-attributed chunks
    - src/agent/langchain_agent.py — RAG integrated: _is_rag_question() keyword routing, retrieve_with_context() prepended to input, rag_sources/rag_chunks in response dict, basis field updated (mixed/rag/calculation)
    - app/streamlit_app.py — citations panel: 3-column metadata row (basis/tools/documents), expandable retrieved document excerpts
    - Index built: 54 vectors from 4 documents, dim=384
    - Retrieval verified: VaR→risk_methodology, data source→data_readme, safety→responsible_ai, MCP→mcp_architecture
    - 68/68 tests still passing
- In progress: nothing
- Blocked: nothing

## Files created
- docs/risk_methodology.md
- docs/responsible_ai.md
- src/rag/documents.py
- src/rag/ingest.py
- src/rag/retriever.py
- data/processed/faiss_index/index.faiss (generated at runtime)
- data/processed/faiss_index/chunks.json (generated at runtime)

## Files modified
- src/agent/langchain_agent.py — RAG wired in, response dict extended
- app/streamlit_app.py — citations panel added

## Commands run
- .venv\Scripts\pip install faiss-cpu==1.9.0 sentence-transformers==3.4.1
- .venv\Scripts\python smoke_rag.py (all 4 queries retrieved correct sources)
- .venv\Scripts\pytest tests/ -q → 68 passed

## Errors / issues
- FAISS AVX512 warning (harmless, falls back to AVX2)
- HuggingFace symlinks warning on Windows (harmless, cache still works)

## Decisions made
- all-MiniLM-L6-v2 embedding model (fast, 384-dim, well-suited for short technical passages)
- IndexFlatIP with normalised embeddings = cosine similarity (exact search, appropriate for 54 vectors)
- Persistent index in data/processed/faiss_index/ (rebuilt only when documents change)
- RAG triggered by keyword matching (_is_rag_question) — avoids unnecessary retrieval on pure calculation questions
- data/processed/ and faiss_index/ added to .gitignore (regenerated at runtime)

## Next exact task
Phase 6 — Safety, uncertainty, human-review logic, and EU AI Act mapping
Build src/agent/safety.py, docs/eu_ai_act_mapping.md, tests/test_safety.py, tests/test_eu_ai_act_mapping.py

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
