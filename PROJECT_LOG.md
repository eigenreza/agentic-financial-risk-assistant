# Project Log

## Current phase
Phase 14 — CV and cover-letter positioning — COMPLETE

## Current status
- Completed: ALL PHASES (1–6, 7, 8–14)
  - Phase 1: project skeleton, synthetic CSVs, tracker files
  - Phase 2: risk engine — 39 tests (returns, vol, drawdown, VaR, ES, rolling)
  - Phase 3: Streamlit dashboard (sidebar, risk summary, charts, file upload)
  - Phase 4: LangChain agent (claude-haiku-4-5, tool-calling, fallback mode)
  - Phase 4B: MCP layer (5 tools, 5 resources, server stub) — 29 tests
  - Phase 5: RAG (FAISS, all-MiniLM-L6-v2, 4 docs, 54 vectors, citations in UI)
  - Phase 6: Safety + EU AI Act mapping — 73 tests
  - Phase 7: Evaluation framework (30 questions, 30/30 pass, 12 failure modes)
  - Phase 8: Docker (multi-stage, confirmed working)
  - Phase 9: Kubernetes manifests (Deployment, Service, Ingress, HPA)
  - Phase 10: Azure deployment docs (Container Apps, AKS, CLI script, architecture)
  - Phase 11: GitHub Actions CI (test + lint + Docker build)
  - Phase 12: Architecture documentation (8 layers, diagrams, data-flow examples)
  - Phase 13: README polished, technical report, project summary
  - Phase 14: CV bullet, skills section, cover-letter paragraph, interview explanation, Equinor positioning notes, publication checklist
  - 141/141 tests passing
- In progress: nothing
- Blocked: nothing

## Files created (Phase 14)
- reports/positioning.md

## Files modified
None

## Commands run
None (documentation-only phase)

## Errors / issues
None

## Decisions made
- Positioning notes include a dedicated Equinor section explaining why those specific datasets were chosen and why the responsible AI / EU Act layer is relevant to the role
- Publication checklist embedded in positioning.md so it is easy to find before making repo public
- Only two items remaining before publication: screenshots and updating status badge

## Publication status
READY except:
- [ ] Add screenshots to docs/screenshots/
- [ ] Update README status badge from "in development" to "complete"

## Next exact task
Take screenshots of the running app, add to docs/screenshots/, update README badge,
then make the repository public.

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. All 14 phases complete. 141 tests passing. Remaining: screenshots + status badge + make repo public.
