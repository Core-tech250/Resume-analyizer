from datetime import datetime, timezone
import json
import re
from typing import List, Optional
from sqlalchemy.orm import Session

from src.resume_shortlister.db.models import JobProfileDB, ResumeDB, RankingResultDB
from src.resume_shortlister.ranking.embedder import embedding_service
from src.resume_shortlister.ranking.multi_factor_scorer import (
    evaluate_candidate,
    ScoringWeights,
    CandidateMultiFactorScore
)
from src.resume_shortlister.parsers.structured_extractor import extract_structured_resume
from src.resume_shortlister.explainability.explainer import generate_candidate_explanation
from src.resume_shortlister.explainability.interview_generator import generate_interview_questions
from src.resume_shortlister.schemas.ranking import RankedCandidate, RankingResponse, ScoringWeightsSchema

def utcnow():
    return datetime.now(timezone.utc)

def construct_job_query_text(job: JobProfileDB) -> str:
    """
    Constructs a rich textual representation of the job profile for semantic embedding.
    """
    req_skills = json.loads(job.required_skills) if job.required_skills else []
    nice_skills = json.loads(job.nice_to_have_skills) if job.nice_to_have_skills else []

    parts = [
        f"Job Title: {job.title}",
        f"Department: {job.department or 'General'}",
        f"Minimum Experience: {job.min_experience_years} years",
        f"Education Requirement: {job.min_education}",
    ]

    if req_skills:
        parts.append(f"Required Skills: {', '.join(req_skills)}")
    if nice_skills:
        parts.append(f"Preferred Skills: {', '.join(nice_skills)}")

    parts.append(f"Job Description: {job.description}")
    return "\n".join(parts)

def find_matched_skills(text: str, skill_list: List[str]) -> List[str]:
    """
    Checks which skills appear in the resume text (case-insensitive boundary check).
    """
    matched = []
    text_lower = text.lower()
    for skill in skill_list:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matched.append(skill)
    return matched

