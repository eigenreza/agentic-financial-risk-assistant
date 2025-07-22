"""
MCP server stub for the Agentic Financial Risk Assistant.

Uses the official `mcp` Python SDK (pip install mcp) to register risk-analysis
tools and documentation resources. This demonstrates the architectural pattern
of separating agent orchestration from tool/data access via a structured
MCP interface.

In production this server would run as a standalone process and the agent
would connect to it over stdio or SSE. In this prototype it is a runnable
stub that registers tools and resources and can be started for inspection.

Usage:
    python -m src.mcp.server          # starts stdio server (for inspection)
    python src/mcp/server.py          # same
"""

import json
import asyncio
import pandas as pd

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from src.mcp.tools import (
    mcp_calculate_volatility,
    mcp_calculate_drawdown,
    mcp_calculate_var,
    mcp_calculate_expected_shortfall,
    mcp_generate_risk_summary,
)
from src.mcp.resources import read_resource, list_resources
from src.data.sample_data import load_sample

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

app = Server("financial-risk-assistant")

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="calculate_volatility",
            description=(
                "Calculate daily and annualised volatility of the loaded price series. "
                "Volatility is the standard deviation of log returns, annualised by sqrt(252)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "annualise": {
                        "type": "boolean",
                        "description": "If true, return annualised volatility (default: true)",
                        "default": True,
                    }
                },
            },
        ),
        types.Tool(
            name="calculate_drawdown",
            description=(
                "Calculate the maximum drawdown and trough date of the loaded price series. "
                "Drawdown measures peak-to-trough decline: (price - peak) / peak."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="calculate_var",
            description=(
                "Calculate Value-at-Risk (VaR) for the loaded price series. "
                "Returns the maximum daily loss not exceeded at the given confidence level."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level between 0.90 and 0.99 (default: 0.95)",
                        "default": 0.95,
                    },
                    "method": {
                        "type": "string",
                        "enum": ["historical", "parametric"],
                        "description": "VaR method: 'historical' or 'parametric' (default: 'historical')",
                        "default": "historical",
                    },
                },
            },
        ),
        types.Tool(
            name="calculate_expected_shortfall",
            description=(
                "Calculate Expected Shortfall (CVaR) for the loaded price series. "
                "ES is the mean loss in the tail beyond the VaR threshold."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level between 0.90 and 0.99 (default: 0.95)",
                        "default": 0.95,
                    }
                },
            },
        ),
        types.Tool(
            name="generate_risk_summary",
            description=(
                "Generate a full risk summary covering returns, volatility, drawdown, "
                "VaR, and expected shortfall for the loaded price series."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level for VaR/ES (default: 0.95)",
                        "default": 0.95,
                    },
                    "dataset_label": {
                        "type": "string",
                        "description": "Human-readable dataset name for labelling output",
                        "default": "Unknown dataset",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    """Route tool calls to the appropriate risk function."""
    # Load sample data as the default price series for the stub server.
    # In production the client would pass a session ID or data reference.
    prices = load_sample("equinor_stock_sample")["Close"]

    try:
        if name == "calculate_volatility":
            result = mcp_calculate_volatility(prices, annualise=arguments.get("annualise", True))
        elif name == "calculate_drawdown":
            result = mcp_calculate_drawdown(prices)
        elif name == "calculate_var":
            result = mcp_calculate_var(
                prices,
                confidence=arguments.get("confidence", 0.95),
                method=arguments.get("method", "historical"),
            )
        elif name == "calculate_expected_shortfall":
            result = mcp_calculate_expected_shortfall(
                prices, confidence=arguments.get("confidence", 0.95)
            )
        elif name == "generate_risk_summary":
            result = mcp_generate_risk_summary(
                prices,
                confidence=arguments.get("confidence", 0.95),
                dataset_label=arguments.get("dataset_label", "Equinor ASA (EQNR)"),
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e), "tool": name}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ---------------------------------------------------------------------------
# Resource definitions
# ---------------------------------------------------------------------------

@app.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    resources = list_resources()
    return [
        types.Resource(
            uri=f"file://{r['uri']}",
            name=r["name"],
            description=r["description"],
            mimeType="text/markdown",
        )
        for r in resources
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    # Map URI back to resource name
    name = uri.replace("file://", "").replace("\\", "/")
    # Match by URI suffix
    resources = list_resources()
    for r in resources:
        if r["uri"].replace("\\", "/") in name:
            payload = read_resource(r["name"])
            if payload["available"]:
                return payload["content"]
            return f"Resource not yet available: {payload['error']}"
    return f"Resource not found for URI: {uri}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_run())
