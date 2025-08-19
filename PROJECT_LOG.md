# Project Log

## Current phase
Phase 12 — Architecture documentation — COMPLETE

## Current status
- Completed:
  - Phases 1–6: full runnable core
  - Phase 8: Docker
  - Phase 9: Kubernetes manifests
  - Phase 10: Azure deployment documentation
  - Phase 11: GitHub Actions CI
  - Phase 12:
    - docs/architecture.md — full system architecture document:
      - ASCII system diagram showing all layers and data flow
      - Layer descriptions for all 8 layers (data, analytics, agent, MCP, RAG, safety, EU AI Act, deployment)
      - Component tables (file, purpose) for each layer
      - End-to-end data flow for 3 example questions
      - Limitations section (7 items)
      - Production extensions table (8 concerns)
      - EU AI Act risk-tier mapping table
    - 141/141 tests passing
- In progress: nothing
- Blocked: nothing

## Files created
- docs/architecture.md

## Files modified
None

## Commands run
- pytest tests/ -q → 141 passed

## Errors / issues
None

## Decisions made
- Architecture doc written as a living reference that mirrors the actual code structure (no aspirational features)
- Three end-to-end examples chosen to illustrate calculation, safety-block, and RAG paths

## Next exact task
Phase 13 — Final README, evaluation framework, and reports
- Evaluation framework (evaluation/evaluation_questions.csv, evaluation_results.md, failure_modes.md)
- Polish README.md with screenshots placeholder, quickstart, all feature sections
- reports/project_summary.md and reports/technical_report.md

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
