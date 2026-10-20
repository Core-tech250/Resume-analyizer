import numpy as np

def cosine_similarity_1d(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Computes cosine similarity between two 1D vectors.
    Returns float in range [0.0, 1.0].
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
    # Clip to [0.0, 1.0] for normalized cosine similarity
    return float(np.clip(sim, 0.0, 1.0))

def cosine_similarity_matrix(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """
    Computes cosine similarity between a 1D query vector and a 2D document matrix.
    doc_matrix shape: (N, D), query_vec shape: (D,)
    """
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0.0:
        return np.zeros(doc_matrix.shape[0])
    
    doc_norms = np.linalg.norm(doc_matrix, axis=1)
    doc_norms[doc_norms == 0.0] = 1.0  # avoid division by zero
    
    dots = np.dot(doc_matrix, query_vec)
    sims = dots / (doc_norms * query_norm)
    return np.clip(sims, 0.0, 1.0)
