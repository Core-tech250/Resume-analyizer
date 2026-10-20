from datetime import datetime, timedelta, timezone
import os
from typing import Dict, Any
from sqlalchemy.orm import Session

from src.resume_shortlister.db.models import ResumeDB, RankingResultDB

def purge_expired_resumes(db: Session, retention_days: int = 90) -> Dict[str, Any]:
    """
    Phase 4 Privacy & Security Compliance:
    Automatically deletes resumes and associated candidate rankings that exceed
    the organizational data retention window.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    expired_resumes = (
        db.query(ResumeDB)
        .filter(ResumeDB.created_at < cutoff_date)
        .all()
    )

    deleted_count = 0
    freed_bytes = 0

    for r in expired_resumes:
        # Delete underlying physical file if it exists
        if r.file_path and os.path.exists(r.file_path):
            try:
                freed_bytes += os.path.getsize(r.file_path)
                os.remove(r.file_path)
            except Exception:
                pass

        # Cascade deletes associated rankings
        db.query(RankingResultDB).filter(RankingResultDB.resume_id == r.id).delete()
        db.delete(r)
        deleted_count += 1

    db.commit()

    return {
        "status": "success",
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
        "resumes_purged": deleted_count,
        "storage_freed_bytes": freed_bytes
    }
