import re
import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

from src.resume_shortlister.anonymizer.redactor import redact_personal_and_institutional_data
from src.resume_shortlister.anonymizer.synonyms import match_skills_in_text, SKILL_SYNONYMS

logger = logging.getLogger(__name__)

DEGREE_HIERARCHY = {
    "ph.d.": 4,
    "phd": 4,
    "doctorate": 4,
    "master's": 3,
    "masters": 3,
    "ms": 3,
    "m.s.": 3,
    "m.tech": 3,
    "mtech": 3,
    "mba": 3,
    "bachelor's": 2,
    "bachelors": 2,
    "bs": 2,
    "b.s.": 2,
    "b.tech": 2,
    "btech": 2,
    "b.e.": 2,
    "be": 2,
    "associate": 1,
    "diploma": 1,
}

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12
}

@dataclass
class StructuredResume:
    anonymous_id: str
    degree_level: str
    field_of_study: str
    experience_years: float
    roles: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    anonymized_text: str = ""
    redactions_count: int = 0
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def extract_degree_and_field(text: str) -> tuple[str, str]:
    """
    Extracts canonical degree level and field of study without institutional names.
    """
    text_lower = text.lower()
    
    # 1. Degree level
    degree_level = "None"
    highest_rank = 0
    
    for degree_key, rank in DEGREE_HIERARCHY.items():
        pattern = r'\b' + re.escape(degree_key) + r'\b'
        if re.search(pattern, text_lower) and rank > highest_rank:
            highest_rank = rank
            if rank == 4:
                degree_level = "Ph.D."
            elif rank == 3:
                degree_level = "Master's"
            elif rank == 2:
                degree_level = "Bachelor's"
            elif rank == 1:
                degree_level = "Associate / Diploma"

    # 2. Field of study
    field_of_study = "General"
    fields = [
        ("Computer Science", [r'computer science', r'\bcs\b', r'software engineering']),
        ("Artificial Intelligence & ML", [r'artificial intelligence', r'machine learning', r'data science']),
        ("Information Technology", [r'information technology', r'\bit\b']),
        ("Electrical & Electronics", [r'electrical engineering', r'electronics', r'telecommunications']),
        ("Business Administration", [r'business administration', r'management', r'finance', r'marketing']),
        ("Design & Media", [r'interactive media', r'design', r'human-computer interaction', r'graphic design']),
        ("Mechanical Engineering", [r'mechanical engineering']),
    ]
    
    for canon_field, patterns in fields:
        for p in patterns:
            if re.search(p, text_lower):
                field_of_study = canon_field
                break
        if field_of_study != "General":
            break

    return degree_level, field_of_study

