import pytest
from src.resume_shortlister.anonymizer.redactor import redact_personal_and_institutional_data
from src.resume_shortlister.parsers.structured_extractor import (
    extract_sections,
    extract_experience_years,
    extract_structured_resume
)

def test_enhanced_college_and_institution_redaction():
    """
    Verifies that regional, national, and international colleges are thoroughly redacted,
    including institutions like BITS Pilani, Georgia Tech, and Vellore Institute of Technology.
    """
    text = """
    Dr. Rajesh Sharma
    rajesh.sharma@example.com | +1 555-019-2834
    Education:
    - B.Tech from BITS Pilani (2018)
    - M.S. from Georgia Tech (2020)
    - Ph.D. research at Vellore Institute of Technology (2023)
    Affiliations: Active member of Society of Women Engineers ally network.
    """
    res = redact_personal_and_institutional_data(text)
    anon = res.anonymized_text

    # Verify names & honorifics redacted
    assert "Rajesh" not in anon
    assert "Sharma" not in anon
    assert "Dr." not in anon

    # Verify colleges redacted
    assert "BITS Pilani" not in anon
    assert "Georgia Tech" not in anon
    assert "Vellore Institute of Technology" not in anon
    assert "[REDACTED_INSTITUTION]" in anon

    # Verify affinity groups redacted
    assert "Society of Women Engineers" not in anon
    assert "[REDACTED_ORGANIZATION]" in anon

    # Verify contact info redacted
    assert "rajesh.sharma@example.com" not in anon
    assert "[REDACTED_EMAIL]" in anon
    assert "+1 555-019-2834" not in anon


def test_flexible_section_header_recognition():
    """
    Verifies that real-world header variations (e.g. 'Work Experience & History',
    'Technical Skills & Tools', 'Selected Academic Projects') are recognized correctly.
    """
    resume_text = """
    Professional Summary:
    Full stack engineer with 4 years experience.

    Technical Skills & Tools:
    Python, FastAPI, Docker, PostgreSQL, React, TypeScript

    Work Experience & History:
    Senior Software Engineer (2022 - Present)
    - Built scalable microservices using FastAPI and Kafka.

    Selected Academic & Personal Projects:
    Project 1: Distributed Cache in Go
    - Implemented consistent hashing and LRU eviction.

    Educational Qualifications & Background:
    B.Tech in Computer Science (2018 - 2022)
    """
    sections = extract_sections(resume_text)

    assert "skills" in sections
    assert "Python" in sections["skills"]

    assert "experience" in sections
    assert "Senior Software Engineer" in sections["experience"]

    assert "projects" in sections
    assert "Distributed Cache in Go" in sections["projects"]

    assert "education" in sections
    assert "Computer Science" in sections["education"]


def test_experience_interval_union_merging():
    """
    Verifies that overlapping job dates are merged as disjoint intervals
    rather than double-counting experience tenure.
    """
    # Overlapping intervals: 2021-2023 (2 yrs) and 2022-2024 (2 yrs)
    # Total merged duration should be 2021 to 2024 = 3.0 years, NOT 4.0 years!
    overlapping_text = """
    Work Experience:
    Software Developer | 2021 - 2023
    Contract Consultant | 2022 - 2024
    """
    exp_years = extract_experience_years(overlapping_text)
    assert exp_years == 3.0
