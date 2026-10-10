"""
Lightweight stub — no ML model loaded.
Keeps the same API surface so nothing else breaks.

Why: Render free tier has 512 MB RAM. torch + sentence-transformers
uses ~500 MB by itself, causing OOM. We removed them; gap detection
now uses keyword-based logic in semantic_gaps.py.
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
    """Simple word-based chunking. No ML involved."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def embed_texts(texts: List[str]) -> List:
    """No-op — returns None placeholders. Kept for API compatibility."""
    return [None] * len(texts)
