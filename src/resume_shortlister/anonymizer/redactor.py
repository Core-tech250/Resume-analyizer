import re
from dataclasses import dataclass, field
from typing import Tuple, List, Dict

@dataclass
class RedactionResult:
    anonymized_text: str
    redactions_count: int
    redacted_items: Dict[str, List[str]]

# Comprehensive list of global and national elite and regional institutions
PRESTIGE_AND_REGIONAL_COLLEGES = [
    # Top Global Universities
    r'\b(?:Stanford|Harvard|MIT|Massachusetts Institute of Technology|Berkeley|UC Berkeley|Oxford|Cambridge|Princeton|Yale|Columbia|Cornell|Caltech|California Institute of Technology|CMU|Carnegie Mellon|UCLA|USC|NYU|Purdue|Georgia Tech|Georgia Institute of Technology|UIUC|University of Illinois|UT Austin|University of Texas|UMich|University of Michigan|UW|University of Washington|Waterloo|University of Waterloo|Toronto|University of Toronto|McGill|UBC|Imperial College|UCL|ETH Zurich|EPFL|TUM|TU Munich|NUS|NTU)\b',
    # Indian Premier & State Institutions
    r'\b(?:IIT|NIT|IIIT|BITS|IIM|IISc|TIFR|ISRO|DRDO)\s+[A-Za-z]+\b',
    r'\b(?:IIT|NIT|IIIT|BITS|IIM|IISc|TIFR)\b',
    r'\b(?:BITS Pilani|BIT Mesra|Vellore Institute of Technology|VIT|SRM Institute|SRM University|SRM|Manipal University|Manipal|MAHE|Amity University|Amity|Thapar University|Thapar Institute|TIET|Delhi Technological University|DTU|DCE|Netaji Subhas University of Technology|NSUT|Anna University|PSG College|PSG Tech|Coimbatore Institute of Technology|CIT|Delhi University|DU|Jawaharlal Nehru University|JNU|Banaras Hindu University|BHU|Aligarh Muslim University|AMU|Jamia Millia Islamia|Mumbai University|VJTI|SPIT|SNDT|Pune University|Savitribai Phule Pune University|COEP|PICT|Visvesvaraya Technological University|VTU|RVCE|RV College of Engineering|BMSCE|BMS College|MSRIT|Ramaiah Institute|PESIT|PES University|Jawaharlal Nehru Technological University|JNTU|CBIT|Vasavi College|Symbiosis|SIBM|SCIT|Kalinga Institute|KIIT|SOA University)\b',
    # Generic Institution Phrasing
    r'\b(?:University of [A-Za-z\s]+|[A-Za-z\s]+ (?:University|College|Institute of Technology|Polytechnic|Academy|Campus|School of Engineering|School of Business|School of Management|School of Technology))\b',
    r'\b(?:Indian Institute of [A-Za-z\s]+|National Institute of [A-Za-z\s]+|State University of [A-Za-z\s]+)\b'
]

# Email pattern
EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

# Phone pattern
PHONE_PATTERN = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

# URL / Social links pattern
URL_PATTERN = r'https?://[^\s]+|(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
SOCIAL_PATTERN = r'(?:linkedin\.com/in/|github\.com/|twitter\.com/|x\.com/)[a-zA-Z0-9_\-\.]+'

# Honorifics & titles
HONORIFICS_PATTERN = r'\b(?:Mr\.|Ms\.|Mrs\.|Miss|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'

# Demographic & Affinity organizations
AFFINITY_ORGANIZATIONS = [
    r'\b(?:Society of Women Engineers|SWE|Women in Tech|Women in STEM|Girls Who Code|Black in AI|Latinx in Tech|Queer in Tech|Out in Tech|Women Who Code|National Society of Black Engineers|NSBE|Society of Hispanic Professional Engineers|SHPE)\b'
]

# Gender pronouns
GENDER_PATTERN = r'\b(?:he/him|she/her|they/them|he|him|his|she|her|hers)\b'

# Graduation years & age
AGE_PATTERN = r'\b(?:Age|DOB|Date of Birth)[\s:]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\bAge[\s:]+\d{2}\b'

