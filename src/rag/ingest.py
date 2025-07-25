"""
RAG ingestion pipeline: load documents, split into chunks, embed, store in FAISS.

The index is written to data/processed/faiss_index/ and reused across runs.
Call rebuild_index() to force a full rebuild (e.g. after adding new documents).
"""

import json
import logging
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.rag.documents import get_available_documents

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_INDEX_DIR = _PROJECT_ROOT / "data" / "processed" / "faiss_index"
_INDEX_PATH = _INDEX_DIR / "index.faiss"
_CHUNKS_PATH = _INDEX_DIR / "chunks.json"

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_CHUNK_SIZE = 500       # characters per chunk
_CHUNK_OVERLAP = 100    # character overlap between adjacent chunks


def _split_text(text: str, source: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[dict]:
    """Split text into overlapping character-level chunks with source metadata."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({"text": chunk_text, "source": source, "start": start})
        start += chunk_size - overlap
    return chunks


def _load_model() -> SentenceTransformer:
    return SentenceTransformer(_EMBEDDING_MODEL)


def build_index(force_rebuild: bool = False) -> tuple[faiss.Index, list[dict]]:
    """
    Build (or load) the FAISS index from all available RAG documents.

    Returns:
        (faiss_index, chunks) where chunks[i] corresponds to index vector i.
    """
    if not force_rebuild and _INDEX_PATH.exists() and _CHUNKS_PATH.exists():
        logger.info("Loading existing FAISS index from %s", _INDEX_DIR)
        index = faiss.read_index(str(_INDEX_PATH))
        with open(_CHUNKS_PATH, encoding="utf-8") as f:
            chunks = json.load(f)
        return index, chunks

    logger.info("Building FAISS index from source documents")
    _INDEX_DIR.mkdir(parents=True, exist_ok=True)

    docs = get_available_documents()
    if not docs:
        raise RuntimeError("No RAG documents available. Check docs/ and data/ directories.")

    all_chunks: list[dict] = []
    for name, path, _desc in docs:
        text = path.read_text(encoding="utf-8")
        doc_chunks = _split_text(text, source=name)
        all_chunks.extend(doc_chunks)
        logger.info("  %s: %d chunks from %d chars", name, len(doc_chunks), len(text))

    model = _load_model()
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # inner product on normalised vectors = cosine similarity
    index.add(embeddings)

    faiss.write_index(index, str(_INDEX_PATH))
    with open(_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    logger.info("FAISS index built: %d vectors, dim=%d", len(all_chunks), dim)
    return index, all_chunks


def rebuild_index() -> tuple[faiss.Index, list[dict]]:
    """Force a full index rebuild, discarding any cached index."""
    return build_index(force_rebuild=True)
