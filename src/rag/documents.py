"""
Registry of documents available for RAG ingestion.

All paths are relative to the project root. Add new documents here to make
them available to the retriever without changing any other module.
"""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Each entry: (logical_name, file_path, short_description)
RAG_DOCUMENTS: list[tuple[str, Path, str]] = [
    (
        "data_readme",
        _PROJECT_ROOT / "data" / "README.md",
        "Data source documentation: dataset origins, columns, download instructions",
    ),
    (
        "risk_methodology",
        _PROJECT_ROOT / "docs" / "risk_methodology.md",
        "Risk methodology: formulae and definitions for all risk metrics",
    ),
    (
        "responsible_ai",
        _PROJECT_ROOT / "docs" / "responsible_ai.md",
        "Responsible AI policy: safety rules, human-review protocol, limitations",
    ),
    (
        "mcp_architecture",
        _PROJECT_ROOT / "docs" / "mcp_architecture.md",
        "MCP architecture: tool/data access layer design and production extensions",
    ),
]


def get_available_documents() -> list[tuple[str, Path, str]]:
    """Return only documents whose files exist and are non-empty."""
    return [
        (name, path, desc)
        for name, path, desc in RAG_DOCUMENTS
        if path.exists() and path.stat().st_size > 0
    ]
