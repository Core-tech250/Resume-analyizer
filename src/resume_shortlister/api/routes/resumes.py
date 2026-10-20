import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from src.resume_shortlister.config import settings
from src.resume_shortlister.db.database import get_db
from src.resume_shortlister.db.models import ResumeDB
from src.resume_shortlister.parsers.extractor import extract_resume_text
from src.resume_shortlister.parsers.cleaner import generate_preview_snippet
from src.resume_shortlister.schemas.resume import ResumeResponse, ResumeUploadResponse, ResumeUploadResult

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload one or multiple resumes (PDF, DOCX, TXT).
    Extracts text, cleans it, handles OCR fallback for scanned documents,
    and stores records in the database.
    """
    results: List[ResumeUploadResult] = []
    success_count = 0
    fail_count = 0

    for file in files:
        filename = file.filename or "unknown"
        try:
            content = await file.read()
            if not content:
                results.append(ResumeUploadResult(
                    filename=filename,
                    status="failed",
                    error="Empty file"
                ))
                fail_count += 1
                continue

            # Save raw file to uploads directory
            safe_filename = f"{os.urandom(4).hex()}_{filename}"
            save_path = settings.UPLOAD_DIR / safe_filename
            with open(save_path, "wb") as f:
                f.write(content)

            # Extract text & metadata
            extracted = extract_resume_text(content, filename)

            # Save record to DB
            db_resume = ResumeDB(
                filename=filename,
                file_type=extracted.file_type,
                file_size=len(content),
                file_path=str(save_path),
                raw_text=extracted.raw_text,
                cleaned_text=extracted.cleaned_text,
                char_count=extracted.char_count,
                word_count=extracted.word_count,
                ocr_used=extracted.ocr_used
            )
            db.add(db_resume)
            db.commit()
            db.refresh(db_resume)

            success_count += 1
            results.append(ResumeUploadResult(
                filename=filename,
                status="success",
                resume_id=db_resume.id,
                char_count=extracted.char_count,
                word_count=extracted.word_count,
                ocr_used=extracted.ocr_used
            ))

        except Exception as e:
            db.rollback()
            fail_count += 1
            results.append(ResumeUploadResult(
                filename=filename,
                status="failed",
                error=str(e)
            ))

    return ResumeUploadResponse(
        total_uploaded=len(files),
        successful=success_count,
        failed=fail_count,
        results=results
    )

@router.get("", response_model=List[ResumeResponse])
def list_resumes(db: Session = Depends(get_db)):
    """List all ingested resumes."""
    resumes = db.query(ResumeDB).order_by(ResumeDB.id.desc()).all()
    out = []
    for r in resumes:
        out.append(ResumeResponse(
            id=r.id,
            filename=r.filename,
            file_type=r.file_type,
            file_size=r.file_size,
            char_count=r.char_count,
            word_count=r.word_count,
            preview_snippet=generate_preview_snippet(r.cleaned_text),
            ocr_used=r.ocr_used,
            created_at=r.created_at
        ))
    return out

@router.get("/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific resume including text."""
    r = db.query(ResumeDB).filter(ResumeDB.id == resume_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": r.id,
        "filename": r.filename,
        "file_type": r.file_type,
        "file_size": r.file_size,
        "char_count": r.char_count,
        "word_count": r.word_count,
        "ocr_used": r.ocr_used,
        "created_at": r.created_at,
        "cleaned_text": r.cleaned_text
    }
