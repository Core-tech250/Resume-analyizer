import math
from typing import List, Set, Tuple
import numpy as np
from scipy.stats import spearmanr, kendalltau

def precision_at_k(system_ranked_ids: List[int], ground_truth_positive_ids: Set[int], k: int = 10) -> float:
    """
    Computes Precision@K: Fraction of top-K system recommendations that are
    in the ground-truth recruiter shortlist.
    """
    if k <= 0 or not system_ranked_ids:
        return 0.0
    top_k = system_ranked_ids[:k]
    hits = sum(1 for cid in top_k if cid in ground_truth_positive_ids)
    return round(float(hits / len(top_k)), 4)

def top_k_agreement(system_top_k: List[int], recruiter_top_k: List[int], k: int = 10) -> float:
    """
    Measures percentage overlap between system's top-K and recruiter's top-K:
    Agreement = |System_TopK ∩ Recruiter_TopK| / K
    """
    if k <= 0 or not system_top_k or not recruiter_top_k:
        return 0.0
    set_sys = set(system_top_k[:k])
    set_rec = set(recruiter_top_k[:k])
    overlap = len(set_sys.intersection(set_rec))
    denom = min(k, len(set_rec))
    return round(float(overlap / denom), 4) if denom > 0 else 0.0

def rank_correlation(system_scores: List[float], recruiter_ranks: List[int]) -> Tuple[float, float]:
    """
    Computes Spearman's rank correlation (rho) and Kendall's tau between system scores
    and ground-truth recruiter ranks.
    Recruiter rank 1 is best, so we invert or correlate negatively with score.
    Returns (spearman_rho, kendall_tau).
    """
    if len(system_scores) < 3 or len(recruiter_ranks) < 3:
        return 0.0, 0.0
    
    # Invert recruiter rank so rank 1 has highest value for positive correlation with score
    max_rank = max(recruiter_ranks) + 1
    recruiter_scores = [max_rank - r for r in recruiter_ranks]

    rho, _ = spearmanr(system_scores, recruiter_scores)
    tau, _ = kendalltau(system_scores, recruiter_scores)

    return (
        round(float(rho), 4) if not math.isnan(rho) else 0.0,
        round(float(tau), 4) if not math.isnan(tau) else 0.0
    )

def keyword_only_score(resume_text: str, required_keywords: List[str]) -> float:
    """
    Naive baseline screener: counts simple word occurrences without synonym handling
    or multi-factor structure.
    """
    if not required_keywords:
        return 0.0
    text_lower = resume_text.lower()
    matches = sum(1 for kw in required_keywords if kw.lower() in text_lower)
    return round(float(matches / len(required_keywords)), 4)
