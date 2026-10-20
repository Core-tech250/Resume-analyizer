import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.resume_shortlister.db.database import get_db
from src.resume_shortlister.db.models import JobProfileDB
from src.resume_shortlister.schemas.job import JobProfileCreate, JobProfileResponse

router = APIRouter(prefix="/api/jobs", tags=["Job Profiles"])

def _db_to_response(job: JobProfileDB) -> JobProfileResponse:
    return JobProfileResponse(
        id=job.id,
        title=job.title,
        department=job.department,
        min_experience_years=job.min_experience_years,
        min_education=job.min_education,
        required_skills=json.loads(job.required_skills) if job.required_skills else [],
        nice_to_have_skills=json.loads(job.nice_to_have_skills) if job.nice_to_have_skills else [],
        description=job.description,
        created_at=job.created_at
    )

@router.post("", response_model=JobProfileResponse, status_code=status.HTTP_201_CREATED)
def create_job_profile(job_in: JobProfileCreate, db: Session = Depends(get_db)):
    """Create a new job profile."""
    job_db = JobProfileDB(
        title=job_in.title,
        department=job_in.department,
        min_experience_years=job_in.min_experience_years,
        min_education=job_in.min_education,
        required_skills=json.dumps(job_in.required_skills),
        nice_to_have_skills=json.dumps(job_in.nice_to_have_skills),
        description=job_in.description
    )
    db.add(job_db)
    db.commit()
    db.refresh(job_db)
    return _db_to_response(job_db)

@router.get("", response_model=List[JobProfileResponse])
def list_job_profiles(db: Session = Depends(get_db)):
    """List all created job profiles."""
    jobs = db.query(JobProfileDB).order_by(JobProfileDB.id.desc()).all()
    return [_db_to_response(job) for job in jobs]

@router.get("/{job_id}", response_model=JobProfileResponse)
def get_job_profile(job_id: int, db: Session = Depends(get_db)):
    """Get details of a specific job profile."""
    job = db.query(JobProfileDB).filter(JobProfileDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job profile not found")
    return _db_to_response(job)
