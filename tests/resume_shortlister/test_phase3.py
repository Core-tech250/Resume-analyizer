import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.resume_shortlister.db.models import Base, JobProfileDB, ResumeDB, RankingResultDB
from src.resume_shortlister.parsers.structured_extractor import extract_structured_resume
from src.resume_shortlister.ranking.multi_factor_scorer import evaluate_candidate, ScoringWeights
from src.resume_shortlister.explainability.explainer import generate_candidate_explanation
from src.resume_shortlister.explainability.interview_generator import generate_interview_questions
from src.resume_shortlister.reporting.csv_exporter import export_shortlist_to_csv
from src.resume_shortlister.reporting.pdf_exporter import generate_shortlist_pdf_report

JOB_FIXTURE = JobProfileDB(
    title="Senior Backend Engineer",
    department="Engineering",
    min_experience_years=3.0,
    min_education="Bachelor's",
    required_skills='["Python", "FastAPI", "Docker", "SQL"]',
    nice_to_have_skills='["PostgreSQL", "Redis"]',
    description="We need a backend engineer with Python, FastAPI, and Docker microservices experience."
)

CANDIDATE_TEXT = """
Alex Vance - Senior Software Engineer
Summary:
Backend developer with 5 years experience building resilient microservices and distributed APIs.
Technical Skills:
- Languages & Frameworks: Python, FastAPI, Django, Flask, SQL, Bash
- Databases & Queues: PostgreSQL, Redis, SQLAlchemy
- DevOps & Tools: Docker, Git, Linux
Experience:
Senior Backend Developer | NovaCloud (2022 - Present)
- Architected and deployed 15+ FastAPI microservices handling 25M daily requests.
- Implemented PostgreSQL schema optimizations reducing query latency by 45%.
Projects:
- High-Throughput Stream Pipeline: Built Kafka-based event processor in Python.
Education:
Bachelor of Science in Computer Science (2019)
"""

def test_explainability_generation():
    """
    Verifies that explainability engine extracts concrete strengths,
    identifies missing skills, and formulates a transparent rationale.
    """
    struct = extract_structured_resume(CANDIDATE_TEXT, resume_id=1)
    score = evaluate_candidate(struct, JOB_FIXTURE, resume_id=1, filename="alex.pdf")
    explanation = generate_candidate_explanation(struct, JOB_FIXTURE, score)

    assert "strengths" in explanation
    assert len(explanation["strengths"]) >= 2
    assert any("Python" in s for s in explanation["strengths"])
    assert "rationale" in explanation
    assert f"{score.percentage_score:.1f}%" in explanation["rationale"]

def test_interview_questions_generation():
    """
    Verifies that tailored interview questions are generated based on
    candidate's projects, technical strengths, and any gaps.
    """
    struct = extract_structured_resume(CANDIDATE_TEXT, resume_id=1)
    score = evaluate_candidate(struct, JOB_FIXTURE, resume_id=1, filename="alex.pdf")
    questions = generate_interview_questions(struct, score, JOB_FIXTURE.title)

    assert len(questions) >= 2
    categories = [q["category"] for q in questions]
    assert any("Technical Depth" in c or "Project" in c for c in categories)
    # Check question formatting
    for q in questions:
        assert len(q["question"]) > 20
        assert "?" in q["question"]

def test_csv_export():
    """
    Verifies CSV export contains expected columns and valid data.
    """
    candidates = [{
        "rank": 1,
        "candidate_id": "CAND-0001",
        "filename": "alex.pdf",
        "percentage_score": 92.5,
        "skills_score": 95.0,
        "experience_score": 100.0,
        "projects_score": 85.0,
        "education_score": 100.0,
        "matched_skills": ["Python", "FastAPI", "Docker"],
        "missing_skills": [],
        "hr_status": "Shortlisted",
        "hr_notes": "Top tier backend candidate",
        "hard_requirement_flags": []
    }]
    csv_str = export_shortlist_to_csv(candidates)
    assert "CAND-0001" in csv_str
    assert "92.5%" in csv_str
    assert "Top tier backend candidate" in csv_str

def test_pdf_report_generation():
    """
    Verifies that the PDF generator builds a valid PDF document with reportlab.
    """
    job_info = {
        "title": "Senior Backend Engineer",
        "department": "Engineering",
        "min_experience_years": 3.0,
        "min_education": "Bachelor's",
        "required_skills": ["Python", "FastAPI"],
        "nice_to_have_skills": ["Docker"]
    }
    candidates = [{
        "rank": 1,
        "candidate_id": "CAND-0001",
        "percentage_score": 90.0,
        "skills_score": 95.0,
        "experience_score": 100.0,
        "projects_score": 80.0,
        "education_score": 100.0,
        "hr_status": "Shortlisted",
        "strengths": ["Strong Python experience", "Exceeds experience threshold"],
        "gaps": [],
        "interview_questions": [{"category": "Technical", "question": "Explain async await in FastAPI?"}],
        "hr_notes": "Proceed to Round 1"
    }]
    pdf_bytes = generate_shortlist_pdf_report(job_info, candidates)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
