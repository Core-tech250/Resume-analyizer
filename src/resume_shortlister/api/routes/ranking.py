from datetime import datetime, timezone
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from src.resume_shortlister.db.database import get_db
from src.resume_shortlister.db.models import JobProfileDB, RankingResultDB, ResumeDB
from src.resume_shortlister.ranking.ranker import rank_resumes_for_job
from src.resume_shortlister.ranking.multi_factor_scorer import ScoringWeights
from src.resume_shortlister.reporting.csv_exporter import export_shortlist_to_csv
from src.resume_shortlister.reporting.pdf_exporter import generate_shortlist_pdf_report
from src.resume_shortlister.schemas.ranking import (
    RankedCandidate, RankingRequest, RankingResponse, HROverrideRequest
)

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])

def utcnow():
    return datetime.now(timezone.utc)

@router.post("/run", response_model=RankingResponse)
def run_ranking(req: RankingRequest, db: Session = Depends(get_db)):
    """
    Ranks resumes against a job profile.
    Supports Phase 3/2 multi-factor scoring with explainability, or Phase 1 baseline.
    """
    try:
        weights_obj = None
        if req.weights:
            weights_obj = ScoringWeights(
                skills_weight=req.weights.skills_weight,
                experience_weight=req.weights.experience_weight,
                projects_weight=req.weights.projects_weight,
                education_weight=req.weights.education_weight
            )

        response = rank_resumes_for_job(
            db=db,
            job_id=req.job_id,
            resume_ids=req.resume_ids,
            engine=req.engine,
            mode=req.mode,
            weights=weights_obj
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {e}")

@router.get("/{job_id}", response_model=RankingResponse)
def get_job_ranking(job_id: int, db: Session = Depends(get_db)):
    """
    Get the latest stored ranking results for a job profile with complete Phase 3 metadata.
    """
    job = db.query(JobProfileDB).filter(JobProfileDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job profile not found")

    rankings = (
        db.query(RankingResultDB)
        .filter(RankingResultDB.job_id == job_id)
        .order_by(RankingResultDB.rank.asc())
        .all()
    )

    candidates = []
    for r in rankings:
        resume = db.query(ResumeDB).filter(ResumeDB.id == r.resume_id).first()
        filename = resume.filename if resume else f"Resume #{r.resume_id}"
        preview = " ".join(resume.cleaned_text.split()[:40]) + "..." if resume else ""
        anon_preview = " ".join((resume.anonymized_text or "").split()[:40]) + "..." if resume else ""

        matched = json.loads(r.matched_skills) if r.matched_skills else []
        missing = json.loads(r.missing_skills) if r.missing_skills else []
        flags = json.loads(r.hard_flags) if r.hard_flags else []
        strengths = json.loads(r.strengths_json) if r.strengths_json else []
        gaps = json.loads(r.gaps_json) if r.gaps_json else []
        questions = json.loads(r.interview_questions_json) if r.interview_questions_json else []

        candidates.append(RankedCandidate(
            rank=r.rank,
            resume_id=r.resume_id,
            candidate_id=f"CAND-{r.resume_id:04d}",
            filename=filename,
            similarity_score=r.similarity_score,
            percentage_score=round(r.similarity_score * 100, 1),
            skills_score=round((r.skills_score or 0.0) * 100, 1),
            experience_score=round((r.experience_score or 0.0) * 100, 1),
            projects_score=round((r.projects_score or 0.0) * 100, 1),
            education_score=round((r.education_score or 0.0) * 100, 1),
            hard_requirement_flags=flags,
            matched_skills=matched,
            missing_skills=missing,
            preview_snippet=preview,
            anonymized_preview=anon_preview,
            hr_status=r.hr_status or "Shortlisted",
            hr_notes=r.hr_notes or "",
            identity_revealed=bool(r.identity_revealed),
            strengths=strengths,
            gaps=gaps,
            interview_questions=questions
        ))

    return RankingResponse(
        job_id=job.id,
        job_title=job.title,
        total_candidates=len(candidates),
        engine_used="stored_results",
        scoring_mode="multifactor",
        ranked_at=rankings[0].created_at if rankings else utcnow(),
        candidates=candidates
    )

@router.patch("/{ranking_id}/override")
def override_hr_candidate(
    ranking_id: int,
    req: HROverrideRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 3 HR Control: Manual override of status, recruiter evaluation notes,
    and unmasking identity only after shortlisting.
    """
    rec = db.query(RankingResultDB).filter(RankingResultDB.id == ranking_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Ranking record not found")

    if req.hr_status is not None:
        rec.hr_status = req.hr_status
    if req.hr_notes is not None:
        rec.hr_notes = req.hr_notes
    if req.identity_revealed is not None:
        rec.identity_revealed = req.identity_revealed

    db.commit()
    return {"status": "success", "ranking_id": rec.id, "hr_status": rec.hr_status, "identity_revealed": rec.identity_revealed}

@router.get("/{job_id}/export/csv")
def export_csv(job_id: int, db: Session = Depends(get_db)):
    """
    Export shortlist as a CSV file.
    """
    resp = get_job_ranking(job_id, db)
    candidates_dict = [c.dict() for c in resp.candidates]
    csv_content = export_shortlist_to_csv(candidates_dict)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=shortlist_job_{job_id}.csv"}
    )

@router.get("/{job_id}/export/pdf")
def export_pdf(job_id: int, db: Session = Depends(get_db)):
    """
    Export shortlist as an executive PDF report.
    """
    job = db.query(JobProfileDB).filter(JobProfileDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp = get_job_ranking(job_id, db)
    candidates_dict = [c.dict() for c in resp.candidates]

    job_info = {
        "title": job.title,
        "department": job.department,
        "min_experience_years": job.min_experience_years,
        "min_education": job.min_education,
        "required_skills": json.loads(job.required_skills) if job.required_skills else [],
        "nice_to_have_skills": json.loads(job.nice_to_have_skills) if job.nice_to_have_skills else []
    }

    pdf_bytes = generate_shortlist_pdf_report(job_info, candidates_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=shortlist_report_job_{job_id}.pdf"}
    )
