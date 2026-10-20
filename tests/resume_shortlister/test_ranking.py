import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.resume_shortlister.db.models import Base, JobProfileDB, ResumeDB
from src.resume_shortlister.ranking.similarity import cosine_similarity_1d, cosine_similarity_matrix
from src.resume_shortlister.ranking.embedder import embedding_service
from src.resume_shortlister.ranking.ranker import find_matched_skills, rank_resumes_for_job

def test_cosine_similarity_identical_vectors():
    vec = np.array([1.0, 2.0, 3.0])
    sim = cosine_similarity_1d(vec, vec)
    assert pytest.approx(sim, 0.001) == 1.0

def test_cosine_similarity_orthogonal_vectors():
    vec_a = np.array([1.0, 0.0])
    vec_b = np.array([0.0, 1.0])
    sim = cosine_similarity_1d(vec_a, vec_b)
    assert pytest.approx(sim, 0.001) == 0.0

def test_find_matched_skills():
    resume_text = "Proficient in Python, FastAPI, and Docker. Experience with SQL and Postgres."
    skills = ["Python", "FastAPI", "Kubernetes", "Docker", "Go"]
    matched = find_matched_skills(resume_text, skills)
    assert "Python" in matched
    assert "FastAPI" in matched
    assert "Docker" in matched
    assert "Kubernetes" not in matched
    assert "Go" not in matched

def test_tfidf_ranking_order():
    job_text = "Senior Python Backend Engineer with FastAPI and PostgreSQL microservices"
    candidate_1 = "Experienced Python developer building FastAPI web services and SQL databases."
    candidate_2 = "Creative UX Designer with Figma, Adobe XD, and user research skills."
    
    scores = embedding_service.rank_texts(job_text, [candidate_1, candidate_2], engine="tfidf")
    assert len(scores) == 2
    assert scores[0] > scores[1]  # Python dev should score significantly higher than UX designer

def test_end_to_end_ranking_in_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    import json
    job = JobProfileDB(
        title="Python Engineer",
        min_experience_years=2.0,
        required_skills=json.dumps(["Python", "SQL"]),
        nice_to_have_skills=json.dumps(["Docker"]),
        description="Looking for Python backend developer."
    )
    db.add(job)
    db.commit()

    r1 = ResumeDB(
        filename="alice.pdf",
        file_type="pdf",
        raw_text="Alice: Senior Python Engineer with 5 years experience in SQL and Docker.",
        cleaned_text="Alice: Senior Python Engineer with 5 years experience in SQL and Docker."
    )
    r2 = ResumeDB(
        filename="bob.pdf",
        file_type="pdf",
        raw_text="Bob: Marketing specialist and content strategist.",
        cleaned_text="Bob: Marketing specialist and content strategist."
    )
    db.add_all([r1, r2])
    db.commit()

    resp = rank_resumes_for_job(db, job_id=job.id, engine="tfidf")
    assert resp.total_candidates == 2
    assert resp.candidates[0].filename == "alice.pdf"
    assert resp.candidates[0].rank == 1
    assert "Python" in resp.candidates[0].matched_skills
    db.close()
