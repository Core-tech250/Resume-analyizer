from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class UserRole(str, Enum):
    HR_ADMIN = "hr_admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"

@dataclass
class CompanyWorkspace:
    company_id: int
    name: str
    domain: str
    retention_days: int = 90

@dataclass
class AuthUser:
    user_id: int
    email: str
    role: UserRole
    company_id: int

# Default tenant workspaces
DEFAULT_COMPANIES = [
    CompanyWorkspace(company_id=1, name="Acme Tech Innovations", domain="acmetech.io", retention_days=90),
    CompanyWorkspace(company_id=2, name="NovaCloud Systems", domain="novacloud.com", retention_days=60),
    CompanyWorkspace(company_id=3, name="Optima Health Analytics", domain="optimahealth.org", retention_days=30),
]

def check_permission(user: AuthUser, action: str) -> bool:
    """
    Role-Based Access Control (RBAC) permission enforcement:
    - HR_ADMIN: Full administrative rights (purge data, manage retention, unmask identity, manage jobs)
    - RECRUITER: Operational rights (upload resumes, review candidates, add notes, override status)
    - VIEWER: Read-only access to anonymized shortlists
    """
    if user.role == UserRole.HR_ADMIN:
        return True  # HR Admin has all permissions
        
    if user.role == UserRole.RECRUITER:
        # Recruiters can shortlist, review, override notes, but CANNOT purge data or change global retention
        allowed = {
            "view_shortlist",
            "upload_resumes",
            "run_ranking",
            "add_recruiter_notes",
            "override_candidate_status",
            "unmask_identity",
            "export_reports"
        }
        return action in allowed

    if user.role == UserRole.VIEWER:
        return action in {"view_shortlist", "export_reports"}

    return False