def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merges overlapping or contiguous month intervals into non-overlapping disjoint intervals.
    Solves the double-counting problem when candidates list overlapping jobs/projects.
    """
    if not intervals:
        return []
    
    # Sort intervals by start month
    sorted_inv = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [sorted_inv[0]]
    
    for current_start, current_end in sorted_inv[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            # Overlapping or contiguous interval -> extend last interval
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
            
    return merged

def extract_experience_years(text: str) -> float:
    """
    Extracts experience duration using disjoint calendar interval union.
    Guarantees no double-counting for concurrent roles or overlapping dates.
    """
    current_year = 2026
    current_month = 10
    current_month_index = current_year * 12 + current_month

    # 1. Direct mention: e.g. "6 years of experience", "4+ years experience"
    exp_pattern = r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience'
    matches = re.findall(exp_pattern, text, flags=re.IGNORECASE)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            pass

    intervals: List[Tuple[int, int]] = []

    # 2. Month + Year ranges: e.g. "Jan 2020 - Mar 2023", "06/2019 - Present"
    month_pattern = r'\b([A-Za-z]{3,9}|\d{1,2})[/\s]+(19\d{2}|20\d{2})\s*[-–—to]+\s*([A-Za-z]{3,9}|\d{1,2}|Present|Current)?(?:[/\s]+(19\d{2}|20\d{2}))?\b'
    for match in re.finditer(month_pattern, text, flags=re.IGNORECASE):
        m1_raw, y1_raw, m2_raw, y2_raw = match.groups()
        try:
            y1 = int(y1_raw)
            m1 = MONTH_MAP.get(m1_raw.lower(), int(m1_raw) if m1_raw.isdigit() and 1 <= int(m1_raw) <= 12 else 1)
            start_idx = y1 * 12 + m1

            if not m2_raw or m2_raw.lower() in ['present', 'current']:
                end_idx = current_month_index
            elif y2_raw:
                y2 = int(y2_raw)
                m2 = MONTH_MAP.get(m2_raw.lower(), int(m2_raw) if m2_raw.isdigit() and 1 <= int(m2_raw) <= 12 else 12)
                end_idx = y2 * 12 + m2
            else:
                end_idx = start_idx + 12

            if 1970 * 12 <= start_idx <= current_month_index and start_idx <= end_idx:
                intervals.append((start_idx, end_idx))
        except Exception:
            continue

    # 3. Simple Year-Year ranges: e.g. "2020 - 2023", "2021 - Present"
    year_pattern = r'\b(19\d{2}|20\d{2})\s*[-–—to]+\s*(Present|Current|19\d{2}|20\d{2})\b'
    for match in re.finditer(year_pattern, text, flags=re.IGNORECASE):
        start_yr, end_yr = match.groups()
        try:
            s_yr = int(start_yr)
            e_yr = current_year if end_yr.lower() in ['present', 'current'] else int(end_yr)
            if 1970 <= s_yr <= current_year and s_yr <= e_yr:
                intervals.append((s_yr * 12, e_yr * 12))
        except Exception:
            continue

    if intervals:
        merged = _merge_intervals(intervals)
        total_months = sum(end - start for start, end in merged)
        if total_months > 0:
            return round(total_months / 12.0, 1)

    return 1.0  # Conservative default if no explicit dates found

def extract_sections(text: str) -> Dict[str, str]:
    """
    Splits resume into recognized logical sections using robust regex pattern matching.
    Handles variations like 'Work Experience & History', 'Selected Technical Projects', etc.
    """
    lines = text.splitlines()
    sections: Dict[str, List[str]] = {
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "other": []
    }
    
    current_sec = "summary"
    
    # Robust regex patterns for section headers (education checked before experience to avoid 'educational background' mismatch)
    header_patterns = [
        ("education", r'^(?:.*?\s+)?(?:education|educational|academics|academic\s+background|qualifications|degrees)\b'),
        ("skills", r'^(?:.*?\s+)?(?:skills|technologies|competencies|tech\s+stack|tools|proficiencies)\b'),
        ("projects", r'^(?:.*?\s+)?(?:projects|portfolio|open\s+source|project\s+work)\b'),
        ("experience", r'^(?:.*?\s+)?(?:work\s+experience|professional\s+experience|employment\s+history|experience|work\s+history|employment)\b')
    ]

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        # Clean line for header check
        clean_header = re.sub(r'^[#*•\-\d\.\s]+', '', line_strip).strip()
        
        # Section headers are generally short (<= 60 chars)
        matched_header = None
        if len(clean_header) <= 60:
            for sec_name, pattern in header_patterns:
                if re.match(pattern, clean_header, flags=re.IGNORECASE):
                    matched_header = sec_name
                    break
                
        if matched_header:
            current_sec = matched_header
        else:
            sections[current_sec].append(line_strip)

    return {k: "\n".join(v).strip() for k, v in sections.items()}

def extract_structured_resume(raw_text: str, resume_id: Optional[int] = None) -> StructuredResume:
    """
    Structured Extraction Pipeline:
    1. Redacts PII, college names, gender pronouns, and personal data.
    2. Identifies degree level and field of study.
    3. Calculates experience duration with disjoint interval merging.
    4. Extracts demonstrated technical skills via synonym canonicalization.
    5. Extracts structured roles and projects from the anonymized text.
    """
    # 1. Apply Redaction Layer First!
    redaction_res = redact_personal_and_institutional_data(raw_text)
    anonymized = redaction_res.anonymized_text

    # 2. Extract sections
    sections = extract_sections(anonymized)

    # 3. Degree & Field (extracted from education section or full text)
    edu_text = sections.get("education", "") or anonymized
    degree_level, field_of_study = extract_degree_and_field(edu_text)

    # 4. Experience Years with interval merging
    exp_text = sections.get("experience", "") or anonymized
    exp_years = extract_experience_years(exp_text)

    # 5. Skills extraction across full text using synonym-aware dictionary
    all_target_skills = list(SKILL_SYNONYMS.keys())
    matched_skills = match_skills_in_text(anonymized, all_target_skills)

    # Also capture bullet points from skills section
    skills_sec_text = sections.get("skills", "")
    for line in skills_sec_text.splitlines():
        clean_line = re.sub(r'^[-*•\d\.\s]+', '', line)
        for token in re.split(r'[,|•;]', clean_line):
            token_clean = token.strip()
            if 2 <= len(token_clean) <= 30 and token_clean.lower() not in [s.lower() for s in matched_skills]:
                # Exclude common non-skill words
                if token_clean.lower() not in ["languages", "frameworks", "tools", "databases", "platforms"]:
                    matched_skills.append(token_clean)

    # 6. Extract Projects
    projects = []
    proj_text = sections.get("projects", "")
    if proj_text:
        proj_blocks = re.split(r'\n(?=[-•*]|\b[A-Z][a-zA-Z\s]{3,40}:|\bProject\s+\d+:)', proj_text)
        for b in proj_blocks:
            b_clean = b.strip()
            if len(b_clean) > 20:
                projects.append({
                    "title": b_clean.splitlines()[0][:60],
                    "description": b_clean
                })

    # 7. Extract Roles
    roles = []
    if exp_text:
        role_blocks = re.split(r'\n(?=[-•*]|\b[A-Za-z\s]+(?:Developer|Engineer|Manager|Specialist|Lead|Architect|Intern|Analyst|Consultant)\b)', exp_text)
        for r_block in role_blocks:
            r_clean = r_block.strip()
            if len(r_clean) > 20:
                roles.append({
                    "description": r_clean
                })

    anon_id = f"CAND-{(resume_id or abs(hash(raw_text))) % 10000:04d}"

    return StructuredResume(
        anonymous_id=anon_id,
        degree_level=degree_level,
        field_of_study=field_of_study,
        experience_years=exp_years,
        roles=roles,
        projects=projects,
        skills=list(dict.fromkeys(matched_skills)),
        anonymized_text=anonymized,
        redactions_count=redaction_res.redactions_count,
        raw_text=raw_text
    )
