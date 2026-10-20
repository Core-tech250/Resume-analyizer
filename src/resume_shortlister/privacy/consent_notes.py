CONSENT_NOTICE = """
### Candidate Data Handling & Algorithmic Transparency Notice

1. **Purpose of Processing**: Resumes submitted to this organization are evaluated solely to support recruiter shortlisting against job competency requirements.
2. **Anonymization by Design**: The automated evaluation layer operates under strict identity blinding. Personal identifiers (names, contact info, photo, age, gender) and educational institution brand names are redacted prior to scoring.
3. **Human Decision-Making**: No applicant is automatically rejected by an algorithm. All shortlisting, interview invitations, and hiring determinations remain exclusively with human hiring managers and HR personnel.
4. **Data Retention Policy**: Candidate materials are retained for a maximum of 90 days following vacancy closure, after which all document records are permanently deleted.
5. **Candidate Rights**: Applicants retain the right to request deletion of their profile materials at any point during the recruitment process.
"""

def get_compliance_notice() -> str:
    return CONSENT_NOTICE.strip()
