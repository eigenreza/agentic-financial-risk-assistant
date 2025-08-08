# Project Log

## Current phase
Phase 9 — Kubernetes manifests — COMPLETE

## Current status
- Completed:
  - Phases 1–6: full runnable core
  - Phase 8: Docker (build and run confirmed working)
  - Phase 9:
    - deployment/kubernetes/deployment.yaml — 2-replica Deployment; rolling update; resource limits (250m–1000m CPU, 512Mi–1Gi RAM); liveness + readiness probes on /_stcore/health; ANTHROPIC_API_KEY from Secret (optional); emptyDir for FAISS index (PVC note included); topology spread; non-root security context
    - deployment/kubernetes/service.yaml — ClusterIP; port 80 → 8501
    - deployment/kubernetes/ingress.yaml — nginx Ingress; WebSocket support for Streamlit; HTTPS redirect; TLS via cert-manager (commented); placeholder domain
    - deployment/kubernetes/hpa.yaml — autoscaling/v2 HPA; 2–8 replicas; CPU 70% + memory 80% targets; scale-up 2 pods/min; scale-down 1 pod/2min with 5min stabilisation window
    - deployment/kubernetes/README.md — prerequisites, quick-start (build/push/secret/apply), HPA checking, teardown, AKS mapping table, production extensions
    - YAML syntax validated on all 4 manifests (yaml.safe_load, all OK)
    - 141/141 tests still passing
- In progress: nothing
- Blocked: nothing

## Files created
- deployment/kubernetes/deployment.yaml
- deployment/kubernetes/service.yaml
- deployment/kubernetes/ingress.yaml
- deployment/kubernetes/hpa.yaml
- deployment/kubernetes/README.md

## Files modified
None

## Commands run
- yaml.safe_load validation on all 4 manifests → all OK
- pytest tests/ -q → 141 passed

## Errors / issues
None

## Decisions made
- autoscaling/v2 (not deprecated v1) for HPA
- ClusterIP service (not LoadBalancer) — external traffic enters via Ingress only
- WebSocket proxy headers in Ingress annotations — required for Streamlit's SSE/WS live updates
- emptyDir for FAISS volume with clear production upgrade note (PVC)
- optional: true on Secret ref so app runs in fallback mode if key is absent

## Next exact task
Phase 10 — Azure deployment documentation
deployment/azure/deploy_container_apps.md, azure_cli_commands.sh, architecture_azure.md, aks_extension_note.md

## Handoff prompt for next Claude Code session
Read PROJECT_LOG.md and tell me where we left off. This is the Agentic Financial Risk Assistant project — a production-style agentic AI prototype using Python risk tools, LangChain, MCP-style tool/data access (official mcp SDK), RAG, safety guardrails, EU AI Act risk-tier mapping, Docker, Kubernetes, Azure, and CI/CD. Static CSV-first data approach using Equinor stock, Brent crude, USD/NOK, S&P 500, and VIX. Repo is private until polished. Do not rewrite completed parts unless a test fails. Focus on the next exact task only.
