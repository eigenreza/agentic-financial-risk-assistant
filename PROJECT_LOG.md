# Project Log

## Current phase
Phase 11 — CI/CD — COMPLETE

## Current status
- Completed:
  - Phases 1–6: full runnable core
  - Phase 8: Docker (confirmed working)
  - Phase 9: Kubernetes manifests
  - Phase 10: Azure deployment documentation
  - Phase 11:
    - .github/workflows/ci.yml — two-job workflow:
      1. test: Python 3.11, pip cache, ruff lint (continue-on-error), pytest -v
      2. docker: depends on test, Docker Buildx, build-push-action (push=false), GHA layer cache
    - YAML validated (10/10 structural checks pass)
    - 141/141 tests passing
- In progress: nothing
- Blocked: nothing

## Files created
- .github/workflows/ci.yml

## Files modified
None

## Commands run
- validate_ci.py (10 checks, all pass)
- pytest tests/ -q → 141 passed

## Errors / issues
- yaml.safe_load parses the 'on' key as Python True in some versions — handled with .get(True) fallback in validation script

## Decisions made
- Two separate jobs (test + docker) so Docker build only runs when tests pass
- ruff lint uses continue-on-error=true — warnings visible in GHA UI but don't block merge
- Docker job uses GHA layer cache (type=gha) for faster rebuilds
- push: false — CI only validates the build, never pushes to a registry

## Next exact task
Phase 12 — Architecture documentation
docs/architecture.md — full system architecture document with all layers, diagrams, tables

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
