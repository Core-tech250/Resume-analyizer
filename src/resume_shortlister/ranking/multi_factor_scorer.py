from dataclasses import dataclass, field
import json
import logging
from typing import List, Dict, Any, Optional

from src.resume_shortlister.db.models import JobProfileDB
from src.resume_shortlister.parsers.structured_extractor import StructuredResume, DEGREE_HIERARCHY
from src.resume_shortlister.anonymizer.synonyms import are_skills_equivalent, match_skills_in_text
from src.resume_shortlister.ranking.similarity import cosine_similarity_1d
from src.resume_shortlister.ranking.embedder import embedding_service

logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    skills_weight: float = 0.40
    experience_weight: float = 0.30
    projects_weight: float = 0.20
    education_weight: float = 0.10

    def normalized(self) -> "ScoringWeights":
        total = self.skills_weight + self.experience_weight + self.projects_weight + self.education_weight
        if total == 0:
            return ScoringWeights(0.25, 0.25, 0.25, 0.25)
        return ScoringWeights(
            skills_weight=round(self.skills_weight / total, 4),
            experience_weight=round(self.experience_weight / total, 4),
            projects_weight=round(self.projects_weight / total, 4),
            education_weight=round(self.education_weight / total, 4)
        )

@dataclass
class CandidateMultiFactorScore:
    candidate_id: str
    resume_id: int
    filename: str
    skills_score: float         # 0.0 to 1.0
    experience_score: float     # 0.0 to 1.0
    projects_score: float       # 0.0 to 1.0
    education_score: float      # 0.0 to 1.0
    weighted_final_score: float # 0.0 to 1.0
    percentage_score: float     # 0 to 100%
    matched_required_skills: List[str] = field(default_factory=list)
    missing_required_skills: List[str] = field(default_factory=list)
    matched_nice_skills: List[str] = field(default_factory=list)
    hard_requirement_flags: List[str] = field(default_factory=list)
    preview_snippet: str = ""
    anonymized_preview: str = ""

def score_skills(
    candidate_skills: List[str],
    required_skills: List[str],
    nice_to_have_skills: List[str]
) -> tuple[float, List[str], List[str], List[str]]:
    """
    Computes synonym-aware skill match score.
    Required skills carry 75% of skill score; nice-to-have carry 25%.
    """
    matched_req = []
    missing_req = []
    for req in required_skills:
        if any(are_skills_equivalent(req, c_skill) for c_skill in candidate_skills):
            matched_req.append(req)
        else:
            missing_req.append(req)

    matched_nice = []
    for nice in nice_to_have_skills:
        if any(are_skills_equivalent(nice, c_skill) for c_skill in candidate_skills):
            matched_nice.append(nice)

    req_score = len(matched_req) / len(required_skills) if required_skills else 1.0
    nice_score = len(matched_nice) / len(nice_to_have_skills) if nice_to_have_skills else 1.0

    if required_skills and nice_to_have_skills:
        total_skill_score = (0.75 * req_score) + (0.25 * nice_score)
    elif required_skills:
        total_skill_score = req_score
    else:
        total_skill_score = nice_score

    return round(float(total_skill_score), 4), matched_req, missing_req, matched_nice

def score_experience(
    candidate_years: float,
    min_required_years: float
) -> tuple[float, List[str]]:
    """
    Computes experience fit score and flags candidates who miss hard requirement
    without auto-rejecting.
    """
    flags = []
    if min_required_years <= 0.0:
        return 1.0, flags

    if candidate_years >= min_required_years:
        # Full score + slight reward if extensive
        score = 1.0
    else:
        # Proportional scale
        score = max(0.2, candidate_years / min_required_years)
        gap = round(min_required_years - candidate_years, 1)
        flags.append(f"⚠️ Experience Requirement Flag: Has {candidate_years} yrs (Required: {min_required_years} yrs, gap: {gap} yrs)")

    return round(float(score), 4), flags

