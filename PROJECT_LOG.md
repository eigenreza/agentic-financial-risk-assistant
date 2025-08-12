# Project Log

## Current phase
Phase 10 — Azure deployment documentation — COMPLETE

## Current status
- Completed:
  - Phases 1–6: full runnable core
  - Phase 8: Docker (confirmed working)
  - Phase 9: Kubernetes manifests (YAML validated)
  - Phase 10:
    - deployment/azure/deploy_container_apps.md — step-by-step Container Apps deployment; required services; variables; resource group → ACR → Key Vault → environment → app; scaling config; update/rollback; log streaming; cleanup; production hardening checklist
    - deployment/azure/azure_cli_commands.sh — full executable script with set -euo pipefail; ANTHROPIC_API_KEY from env (never hardcoded); az acr build from project root; Key Vault secret storage; containerapp create; URL retrieval; cleanup; 9/9 safety checks pass
    - deployment/azure/architecture_azure.md — current Container Apps architecture diagram; enterprise extension diagram (AKS + Azure OpenAI + Azure AI Search + Key Vault + Workload Identity + Front Door + Monitor + Policy); Azure OpenAI swap code; managed identity pattern; cost estimate; security controls table
    - deployment/azure/aks_extension_note.md — step-by-step AKS deployment; ACR attachment; Secrets Store CSI Driver; Azure Monitor add-on; cluster autoscaler; manifest-to-AKS mapping table; teardown
    - 141/141 tests still passing
- In progress: nothing
- Blocked: nothing

## Files created
- deployment/azure/deploy_container_apps.md
- deployment/azure/azure_cli_commands.sh
- deployment/azure/architecture_azure.md
- deployment/azure/aks_extension_note.md

## Files modified
None

## Commands run
- Shell script structural validation (9 checks, all pass)
- pytest tests/ -q → 141 passed

## Errors / issues
None

## Decisions made
- Container Apps as preferred Azure path (serverless, scale-to-zero, no node management)
- AKS documented as separate path for enterprise/production (maps directly to K8s manifests)
- API key read from environment variable in script, stored in Key Vault — never appears in script or logs
- Azure OpenAI swap documented as single-function change (only _build_agent() needs updating)
- az acr build used instead of local docker build+push (works without Docker Desktop installed)

## Next exact task
Phase 11 — CI/CD
.github/workflows/ci.yml — install deps, run tests, optional linting, optional Docker build

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
