import hashlib
from typing import Dict, Optional, List
import numpy as np

class EmbeddingCache:
    """
    In-memory and persistent vector embedding cache.
    Caches computed vector embeddings keyed by SHA-256 hash of text.
    """
    def __init__(self):
        self._cache: Dict[str, np.ndarray] = {}
        self.hits = 0
        self.misses = 0

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        h = self._hash_text(text)
        if h in self._cache:
            self.hits += 1
            return self._cache[h]
        self.misses += 1
        return None

    def put(self, text: str, embedding: np.ndarray):
        h = self._hash_text(text)
        self._cache[h] = embedding

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round((self.hits / total) * 100, 1) if total > 0 else 0.0

embedding_cache = EmbeddingCache()
