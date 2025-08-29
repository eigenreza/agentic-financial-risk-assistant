# Azure Architecture

This document describes the Azure deployment architecture for the Agentic Financial Risk Assistant, including how the MCP-style tool/data access layer could connect to enterprise Azure services in a production extension.

---

## Current deployment: Azure Container Apps

```
Internet
    │  HTTPS (Azure-managed TLS)
    ▼
Azure Container Apps (Ingress)
    │
    ▼
Container App: financial-risk-assistant
    │  port 8501 (Streamlit)
    │
    ├── LangChain Agent
    │       │
    │       ├── MCP Tool/Data Access Layer (src/mcp/)
    │       │       └── Risk tools (src/risk/)
    │       │
    │       ├── RAG Retriever (FAISS, sentence-transformers)
    │       │       └── Methodology docs (docs/)
    │       │
    │       └── Safety Layer (src/agent/safety.py)
    │
    └── the LLM API (external, the language model)
            │
            └── Called via HTTPS; API key from Azure Key Vault
```

### Azure services used

| Service | Role |
|---|---|
| Azure Container Apps | Serverless container hosting; built-in HTTPS; scale-to-zero |
| Azure Container Registry (ACR) | Private container image registry |
| Azure Key Vault | Secure storage for `LLM_API_KEY` |
| Azure Log Analytics | Container logs and diagnostics (auto-provisioned) |

---

## Production extension: enterprise agentic AI architecture

The following diagram shows how this prototype would extend to a full enterprise deployment on Azure, incorporating Azure OpenAI, managed identity, AKS, and an MCP gateway pattern.

```
Users / Internal Clients
    │
    ▼
Azure Front Door (global load balancing + WAF)
    │
    ▼
Azure Kubernetes Service (AKS)
    │
    ├── Streamlit App Pod
    │       │
    │       ▼
    │   LangChain Agent
    │       │
    │       ▼
    │   MCP Gateway (src/mcp/server.py → production MCP server)
    │       │
    │       ├── Risk Calculation Tools ──────────────────┐
    │       │                                            │
    │       ├── RAG Retriever                            │
    │       │       └── Azure AI Search (vector store)  │
    │       │                                            │
    │       └── Document Resources                      │
    │               └── Azure Blob Storage              │
    │                                                    │
    ├── Azure OpenAI (GPT-4o / o1) ◄───────────────────┘
    │       └── Replaces the LLM API for enterprise compliance
    │
    ├── Azure Key Vault
    │       └── All secrets via Workload Identity (no env vars in pods)
    │
    ├── Azure Monitor + Application Insights
    │       └── Tool-call traces, latency, error rates, cost tracking
    │
    └── Azure Policy / Defender for Containers
            └── Governance, vulnerability scanning, compliance

```

---

## Key design decisions for enterprise extension

### MCP as a service boundary

In production, the MCP server (`src/mcp/server.py`) would be deployed as a separate container alongside the Streamlit app in the same AKS namespace. The agent connects to it over a private cluster-internal endpoint. This means:

- Risk tools can be updated and redeployed without touching the agent container
- Multiple agents (e.g. a summary agent, a compliance agent, a risk agent) share one tool server
- The MCP layer enforces authentication, agents present a service account token, not raw credentials

### Azure OpenAI instead of the LLM provider

Replacing `the LangChain LLM provider package` with `langchain-openai` and pointing at an Azure OpenAI endpoint requires changing only `_build_agent()` in `langchain_agent.py`:

```python
from langchain_openai import AzureChatOpenAI
llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment="gpt-4o",
    api_version="2024-02-01",
)
```

No other code changes are required. The tool-calling interface is identical.

### Managed identity for secrets

Replace the Key Vault env-var pattern with the Secrets Store CSI Driver:

```yaml
# In deployment.yaml, replaces secretKeyRef
volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: azure-keyvault-provider
```

The pod accesses Key Vault using its AKS Workload Identity, no credentials stored anywhere in the cluster.

### Azure AI Search as vector store

Replace FAISS with Azure AI Search for multi-user, persistent, and scalable RAG:

```python
# In src/rag/retriever.py, swap the FAISS index for Azure AI Search
from langchain_community.vectorstores import AzureSearch
vector_store = AzureSearch(
    azure_search_endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    azure_search_key=os.environ["AZURE_SEARCH_KEY"],
    index_name="risk-methodology-index",
    embedding_function=model.encode,
)
```

Documents are indexed once at deployment time. The index persists independently of the application container.

---

## Cost estimate (production AKS, moderate traffic)

| Component | Approximate monthly cost |
|---|---|
| AKS cluster (2× Standard_D2s_v3 nodes) | ~$140 |
| Azure Container Registry (Basic) | ~$5 |
| Azure Key Vault | ~$1 |
| Azure OpenAI (GPT-4o, ~10k tool-calling requests) | ~$30 |
| Azure AI Search (Basic tier) | ~$75 |
| Azure Monitor / Log Analytics | ~$10 |
| **Total** | **~$260/month** |

Container Apps consumption plan (current prototype): < $10/month at low traffic.

---

## Security controls in production

| Control | Implementation |
|---|---|
| No hardcoded secrets | Key Vault + Workload Identity |
| Private container registry | ACR with private endpoint |
| Network isolation | AKS private cluster + VNet integration |
| Image scanning | Microsoft Defender for Containers |
| TLS everywhere | Azure Front Door managed certificates |
| Audit logging | Azure Monitor diagnostic settings |
| Policy enforcement | Azure Policy + OPA Gatekeeper |
| DDoS protection | Azure DDoS Standard on the Front Door VNet |
