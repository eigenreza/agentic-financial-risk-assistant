"""
MCP-style resource accessors for methodology and data-source documents.

Resources expose local markdown documents as structured text payloads.
In a production MCP server these would be registered as resource URIs;
here they are callable Python functions that return the same structured format.
"""

from pathlib import Path

# Project root relative to this file: src/mcp/ -> project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent

_RESOURCE_REGISTRY: dict[str, Path] = {
    "data_readme":         _PROJECT_ROOT / "data" / "README.md",
    "risk_methodology":    _PROJECT_ROOT / "docs" / "risk_methodology.md",
    "responsible_ai":      _PROJECT_ROOT / "docs" / "responsible_ai.md",
    "mcp_architecture":    _PROJECT_ROOT / "docs" / "mcp_architecture.md",
    "eu_ai_act_mapping":   _PROJECT_ROOT / "docs" / "eu_ai_act_mapping.md",
}

_RESOURCE_DESCRIPTIONS: dict[str, str] = {
    "data_readme":      "Data source documentation: dataset origins, download instructions, cleaning steps",
    "risk_methodology": "Risk methodology: definitions and formulae for all risk metrics",
    "responsible_ai":   "Responsible AI policy: safety rules, uncertainty handling, human-review protocol",
    "mcp_architecture": "MCP architecture: how the tool/data access layer is structured",
    "eu_ai_act_mapping":"EU AI Act risk-tier mapping: how the system maps to AI governance tiers",
}


def read_resource(name: str) -> dict:
    """
    Return a structured resource payload for the named document.

    Returns:
        {
            "resource": str,          # resource name
            "uri": str,               # relative file path
            "description": str,
            "content": str,           # full text content
            "available": bool,
            "error": str | None,
        }
    """
    if name not in _RESOURCE_REGISTRY:
        return {
            "resource": name,
            "uri": None,
            "description": None,
            "content": None,
            "available": False,
            "error": (
                f"Unknown resource: '{name}'. "
                f"Available: {list(_RESOURCE_REGISTRY.keys())}"
            ),
        }

    path = _RESOURCE_REGISTRY[name]
    description = _RESOURCE_DESCRIPTIONS[name]

    if not path.exists() or path.stat().st_size == 0:
        return {
            "resource": name,
            "uri": str(path.relative_to(_PROJECT_ROOT)),
            "description": description,
            "content": None,
            "available": False,
            "error": f"Document not yet written: {path.relative_to(_PROJECT_ROOT)}",
        }

    content = path.read_text(encoding="utf-8")
    return {
        "resource": name,
        "uri": str(path.relative_to(_PROJECT_ROOT)),
        "description": description,
        "content": content,
        "available": True,
        "error": None,
    }


def list_resources() -> list[dict]:
    """Return a summary of all registered resources and their availability."""
    return [
        {
            "name": name,
            "uri": str(_RESOURCE_REGISTRY[name].relative_to(_PROJECT_ROOT)),
            "description": _RESOURCE_DESCRIPTIONS[name],
            "available": (
                _RESOURCE_REGISTRY[name].exists()
                and _RESOURCE_REGISTRY[name].stat().st_size > 0
            ),
        }
        for name in _RESOURCE_REGISTRY
    ]
