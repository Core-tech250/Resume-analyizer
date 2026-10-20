import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from src.resume_shortlister.db.models import JobProfileDB
from src.resume_shortlister.parsers.structured_extractor import extract_structured_resume
from src.resume_shortlister.ranking.multi_factor_scorer import evaluate_candidate, ScoringWeights
from src.resume_shortlister.evaluation.benchmark_dataset import BENCHMARK_JOBS, generate_benchmark_candidates
from src.resume_shortlister.evaluation.metrics import (
    precision_at_k, top_k_agreement, rank_correlation, keyword_only_score
)

@dataclass
class JobEvaluationResult:
    job_id: int
    job_title: str
    candidates_count: int
    system_top10_agreement: float
    system_precision_at_3: float
    system_precision_at_5: float
    system_precision_at_10: float
    system_spearman_rho: float
    keyword_top10_agreement: float
    keyword_precision_at_10: float
    avg_latency_ms: float

@dataclass
class BenchmarkSummary:
    total_resumes_evaluated: int
    total_job_profiles: int
    overall_top10_agreement_pct: float
    overall_precision_at_10_pct: float
    overall_spearman_rho: float
    keyword_baseline_agreement_pct: float
    accuracy_lift_pct: float
    resume_bullet_text: str
    job_results: List[Dict[str, Any]]

def run_benchmark_evaluation() -> BenchmarkSummary:
    """
    Executes Phase 4 Empirical Evaluation across all labeled benchmark jobs.
    Measures Precision@K, Top-10 Recruiter Agreement, and Spearman correlation.
    Compares against a keyword-only screener baseline.
    """
    job_evals: List[JobEvaluationResult] = []
    total_resumes = 0

    for job_meta in BENCHMARK_JOBS:
        job_id = job_meta["job_id"]
        job_db = JobProfileDB(
            id=job_id,
            title=job_meta["title"],
            department=job_meta["department"],
            min_experience_years=job_meta["min_experience_years"],
            min_education=job_meta["min_education"],
            required_skills=json.dumps(job_meta["required_skills"]),
            nice_to_have_skills=json.dumps(job_meta["nice_to_have_skills"]),
            description=job_meta["description"]
        )

        candidates = generate_benchmark_candidates(job_id)
        total_resumes += len(candidates)

        ground_truth_top10 = [c["id"] for c in candidates if c["recruiter_shortlisted"]]
        ground_truth_set = set(ground_truth_top10)
        recruiter_ranks = [c["recruiter_rank"] for c in candidates]

        # 1. Evaluate Multi-Factor Anonymized Ranker
        system_scores = []
        t0 = time.perf_counter()
        for c in candidates:
            struct = extract_structured_resume(c["resume_text"], c["id"])
            score_obj = evaluate_candidate(struct, job_db, c["id"], f"cand_{c['id']}")
            system_scores.append((c["id"], score_obj.weighted_final_score))
        total_time_ms = (time.perf_counter() - t0) * 1000

        # Sort system rankings
        system_scores.sort(key=lambda x: x[1], reverse=True)
        system_ranked_ids = [x[0] for x in system_scores]
        raw_system_scores = [x[1] for x in system_scores]

        # Multi-factor metrics
        p3 = precision_at_k(system_ranked_ids, ground_truth_set, k=3)
        p5 = precision_at_k(system_ranked_ids, ground_truth_set, k=5)
        p10 = precision_at_k(system_ranked_ids, ground_truth_set, k=10)
        top10_agree = top_k_agreement(system_ranked_ids, ground_truth_top10, k=10)
        rho, _ = rank_correlation(raw_system_scores, recruiter_ranks)

        # 2. Evaluate Naive Keyword-Only Baseline
        req_kw = job_meta["required_skills"]
        kw_scores = [(c["id"], keyword_only_score(c["resume_text"], req_kw)) for c in candidates]
        kw_scores.sort(key=lambda x: x[1], reverse=True)
        kw_ranked_ids = [x[0] for x in kw_scores]
        kw_p10 = precision_at_k(kw_ranked_ids, ground_truth_set, k=10)
        kw_top10_agree = top_k_agreement(kw_ranked_ids, ground_truth_top10, k=10)

        job_evals.append(JobEvaluationResult(
            job_id=job_id,
            job_title=job_meta["title"],
            candidates_count=len(candidates),
            system_top10_agreement=top10_agree,
            system_precision_at_3=p3,
            system_precision_at_5=p5,
            system_precision_at_10=p10,
            system_spearman_rho=rho,
            keyword_top10_agreement=kw_top10_agree,
            keyword_precision_at_10=kw_p10,
            avg_latency_ms=round(total_time_ms / len(candidates), 2)
        ))

    # Aggregates
    avg_top10 = sum(e.system_top10_agreement for e in job_evals) / len(job_evals)
    avg_p10 = sum(e.system_precision_at_10 for e in job_evals) / len(job_evals)
    avg_rho = sum(e.system_spearman_rho for e in job_evals) / len(job_evals)
    avg_kw_agree = sum(e.keyword_top10_agreement for e in job_evals) / len(job_evals)

    lift = ((avg_top10 - avg_kw_agree) / avg_kw_agree * 100) if avg_kw_agree > 0 else 0.0
    top10_pct = round(avg_top10 * 100, 1)

    resume_bullet = (
        f"Built and deployed an explainable, anonymized resume-shortlisting platform "
        f"(FastAPI, sentence-transformers, LLM) that ranks candidates on education, experience, "
        f"projects and skills without using college name or personal identifiers; achieved {top10_pct}% "
        f"top-10 agreement with recruiter shortlists on {total_resumes} resumes while keeping interviews "
        f"and final decisions with HR."
    )

    return BenchmarkSummary(
        total_resumes_evaluated=total_resumes,
        total_job_profiles=len(job_evals),
        overall_top10_agreement_pct=top10_pct,
        overall_precision_at_10_pct=round(avg_p10 * 100, 1),
        overall_spearman_rho=round(avg_rho, 3),
        keyword_baseline_agreement_pct=round(avg_kw_agree * 100, 1),
        accuracy_lift_pct=round(lift, 1),
        resume_bullet_text=resume_bullet,
        job_results=[asdict(e) for e in job_evals]
    )
