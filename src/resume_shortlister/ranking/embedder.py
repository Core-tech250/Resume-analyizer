import logging
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from src.resume_shortlister.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _st_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.use_fallback = settings.USE_TFIDF_FALLBACK

    def _load_st_model(self):
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading sentence-transformers model: {self.model_name}...")
                self._st_model = SentenceTransformer(self.model_name)
                logger.info("SentenceTransformer model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer ({e}). Falling back to TF-IDF.")
                self._st_model = None
        return self._st_model

    def compute_similarity_transformer(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """
        Embeds texts using SentenceTransformer and calculates cosine similarities.
        """
        model = self._load_st_model()
        if model is None:
            logger.warning("SentenceTransformer unavailable. Falling back to TF-IDF.")
            return self.compute_similarity_tfidf(query_text, candidate_texts)

        # Batch encode all texts together
        all_texts = [query_text] + candidate_texts
        embeddings = model.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)

        query_emb = embeddings[0]
        candidate_embs = embeddings[1:]

        # Since normalize_embeddings=True, cosine similarity is simply the dot product
        similarities = np.dot(candidate_embs, query_emb)
        return [float(np.clip(s, 0.0, 1.0)) for s in similarities]

    def compute_similarity_tfidf(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """
        Fast, zero-download TF-IDF baseline similarity.
        """
        corpus = [query_text] + candidate_texts
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vec = tfidf_matrix[0]
        candidate_vecs = tfidf_matrix[1:]

        # Cosine similarity between sparse vectors
        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(candidate_vecs, query_vec).flatten()
        return [float(np.clip(s, 0.0, 1.0)) for s in sims]

    def rank_texts(self, query_text: str, candidate_texts: List[str], engine: str = "transformer") -> List[float]:
        """
        Calculates similarity scores using the requested engine ("transformer" or "tfidf").
        """
        if not candidate_texts:
            return []
        if engine.lower() == "tfidf":
            return self.compute_similarity_tfidf(query_text, candidate_texts)
        return self.compute_similarity_transformer(query_text, candidate_texts)

embedding_service = EmbeddingService()