def score_education(
    degree_level: str,
    field_of_study: str,
    min_education: str
) -> float:
    """
    Evaluates degree level and field of study ONLY.
    Never receives or considers institution/college names.
    """
    req_rank = 2  # default Bachelor's
    for d_key, r in DEGREE_HIERARCHY.items():
        if d_key in min_education.lower():
            req_rank = r
            break

    cand_rank = 0
    for d_key, r in DEGREE_HIERARCHY.items():
        if d_key in degree_level.lower():
            cand_rank = r
            break

    if cand_rank >= req_rank:
        level_score = 1.0
    elif cand_rank == req_rank - 1:
        level_score = 0.7
    else:
        level_score = 0.4

    # Field of study relevance
    field_lower = field_of_study.lower()
    if any(tech in field_lower for tech in ["computer", "artificial intelligence", "data", "information technology", "software", "engineering"]):
        field_score = 1.0
    elif "business" in field_lower or "design" in field_lower:
        field_score = 0.8
    else:
        field_score = 0.6

    final_edu = (0.6 * level_score) + (0.4 * field_score)
    return round(float(final_edu), 4)

def score_projects(
    projects: List[Dict[str, Any]],
    job_desc: str,
    required_skills: List[str]
) -> float:
    """
    Evaluates project scope and tech relevance against job description.
    """
    if not projects:
        return 0.4  # baseline for missing projects section

    proj_texts = [p.get("description", "") for p in projects]
    full_proj_text = " ".join(proj_texts)

    # Check skill mentions inside projects
    matched_proj_skills = match_skills_in_text(full_proj_text, required_skills)
    skill_coverage = len(matched_proj_skills) / len(required_skills) if required_skills else 1.0

    # Semantic similarity of project descriptions to job description
    try:
        sims = embedding_service.rank_texts(job_desc, [full_proj_text], engine="tfidf")
        sem_score = sims[0] if sims else 0.5
    except Exception:
        sem_score = 0.5

    final_proj_score = (0.5 * skill_coverage) + (0.5 * sem_score)
    return round(float(min(1.0, max(0.2, final_proj_score))), 4)

def evaluate_candidate(
    structured_resume: StructuredResume,
    job: JobProfileDB,
    resume_id: int,
    filename: str,
    weights: Optional[ScoringWeights] = None
) -> CandidateMultiFactorScore:
    """
    Full Phase 2 Multi-Factor Scoring Pipeline:
    1. Skills score (synonym-aware)
    2. Experience score (with hard requirement flag)
    3. Projects score (scope and tech relevance)
    4. Education score (degree level & field only, zero college bias)
    5. Weighted final score with adjustable weights
    """
    if weights is None:
        weights = ScoringWeights()
    w = weights.normalized()

    req_skills = json.loads(job.required_skills) if job.required_skills else []
    nice_skills = json.loads(job.nice_to_have_skills) if job.nice_to_have_skills else []

    # 1. Skills
    skills_score, matched_req, missing_req, matched_nice = score_skills(
        structured_resume.skills, req_skills, nice_skills
    )

    # 2. Experience
    exp_score, exp_flags = score_experience(
        structured_resume.experience_years, job.min_experience_years
    )

    # 3. Education
    edu_score = score_education(
        structured_resume.degree_level, structured_resume.field_of_study, job.min_education
    )

    # 4. Projects
    proj_score = score_projects(
        structured_resume.projects, job.description, req_skills
    )

    # Hard flags for critical missing skills
    flags = list(exp_flags)
    if missing_req and len(missing_req) == len(req_skills):
        flags.append("⚠️ Missing All Required Skills")

    # Weighted final score
    weighted_score = (
        (w.skills_weight * skills_score) +
        (w.experience_weight * exp_score) +
        (w.projects_weight * proj_score) +
        (w.education_weight * edu_score)
    )
    weighted_score = round(float(weighted_score), 4)

    preview = " ".join(structured_resume.raw_text.split()[:35]) + "..."
    anon_preview = " ".join(structured_resume.anonymized_text.split()[:35]) + "..."

    return CandidateMultiFactorScore(
        candidate_id=structured_resume.anonymous_id,
        resume_id=resume_id,
        filename=filename,
        skills_score=skills_score,
        experience_score=exp_score,
        projects_score=proj_score,
        education_score=edu_score,
        weighted_final_score=weighted_score,
        percentage_score=round(weighted_score * 100, 1),
        matched_required_skills=matched_req,
        missing_required_skills=missing_req,
        matched_nice_skills=matched_nice,
        hard_requirement_flags=flags,
        preview_snippet=preview,
        anonymized_preview=anon_preview
    )
