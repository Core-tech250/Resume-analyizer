from typing import List, Dict, Any
from src.resume_shortlister.db.models import JobProfileDB
from src.resume_shortlister.parsers.structured_extractor import StructuredResume
from src.resume_shortlister.ranking.multi_factor_scorer import CandidateMultiFactorScore

def generate_candidate_explanation(
    structured: StructuredResume,
    job: JobProfileDB,
    score: CandidateMultiFactorScore
) -> Dict[str, Any]:
    """
    Generates transparent, evidence-grounded explainability data:
    1. Key strengths
    2. Identified gaps & growth areas
    3. Mathematical and qualitative score rationale
    """
    strengths: List[str] = []
    gaps: List[str] = []

    # 1. Skills Analysis
    if score.matched_required_skills:
        req_str = ", ".join(score.matched_required_skills)
        strengths.append(f"Demonstrates verified proficiency in required skills: {req_str}")
    
    if score.matched_nice_skills:
        nice_str = ", ".join(score.matched_nice_skills)
        strengths.append(f"Possesses preferred bonus capabilities: {nice_str}")

    if score.missing_required_skills:
        miss_str = ", ".join(score.missing_required_skills)
        gaps.append(f"Missing required technical competencies: {miss_str}")

    # 2. Experience Analysis
    cand_exp = structured.experience_years
    req_exp = job.min_experience_years
    if cand_exp >= req_exp:
        diff = round(cand_exp - req_exp, 1)
        if diff > 0:
            strengths.append(f"Exceeds minimum experience requirement with {cand_exp} years (+{diff} yrs above the {req_exp} yr threshold)")
        else:
            strengths.append(f"Meets the required {req_exp} years of technical experience")
    else:
        gap_exp = round(req_exp - cand_exp, 1)
        gaps.append(f"Experience deficit: {cand_exp} years documented vs. {req_exp} years required (gap of {gap_exp} yrs)")

    # 3. Project Depth Analysis
    if structured.projects:
        proj_count = len(structured.projects)
        strengths.append(f"Highlights {proj_count} demonstrated technical project(s) showcasing hands-on execution")
        # Extract keywords from projects
        proj_titles = [p.get("title", "") for p in structured.projects if p.get("title")]
        if proj_titles:
            strengths.append(f"Key project scope includes: '{proj_titles[0]}'")
    else:
        gaps.append("Resume contains no standalone dedicated project descriptions or repositories")

    # 4. Education & Academic Background
    if structured.degree_level != "None":
        strengths.append(f"Holds a verified {structured.degree_level} in {structured.field_of_study}")
    else:
        gaps.append("No formal degree level explicitly detected in education section")

    # 5. Comprehensive Rationale
    rationale = (
        f"Candidate achieved an overall match score of {score.percentage_score:.1f}% based on multi-factor analysis: "
        f"Skills fit scored at {score.skills_score*100:.0f}%, Experience fit at {score.experience_score*100:.0f}%, "
        f"Project relevance at {score.projects_score*100:.0f}%, and Education alignment at {score.education_score*100:.0f}%. "
    )
    if not gaps:
        rationale += "The candidate meets or exceeds all core qualifications with zero flagged deficiencies."
    elif score.hard_requirement_flags:
        rationale += f"Note: Recruiter review recommended due to active flags: {'; '.join(score.hard_requirement_flags)}."
    else:
        rationale += f"Minor gaps were noted in {len(gaps)} areas, but demonstrated strengths compensate well."

    return {
        "strengths": strengths,
        "gaps": gaps,
        "rationale": rationale
    }
