import csv
import io
import json
from typing import List, Dict, Any

def export_shortlist_to_csv(candidate_data: List[Dict[str, Any]]) -> str:
    """
    Exports the ranked candidate shortlist to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Rank",
        "Candidate ID",
        "Filename",
        "Final Match %",
        "Skills Fit %",
        "Experience Fit %",
        "Projects Fit %",
        "Education Fit %",
        "Matched Skills",
        "Missing Required Skills",
        "HR Status",
        "Recruiter Notes",
        "Flags"
    ])

    for c in candidate_data:
        writer.writerow([
            c.get("rank", ""),
            c.get("candidate_id", ""),
            c.get("filename", ""),
            f"{c.get('percentage_score', 0):.1f}%",
            f"{c.get('skills_score', 0):.1f}%",
            f"{c.get('experience_score', 0):.1f}%",
            f"{c.get('projects_score', 0):.1f}%",
            f"{c.get('education_score', 0):.1f}%",
            ", ".join(c.get("matched_skills", [])),
            ", ".join(c.get("missing_skills", [])),
            c.get("hr_status", "Shortlisted"),
            c.get("hr_notes", ""),
            "; ".join(c.get("hard_requirement_flags", []))
        ])

    return output.getvalue()
