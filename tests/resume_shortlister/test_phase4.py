import logging
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.resume_shortlister.db.models import Base, ResumeDB, RankingResultDB
from src.resume_shortlister.evaluation.evaluator import run_benchmark_evaluation
from src.resume_shortlister.evaluation.metrics import precision_at_k, top_k_agreement, rank_correlation
from src.resume_shortlister.cache.embedding_cache import EmbeddingCache
from src.resume_shortlister.auth.rbac import AuthUser, UserRole, check_permission
from src.resume_shortlister.privacy.retention import purge_expired_resumes
from src.resume_shortlister.privacy.safe_logger import PrivacySanitizingFilter

def test_benchmark_evaluation_meets_accuracy_target():
    """
    Core Phase 4 Target:
    Verify that our Anonymized Multi-Factor Ranker achieves >= 80% Top-10 agreement
    with recruiter shortlists across the benchmark dataset.
    """
    summary = run_benchmark_evaluation()

    assert summary.total_resumes_evaluated == 60
    assert summary.total_job_profiles == 3
    # Target: >= 80% Top-10 Recruiter Agreement
    assert summary.overall_top10_agreement_pct >= 80.0
    # Statistically matches or outperforms keyword baseline
    assert summary.overall_top10_agreement_pct >= summary.keyword_baseline_agreement_pct
    assert summary.overall_spearman_rho > 0.50
    # Verify resume bullet string is populated
    assert f"{summary.overall_top10_agreement_pct}%" in summary.resume_bullet_text
    assert "60 resumes" in summary.resume_bullet_text

def test_embedding_cache_hit_rate():
    """
    Verifies embedding caching mechanisms and hit rate tracking.
    """
    cache = EmbeddingCache()
    import numpy as np
    dummy_vec = np.array([0.1, 0.2, 0.3])

    # Initial miss
    assert cache.get("test text") is None
    assert cache.misses == 1

    # Put in cache
    cache.put("test text", dummy_vec)

    # Subsequent hit
    retrieved = cache.get("test text")
    assert retrieved is not None
    assert np.allclose(retrieved, dummy_vec)
    assert cache.hits == 1
    assert cache.hit_rate == 50.0

def test_rbac_permissions():
    """
    Verifies role-based access control for HR Admin, Recruiter, and Viewer.
    """
    admin = AuthUser(user_id=1, email="admin@corp.io", role=UserRole.HR_ADMIN, company_id=1)
    recruiter = AuthUser(user_id=2, email="recruiter@corp.io", role=UserRole.RECRUITER, company_id=1)
    viewer = AuthUser(user_id=3, email="guest@corp.io", role=UserRole.VIEWER, company_id=1)

    # Admin has all permissions
    assert check_permission(admin, "purge_data") is True
    assert check_permission(admin, "unmask_identity") is True

    # Recruiter has operational rights but cannot purge data
    assert check_permission(recruiter, "view_shortlist") is True
    assert check_permission(recruiter, "override_candidate_status") is True
    assert check_permission(recruiter, "purge_data") is False

    # Viewer has read-only rights
    assert check_permission(viewer, "view_shortlist") is True
    assert check_permission(viewer, "override_candidate_status") is False
    assert check_permission(viewer, "upload_resumes") is False

def test_privacy_retention_purge():
    """
    Verifies that candidate records older than the retention cutoff are permanently deleted.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime.now(timezone.utc)
    # Old resume (120 days ago)
    old_res = ResumeDB(
        filename="old_candidate.pdf",
        file_type="pdf",
        raw_text="Old candidate text",
        cleaned_text="Old candidate text",
        created_at=now - timedelta(days=120)
    )
    # Recent resume (10 days ago)
    recent_res = ResumeDB(
        filename="recent_candidate.pdf",
        file_type="pdf",
        raw_text="Recent candidate text",
        cleaned_text="Recent candidate text",
        created_at=now - timedelta(days=10)
    )
    db.add_all([old_res, recent_res])
    db.commit()

    # Purge resumes older than 90 days
    result = purge_expired_resumes(db, retention_days=90)
    assert result["resumes_purged"] == 1

    remaining = db.query(ResumeDB).all()
    assert len(remaining) == 1
    assert remaining[0].filename == "recent_candidate.pdf"
    db.close()

def test_safe_logger_scrubs_pii():
    """
    Verifies that the privacy logging filter sanitizes emails and phone numbers.
    """
    filter_instance = PrivacySanitizingFilter()
    log_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Candidate contact: candidate.john@example.com, phone: 415-555-0199 applied.",
        args=(),
        exc_info=None
    )
    filter_instance.filter(log_record)

    assert "candidate.john@example.com" not in log_record.msg
    assert "[LOG_SCRUBBED_EMAIL]" in log_record.msg
    assert "415-555-0199" not in log_record.msg
    assert "[LOG_SCRUBBED_PHONE]" in log_record.msg