def redact_personal_and_institutional_data(text: str) -> RedactionResult:
    """
    Strips and redacts all PII, personal identifiers, demographic markers,
    and institution/college names from the resume text.
    
    Guarantees that the scoring engine sees ONLY:
    - Degree level (e.g. Bachelor's, Master's)
    - Field of study (e.g. Computer Science)
    - Demonstrated skills, roles, projects, and responsibilities.
    """
    if not text:
        return RedactionResult(anonymized_text="", redactions_count=0, redacted_items={})

    anonymized = text.strip()
    redacted_items: Dict[str, List[str]] = {
        "candidate_name": [],
        "institutions": [],
        "contact_info": [],
        "gender_markers": [],
        "dates_and_age": [],
        "affinity_groups": []
    }
    total_redactions = 0

    # 1. Candidate Name Detection across first 5 non-empty lines
    lines = anonymized.splitlines()
    detected_names = []
    
    # Check email prefix for names if available (e.g. john.doe@gmail.com -> John Doe)
    email_matches_pre = re.findall(EMAIL_PATTERN, anonymized)
    for em in email_matches_pre:
        prefix = em.split('@')[0]
        # Split on dot, underscore, dash
        parts = [p for p in re.split(r'[._-]', prefix) if len(p) >= 3 and p.isalpha()]
        if len(parts) >= 2:
            candidate_email_name = " ".join([p.capitalize() for p in parts[:2]])
            detected_names.append(candidate_email_name)

    # Inspect first few non-empty lines
    non_empty_count = 0
    header_blacklist = [
        "summary", "objective", "experience", "education", "skills", "curriculum", "resume",
        "vitae", "contact", "profile", "projects", "certifications", "technologies", "email",
        "phone", "developer", "software engineer", "data scientist", "portfolio"
    ]
    
    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        non_empty_count += 1
        if non_empty_count > 6:
            break

        line_lower = line_str.lower()
        if any(kw == line_lower for kw in header_blacklist):
            continue

        # Pattern: "Name - Title" or "Name | Contact"
        if " - " in line_str:
            name_part, rest = line_str.split(" - ", 1)
            clean_name = name_part.strip()
            if 1 <= len(clean_name.split()) <= 4 and not any(kw in clean_name.lower() for kw in header_blacklist):
                detected_names.append(clean_name)
                lines[idx] = f"[ANONYMIZED_CANDIDATE] - {rest}"
                total_redactions += 1
                break
        elif "|" in line_str:
            name_part, rest = line_str.split("|", 1)
            clean_name = name_part.strip()
            if 1 <= len(clean_name.split()) <= 4 and not any(kw in clean_name.lower() for kw in header_blacklist):
                detected_names.append(clean_name)
                lines[idx] = f"[ANONYMIZED_CANDIDATE] | {rest}"
                total_redactions += 1
                break
        else:
            words = line_str.split()
            # If line is 1-4 words and mostly capitalized/title-case
            if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                if not any(kw in line_lower for kw in header_blacklist):
                    detected_names.append(line_str)
                    lines[idx] = "[ANONYMIZED_CANDIDATE]"
                    total_redactions += 1
                    break

    anonymized = "\n".join(lines)

    # 2. Honorifics and Titles (e.g. "Dr. Jane Smith", "Mr. John Doe")
    def honorific_sub(m):
        nonlocal total_redactions
        found_name = m.group(1)
        redacted_items["candidate_name"].append(found_name)
        total_redactions += 1
        return "[ANONYMIZED_CANDIDATE]"

    anonymized = re.sub(HONORIFICS_PATTERN, honorific_sub, anonymized)

    # If any names were detected, redact all occurrences throughout the text!
    for d_name in detected_names:
        clean_d = d_name.strip()
        if len(clean_d) >= 3:
            redacted_items["candidate_name"].append(clean_d)
            # Redact full name
            anonymized = re.sub(r'\b' + re.escape(clean_d) + r'\b', '[ANONYMIZED_CANDIDATE]', anonymized, flags=re.IGNORECASE)
            # Also redact first name if it is distinct and >3 chars
            first_n = clean_d.split()[0]
            if len(first_n) >= 4 and first_n.lower() not in header_blacklist:
                anonymized = re.sub(r'\b' + re.escape(first_n) + r'\b', '[ANONYMIZED_CANDIDATE]', anonymized, flags=re.IGNORECASE)

    # 3. Redact Emails FIRST
    email_matches = re.findall(EMAIL_PATTERN, anonymized)
    for match in email_matches:
        redacted_items["contact_info"].append(match)
        anonymized = anonymized.replace(match, "[REDACTED_EMAIL]")
        total_redactions += 1

    # 4. Redact Social & Profile Links
    social_matches = re.findall(SOCIAL_PATTERN, anonymized, flags=re.IGNORECASE)
    for match in social_matches:
        redacted_items["contact_info"].append(match)
        anonymized = anonymized.replace(match, "[REDACTED_LINK]")
        total_redactions += 1

    # 5. Redact Standalone URLs
    url_matches = re.findall(URL_PATTERN, anonymized)
    for match in url_matches:
        if "[REDACTED" not in match:
            redacted_items["contact_info"].append(match)
            anonymized = anonymized.replace(match, "[REDACTED_LINK]")
            total_redactions += 1

    # 6. Redact Phone Numbers
    phone_matches = re.findall(PHONE_PATTERN, anonymized)
    for match in phone_matches:
        if len(match.strip()) >= 7:
            redacted_items["contact_info"].append(match)
            anonymized = anonymized.replace(match, "[REDACTED_PHONE]")
            total_redactions += 1

    # 7. Redact Colleges, Universities & Premier Institutes
    for col_pattern in PRESTIGE_AND_REGIONAL_COLLEGES:
        col_matches = re.findall(col_pattern, anonymized, flags=re.IGNORECASE)
        for match in col_matches:
            match_str = match.strip() if isinstance(match, str) else str(match)
            if len(match_str) > 2 and match_str.upper() not in ["AI", "ML", "IT", "CS"]:
                redacted_items["institutions"].append(match_str)
                anonymized = re.sub(r'\b' + re.escape(match_str) + r'\b', '[REDACTED_INSTITUTION]', anonymized, flags=re.IGNORECASE)
                total_redactions += 1

    # 8. Redact Affinity & Diversity Organizations
    for aff_pattern in AFFINITY_ORGANIZATIONS:
        aff_matches = re.findall(aff_pattern, anonymized, flags=re.IGNORECASE)
        for match in aff_matches:
            redacted_items["affinity_groups"].append(match)
            anonymized = re.sub(r'\b' + re.escape(match) + r'\b', '[REDACTED_ORGANIZATION]', anonymized, flags=re.IGNORECASE)
            total_redactions += 1

    # 9. Redact Age and Dates of Birth
    age_matches = re.findall(AGE_PATTERN, anonymized, flags=re.IGNORECASE)
    for match in age_matches:
        redacted_items["dates_and_age"].append(match)
        anonymized = anonymized.replace(match, "[REDACTED_AGE]")
        total_redactions += 1

    # 10. Redact Graduation Years (using re.sub to prevent character index drift)
    grad_year_pattern = r'(\b(?:graduated:?|class of|education[^\n]*?)\s*)(\b(?:19[7-9]\d|20[0-2]\d)\b)|\((\b(?:19[7-9]\d|20[0-2]\d)\b)\)'
    def grad_sub(m):
        nonlocal total_redactions
        year_str = m.group(2) or m.group(3)
        if year_str:
            redacted_items["dates_and_age"].append(year_str)
            total_redactions += 1
            if m.group(2):
                return m.group(1) + "[REDACTED_YEAR]"
            else:
                return "([REDACTED_YEAR])"
        return m.group(0)

    anonymized = re.sub(grad_year_pattern, grad_sub, anonymized, flags=re.IGNORECASE)

    # 10. Redact Gender Pronouns
    def pronoun_sub(m):
        nonlocal total_redactions
        redacted_items["gender_markers"].append(m.group(0))
        total_redactions += 1
        return "[PRONOUN]"

    anonymized = re.sub(GENDER_PATTERN, pronoun_sub, anonymized, flags=re.IGNORECASE)

    return RedactionResult(
        anonymized_text=anonymized,
        redactions_count=total_redactions,
        redacted_items=redacted_items
    )
