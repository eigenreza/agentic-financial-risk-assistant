# MCP Architecture

## Why MCP-style tool and data access is included

The Model Context Protocol (MCP) defines a standard interface through which AI agents access tools and data resources. Rather than letting an LLM call arbitrary functions or access raw data directly, MCP enforces a structured boundary:

- The **agent** orchestrates: it decides which tool to call and what to do with the result.
- The **MCP layer** executes: it validates inputs, calls the underlying function, and returns a structured output with metadata.

This separation has concrete production benefits:

| Concern | Without MCP boundary | With MCP boundary |
|---|---|---|
| Auditability | Agent calls are opaque | Every tool call is logged with inputs, outputs, and metadata |
| Safety | LLM can invoke any reachable function | Only explicitly registered tools are callable |
| Versioning | Logic baked into agent prompts | Tools carry version numbers; agent and tools can evolve independently |
| Scalability | Agent and tools run in the same process | MCP server can be deployed as a separate service |
| Multi-agent | One agent, one set of tools | Multiple agents can share the same MCP server |

---

## Project MCP layer: `src/mcp/`

```
src/mcp/
├── __init__.py
├── server.py      # MCP server stub — registers tools and resources
├── tools.py       # Structured wrappers around the risk engine
└── resources.py   # Document resource accessors
```

The layer uses the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`pip install mcp`).

---

## Tools exposed

Each tool accepts a typed input, calls the corresponding function in `src/risk/`, and returns a structured output dict containing:

- `tool` — tool name and version
- `inputs` — echoed input parameters
- `outputs` — computed results with human-readable formatted values
- `metadata` — assumptions, limitations, and observation count

| Tool name | Underlying function | What it computes |
|---|---|---|
| `calculate_volatility` | `src/risk/volatility.py` | Daily and annualised volatility |
| `calculate_drawdown` | `src/risk/drawdown.py` | Maximum drawdown and trough date |
| `calculate_var` | `src/risk/var.py` | Historical or parametric VaR |
| `calculate_expected_shortfall` | `src/risk/var.py` | Expected Shortfall (CVaR) |
| `generate_risk_summary` | All risk modules | Full summary of all key metrics |

---

## Resources exposed

Resources provide read access to local documentation. The agent can retrieve methodology, data-source, and governance documents without hardcoding their content into prompts.

| Resource name | File | Description |
|---|---|---|
| `data_readme` | `data/README.md` | Dataset origins, download steps, cleaning notes |
| `risk_methodology` | `docs/risk_methodology.md` | Formulae and definitions for all risk metrics |
| `responsible_ai` | `docs/responsible_ai.md` | Safety rules, uncertainty handling, human-review protocol |
| `mcp_architecture` | `docs/mcp_architecture.md` | This document |
| `eu_ai_act_mapping` | `docs/eu_ai_act_mapping.md` | EU AI Act risk-tier mapping |

---

## How the server stub works

`src/mcp/server.py` creates an `mcp.server.Server` instance and registers:

1. A `list_tools` handler — returns the tool schemas (name, description, JSON input schema)
2. A `call_tool` handler — routes calls to the appropriate `src/mcp/tools.py` function
3. A `list_resources` handler — returns URIs for all registered documents
4. A `read_resource` handler — reads and returns the content of a named document

In the current prototype the server loads the Equinor sample dataset as the default price series. In production the client would pass a session identifier or a data reference URI.

---

## Separation of concerns

```
Streamlit UI
     │
     ▼
LangChain Agent  ──────────── orchestration
     │
     ▼
MCP Tool/Data Access Layer ── structured boundary
     │                 │
     ▼                 ▼
Risk Tools        Document Resources
(src/risk/)       (docs/, data/)
```

The agent never calls `src/risk/` directly. It calls tools through the MCP layer. The MCP layer is the only component that imports `src/risk/`. This means:

- The risk engine can be tested and versioned independently.
- Tool behaviour can be audited by inspecting the MCP layer alone.
- The LLM cannot bypass the structured interface to access raw data.

---

## How this extends to production

In a production enterprise deployment:

**Replace the stdio stub with a real server process**
```bash
python -m src.mcp.server   # runs over stdio
# or deploy with uvicorn for SSE transport
```

**Multiple agents share one server**
- A summarisation agent, a compliance agent, and a risk agent can all connect to the same MCP server with their own session contexts.

**Connect to enterprise APIs**
- The tool handlers in `src/mcp/server.py` can be pointed at live market data APIs, internal risk databases, or Azure-hosted model endpoints rather than local CSV files — without changing the agent layer at all.

**Secrets and identity management**
- The MCP server can enforce authentication (API keys, managed identity) at the boundary, so agents never hold credentials directly.

**Audit logging**
- Every `call_tool` invocation can be logged centrally for compliance purposes.

**Azure deployment**
- The MCP server can be deployed as an Azure Container App, with the Streamlit agent as a separate container. Both connect over a private virtual network.
- Azure OpenAI can be substituted for the Anthropic LLM by updating only the agent layer.
- Azure Key Vault provides secrets to the MCP server at runtime.
