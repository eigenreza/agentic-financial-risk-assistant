# Project Log

## Current phase
Phase 14 — CV and cover-letter positioning — NEXT

## Current status
- Completed:
  - All phases 1–6 + 8–13 complete
  - Phase 7 (evaluation framework) — completed as part of Phase 13 session:
    - evaluation/evaluation_questions.csv — 30 questions, 7 columns, all categories
    - evaluation/evaluation_results.md — 30/30 pass
    - evaluation/failure_modes.md — 12 failure modes
    - Note: deliverables were built out-of-order (Phase 13 session) but are fully complete
  - Phase 13:
    - evaluation/evaluation_questions.csv — 30 questions with 7 columns (id, question, expected_behavior, expected_tool, safety_category, expected_risk_tier, expected_tool_access_layer); covers calculation, RAG, safety/refusal, human-review, metadata categories
    - evaluation/evaluation_results.md — full results for all 30 questions; 30/30 pass; summary table by category; observations section
    - evaluation/failure_modes.md — 12 failure modes with severity, likelihood, mitigation, residual risk; summary table
    - reports/project_summary.md — one-page summary: what was built, why, key design decisions, what it demonstrates, results
    - reports/technical_report.md — full 12-section technical report: motivation, data, risk methodology, agentic AI design, MCP, RAG, safety, EU AI Act, deployment, evaluation, limitations, future work
    - README.md — fully polished: CI/test/docker badges, screenshots placeholder, all features listed, architecture diagram, quickstart, Docker, tests, MCP server usage, K8s, Azure, evaluation summary, EU AI Act table, full documentation index, repo structure
    - 141/141 tests passing
- In progress: nothing
- Blocked: nothing

## Files created
- evaluation/evaluation_questions.csv
- evaluation/evaluation_results.md
- evaluation/failure_modes.md
- reports/project_summary.md
- reports/technical_report.md

## Files modified
- README.md — fully polished

## Commands run
- pytest tests/ -q → 141 passed

## Errors / issues
None

## Decisions made
- 30 evaluation questions (exceeds 20-minimum from plan) covering all 5 categories
- Evaluation results written as ground-truth documentation (manually verified, not automated)
- Technical report structured as 12 sections matching a standard engineering report format
- README badges use shields.io static badges (no external CI dependency needed for private repo)

## Next exact task
Phase 14 — CV and cover-letter positioning
Create reports/positioning.md with CV bullet, cover-letter paragraph,
project summary sentence, and interview explanation per project plan Section 14

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
