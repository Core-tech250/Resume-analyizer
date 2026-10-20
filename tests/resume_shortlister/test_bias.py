import pytest
from src.resume_shortlister.db.models import JobProfileDB
from src.resume_shortlister.anonymizer.redactor import redact_personal_and_institutional_data
from src.resume_shortlister.parsers.structured_extractor import extract_structured_resume
from src.resume_shortlister.ranking.multi_factor_scorer import evaluate_candidate, ScoringWeights

JOB_FIXTURE = JobProfileDB(
    title="Senior Backend Engineer",
    department="Engineering",
    min_experience_years=3.0,
    min_education="Bachelor's",
    required_skills='["Python", "FastAPI", "Docker", "SQL"]',
    nice_to_have_skills='["PostgreSQL", "Redis"]',
    description="We need a backend engineer with Python, FastAPI, and Docker microservices experience."
)

RESUME_TEMPLATE = """
{header}
Summary:
Backend developer with 5 years of experience building resilient microservices and distributed APIs.
{personal_details}
Technical Skills:
- Languages & Frameworks: Python, FastAPI, Django, Flask, SQL, Bash
- Databases & Queues: PostgreSQL, Redis, SQLAlchemy
- DevOps & Tools: Docker, Git, Linux
Experience:
Senior Backend Developer | NovaCloud (2022 - Present)
- Architected and deployed 15+ FastAPI microservices handling 25M daily requests.
- Implemented PostgreSQL schema optimizations reducing query latency by 45%.
Backend Engineer | DataSphere (2019 - 2022)
- Built scalable REST APIs using Python and SQL with comprehensive unit testing.
Education:
{education_line}
"""

def test_bias_immunity_across_demographics_and_institutions():
    """
    Core Phase 2 Bias Test:
    Confirms that changing candidate name, college institution prestige,
    graduation year, and gender markers produces 100% identical factor scores.
    """
    # Candidate A: Male name, Ivy League (Stanford University), recent grad
    resume_a_text = RESUME_TEMPLATE.format(
        header="Alexander Vance - Senior Software Engineer",
        personal_details="Contact: alex.vance@stanford.edu | Phone: (650) 555-0199 | Pronouns: he/him",
        education_line="Bachelor of Science in Computer Science, Stanford University (Class of 2019)"
    )

    # Candidate B: Female Arabic name, State / Community College, older grad
    resume_b_text = RESUME_TEMPLATE.format(
        header="Fatima Al-Mansoor - Senior Software Engineer",
        personal_details="Contact: fatima.mansoor@gmail.com | Phone: (312) 555-4821 | Pronouns: she/her",
        education_line="Bachelor of Science in Computer Science, University of Phoenix (Graduated 2012)"
    )

    # Candidate C: Non-binary name, No institution specified (just degree)
    resume_c_text = RESUME_TEMPLATE.format(
        header="Jordan Taylor - Senior Software Engineer",
        personal_details="Contact: jtaylor@tech.org | Pronouns: they/them",
        education_line="Bachelor of Science in Computer Science"
    )

    # Extract structured resumes (which applies redaction layer first)
    struct_a = extract_structured_resume(resume_a_text, resume_id=1)
    struct_b = extract_structured_resume(resume_b_text, resume_id=2)
    struct_c = extract_structured_resume(resume_c_text, resume_id=3)

    # Verify that institutions and names were removed from anonymized text
    assert "Stanford" not in struct_a.anonymized_text
    assert "Phoenix" not in struct_b.anonymized_text
    assert "Alexander" not in struct_a.anonymized_text
    assert "Fatima" not in struct_b.anonymized_text

    # Evaluate all three against the identical job profile
    weights = ScoringWeights(0.40, 0.30, 0.20, 0.10)
    score_a = evaluate_candidate(struct_a, JOB_FIXTURE, resume_id=1, filename="alex.pdf", weights=weights)
    score_b = evaluate_candidate(struct_b, JOB_FIXTURE, resume_id=2, filename="fatima.pdf", weights=weights)
    score_c = evaluate_candidate(struct_c, JOB_FIXTURE, resume_id=3, filename="jordan.pdf", weights=weights)

    # Check identical factor scores
    assert score_a.skills_score == score_b.skills_score == score_c.skills_score
    assert score_a.experience_score == score_b.experience_score == score_c.experience_score
    assert score_a.education_score == score_b.education_score == score_c.education_score
    assert score_a.projects_score == score_b.projects_score == score_c.projects_score
    assert score_a.weighted_final_score == score_b.weighted_final_score == score_c.weighted_final_score
    assert score_a.percentage_score == score_b.percentage_score == score_c.percentage_score

def test_college_redaction_inside_project_descriptions():
    """
    Verifies that college names mentioned inside project or experience text are redacted.
    """
    text = "Developed a clinical NLP pipeline as a student researcher at Harvard University Medical School."
    res = redact_personal_and_institutional_data(text)
    assert "Harvard" not in res.anonymized_text
    assert "[REDACTED_INSTITUTION]" in res.anonymized_text

def test_hard_requirement_flagging_without_rejection():
    """
    Verifies that candidates missing min experience are flagged with a notice
    rather than being discarded or auto-rejected.
    """
    junior_text = """
    Jordan Lee - Junior Developer
    Summary: Junior engineer with 1 year experience in Python.
    Experience:
    Junior Dev | TechCorp (2025 - Present)
    - Wrote basic Python scripts.
    Education:
    Bachelor of Science in Computer Science
    """
    struct_junior = extract_structured_resume(junior_text, resume_id=4)
    score = evaluate_candidate(struct_junior, JOB_FIXTURE, resume_id=4, filename="junior.pdf")

    # Candidate has score and rank, but has an active flag
    assert score.weighted_final_score > 0.0
    assert len(score.hard_requirement_flags) > 0
    assert any("Experience Requirement Flag" in flag for flag in score.hard_requirement_flags)

def test_adjustable_weights_behavior():
    """
    Verifies that modifying weight configurations deterministically alters final score
    when factor scores differ.
    """
    # Candidate with high skills (1.0) but low experience (0.33)
    cand_text = """
    Candidate X
    Summary: Developer with 1 year experience in Python, FastAPI, Docker, and SQL.
    Technical Skills: Python, FastAPI, Docker, SQL, PostgreSQL, Redis
    Experience:
    Junior Engineer (2025 - Present)
    - Developed backend APIs.
    Education:
    Bachelor of Science in Computer Science
    """
    struct = extract_structured_resume(cand_text, resume_id=5)

    weights_skills_heavy = ScoringWeights(skills_weight=0.80, experience_weight=0.10, projects_weight=0.05, education_weight=0.05)
    weights_exp_heavy = ScoringWeights(skills_weight=0.10, experience_weight=0.80, projects_weight=0.05, education_weight=0.05)

    score_1 = evaluate_candidate(struct, JOB_FIXTURE, resume_id=5, filename="dev.pdf", weights=weights_skills_heavy)
    score_2 = evaluate_candidate(struct, JOB_FIXTURE, resume_id=5, filename="dev.pdf", weights=weights_exp_heavy)

    # When skills are prioritized (0.80), candidate score should be significantly higher than when experience is prioritized
    assert score_1.weighted_final_score > score_2.weighted_final_score
