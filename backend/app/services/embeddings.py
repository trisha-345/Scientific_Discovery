"""
Lazy-loaded embedding model to keep memory footprint low.

Key behaviors:
- Model loaded on first use, not at import time
- Set to eval mode (no gradients, saves memory)
- Threads limited to 1 to avoid memory spikes
"""
import os
import gc
from typing import List

# Limit thread usage BEFORE torch imports
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_model = None


def _get_model():
    """Load SentenceTransformer once, on first use."""
    global _model
    if _model is None:
        print("[embeddings] Loading model (one-time)...")
        import torch
        torch.set_num_threads(1)
        from sentence_transformers import SentenceTransformer
        from app.config import settings

        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        _model.eval()
        print("[embeddings] Model loaded")
    return _model


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Compute embeddings. Frees memory aggressively after."""
    if not texts:
        return []

    try:
        model = _get_model()
        # Reduce batch size to avoid memory spikes
        vecs = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=8,
            convert_to_numpy=True,
        )
        result = [v.tolist() for v in vecs]
        # Free intermediate memory
        del vecs
        gc.collect()
        return result
    except Exception as e:
        print(f"[embeddings] Error (returning nulls): {e}")
        gc.collect()
        return [None] * len(texts)