def rank_resumes_for_job(
    db: Session,
    job_id: int,
    resume_ids: Optional[List[int]] = None,
    engine: str = "transformer",
    mode: str = "multifactor",
    weights: Optional[ScoringWeights] = None
) -> RankingResponse:
    """
    Ranks resumes against a specified Job Profile.
    Supports:
    - Phase 3 / Phase 2 'multifactor': Anonymized, multi-factor scoring with strengths, gaps,
      tailored interview questions, and HR workflow tracking.
    - Phase 1 'baseline': Pure semantic cosine similarity.
    """
    job = db.query(JobProfileDB).filter(JobProfileDB.id == job_id).first()
    if not job:
        raise ValueError(f"Job profile with id {job_id} not found.")

    query = db.query(ResumeDB)
    if resume_ids:
        query = query.filter(ResumeDB.id.in_(resume_ids))
    resumes = query.all()

    if not resumes:
        return RankingResponse(
            job_id=job.id,
            job_title=job.title,
            total_candidates=0,
            engine_used=engine,
            scoring_mode=mode,
            ranked_at=utcnow(),
            candidates=[]
        )

    # Preserve any existing HR notes or manual overrides when re-ranking
    existing_rankings = {r.resume_id: r for r in db.query(RankingResultDB).filter(RankingResultDB.job_id == job_id).all()}
    db.query(RankingResultDB).filter(RankingResultDB.job_id == job_id).delete()

    ranked_candidates = []

    if mode == "multifactor":
        if weights is None:
            weights = ScoringWeights()

        candidate_data = []
        for resume in resumes:
            # Ensure structured data and anonymization exist
            if not resume.anonymized_text or not resume.structured_data:
                struct_res = extract_structured_resume(resume.cleaned_text or resume.raw_text, resume.id)
                resume.anonymized_text = struct_res.anonymized_text
                resume.structured_data = json.dumps(struct_res.to_dict())
                resume.redactions_count = struct_res.redactions_count
                db.commit()
            else:
                data_dict = json.loads(resume.structured_data)
                from src.resume_shortlister.parsers.structured_extractor import StructuredResume
                struct_res = StructuredResume(
                    anonymous_id=data_dict.get("anonymous_id", f"CAND-{resume.id:04d}"),
                    degree_level=data_dict.get("degree_level", "None"),
                    field_of_study=data_dict.get("field_of_study", "General"),
                    experience_years=data_dict.get("experience_years", 0.0),
                    roles=data_dict.get("roles", []),
                    projects=data_dict.get("projects", []),
                    skills=data_dict.get("skills", []),
                    anonymized_text=resume.anonymized_text,
                    redactions_count=resume.redactions_count or 0,
                    raw_text=resume.raw_text
                )

            cand_score = evaluate_candidate(
                structured_resume=struct_res,
                job=job,
                resume_id=resume.id,
                filename=resume.filename,
                weights=weights
            )

            # Phase 3: Explainability and Interview Questions
            explanation = generate_candidate_explanation(struct_res, job, cand_score)
            questions = generate_interview_questions(struct_res, cand_score, job.title)

            # Check if this candidate had existing HR notes
            prev_record = existing_rankings.get(resume.id)
            hr_status = prev_record.hr_status if prev_record else "Shortlisted"
            hr_notes = prev_record.hr_notes if prev_record else ""
            identity_revealed = prev_record.identity_revealed if prev_record else False

            candidate_data.append({
                "resume": resume,
                "score": cand_score,
                "explanation": explanation,
                "questions": questions,
                "hr_status": hr_status,
                "hr_notes": hr_notes,
                "identity_revealed": identity_revealed
            })

        # Sort descending by weighted final score
        candidate_data.sort(key=lambda item: item["score"].weighted_final_score, reverse=True)

        for rank_idx, item in enumerate(candidate_data, start=1):
            s = item["score"]
            resume = item["resume"]
            explanation = item["explanation"]
            questions = item["questions"]

            db_rank = RankingResultDB(
                job_id=job.id,
                resume_id=s.resume_id,
                similarity_score=s.weighted_final_score,
                rank=rank_idx,
                skills_score=s.skills_score,
                experience_score=s.experience_score,
                projects_score=s.projects_score,
                education_score=s.education_score,
                hard_flags=json.dumps(s.hard_requirement_flags),
                matched_skills=json.dumps(s.matched_required_skills + s.matched_nice_skills),
                missing_skills=json.dumps(s.missing_required_skills),
                hr_status=item["hr_status"],
                hr_notes=item["hr_notes"],
                identity_revealed=item["identity_revealed"],
                strengths_json=json.dumps(explanation["strengths"]),
                gaps_json=json.dumps(explanation["gaps"]),
                interview_questions_json=json.dumps(questions),
                created_at=utcnow()
            )
            db.add(db_rank)

            ranked_candidates.append(RankedCandidate(
                rank=rank_idx,
                resume_id=s.resume_id,
                candidate_id=s.candidate_id,
                filename=s.filename,
                similarity_score=s.weighted_final_score,
                percentage_score=s.percentage_score,
                skills_score=round(s.skills_score * 100, 1),
                experience_score=round(s.experience_score * 100, 1),
                projects_score=round(s.projects_score * 100, 1),
                education_score=round(s.education_score * 100, 1),
                hard_requirement_flags=s.hard_requirement_flags,
                matched_skills=s.matched_required_skills + s.matched_nice_skills,
                missing_skills=s.missing_required_skills,
                preview_snippet=s.preview_snippet,
                anonymized_preview=s.anonymized_preview,
                hr_status=item["hr_status"],
                hr_notes=item["hr_notes"],
                identity_revealed=item["identity_revealed"],
                strengths=explanation["strengths"],
                gaps=explanation["gaps"],
                interview_questions=questions,
                score_rationale=explanation["rationale"]
            ))

        db.commit()

        weights_schema = ScoringWeightsSchema(
            skills_weight=weights.skills_weight,
            experience_weight=weights.experience_weight,
            projects_weight=weights.projects_weight,
            education_weight=weights.education_weight
        )

        return RankingResponse(
            job_id=job.id,
            job_title=job.title,
            total_candidates=len(ranked_candidates),
            engine_used=engine,
            scoring_mode="multifactor",
            ranked_at=utcnow(),
            weights_used=weights_schema,
            candidates=ranked_candidates
        )

    else:
        # Baseline cosine similarity
        job_text = construct_job_query_text(job)
        resume_texts = [r.cleaned_text for r in resumes]
        similarity_scores = embedding_service.rank_texts(job_text, resume_texts, engine=engine)

        req_skills = json.loads(job.required_skills) if job.required_skills else []
        nice_skills = json.loads(job.nice_to_have_skills) if job.nice_to_have_skills else []
        all_skills = list(dict.fromkeys(req_skills + nice_skills))

        candidate_results = []
        for resume, score in zip(resumes, similarity_scores):
            matched = find_matched_skills(resume.cleaned_text, all_skills)
            missing = [s for s in all_skills if s not in matched]
            preview = " ".join(resume.cleaned_text.split()[:40]) + "..."
            candidate_results.append({
                "resume": resume,
                "score": score,
                "matched_skills": matched,
                "missing_skills": missing,
                "preview": preview
            })

        candidate_results.sort(key=lambda x: x["score"], reverse=True)

        for rank_idx, item in enumerate(candidate_results, start=1):
            resume = item["resume"]
            score = item["score"]
            db_rank = RankingResultDB(
                job_id=job.id,
                resume_id=resume.id,
                similarity_score=round(score, 4),
                rank=rank_idx,
                matched_skills=json.dumps(item["matched_skills"]),
                missing_skills=json.dumps(item["missing_skills"]),
                created_at=utcnow()
            )
            db.add(db_rank)

            ranked_candidates.append(RankedCandidate(
                rank=rank_idx,
                resume_id=resume.id,
                candidate_id=f"CAND-{resume.id:04d}",
                filename=resume.filename,
                similarity_score=round(score, 4),
                percentage_score=round(score * 100, 1),
                matched_skills=item["matched_skills"],
                missing_skills=item["missing_skills"],
                preview_snippet=item["preview"]
            ))

        db.commit()

        return RankingResponse(
            job_id=job.id,
            job_title=job.title,
            total_candidates=len(ranked_candidates),
            engine_used=engine,
            scoring_mode="baseline",
            ranked_at=utcnow(),
            candidates=ranked_candidates
        )
