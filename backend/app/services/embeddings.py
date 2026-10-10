from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def embed_texts(texts: list) -> list:
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vecs]
