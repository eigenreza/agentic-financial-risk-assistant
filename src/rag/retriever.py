"""
RAG retriever: query the FAISS index and return relevant document chunks
with source attribution.
"""

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from src.rag.ingest import build_index, _EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_TOP_K = 3          # number of chunks to return per query
_MIN_SCORE = 0.25   # minimum cosine similarity to include a chunk


@lru_cache(maxsize=1)
def _get_index_and_chunks():
    """Load (or build) index once per process, then cache."""
    return build_index()


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(_EMBEDDING_MODEL)


def retrieve(query: str, top_k: int = _TOP_K, min_score: float = _MIN_SCORE) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a query.

    Returns a list of dicts:
        {
            "source": str,      # document name (e.g. "risk_methodology")
            "text": str,        # chunk text
            "score": float,     # cosine similarity score
        }
    Sorted by score descending. Empty list if no chunks meet min_score.
    """
    index, chunks = _get_index_and_chunks()
    model = _get_model()

    query_vec = model.encode([query], normalize_embeddings=True)
    query_vec = np.array(query_vec, dtype="float32")

    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or float(score) < min_score:
            continue
        chunk = chunks[idx]
        results.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "score": round(float(score), 4),
        })

    return results


def retrieve_with_context(query: str, top_k: int = _TOP_K) -> dict:
    """
    Retrieve chunks and format them as a context block for the agent.

    Returns:
        {
            "context": str,             # formatted text for the LLM
            "sources": list[str],       # unique source document names
            "chunks": list[dict],       # raw retrieval results
            "found": bool,
        }
    """
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "context": "No relevant documentation found for this query.",
            "sources": [],
            "chunks": [],
            "found": False,
        }

    source_labels = {
        "data_readme": "Data Source Documentation",
        "risk_methodology": "Risk Methodology",
        "responsible_ai": "Responsible AI Policy",
        "mcp_architecture": "MCP Architecture",
        "eu_ai_act_mapping": "EU AI Act Mapping",
    }

    lines = ["Relevant documentation:"]
    for i, chunk in enumerate(chunks, 1):
        label = source_labels.get(chunk["source"], chunk["source"])
        lines.append(f"\n[{i}] Source: {label} (score: {chunk['score']:.2f})")
        lines.append(chunk["text"])

    return {
        "context": "\n".join(lines),
        "sources": list(dict.fromkeys(c["source"] for c in chunks)),  # ordered unique
        "chunks": chunks,
        "found": True,
    }


def invalidate_cache() -> None:
    """Clear the in-process cache so the next call reloads the index."""
    _get_index_and_chunks.cache_clear()
    _get_model.cache_clear()
