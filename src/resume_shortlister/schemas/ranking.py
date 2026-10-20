from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ScoringWeightsSchema(BaseModel):
    skills_weight: float = Field(0.40, ge=0.0, le=1.0, json_schema_extra={"example": 0.40})
    experience_weight: float = Field(0.30, ge=0.0, le=1.0, json_schema_extra={"example": 0.30})
    projects_weight: float = Field(0.20, ge=0.0, le=1.0, json_schema_extra={"example": 0.20})
    education_weight: float = Field(0.10, ge=0.0, le=1.0, json_schema_extra={"example": 0.10})

class RankedCandidate(BaseModel):
    rank: int
    resume_id: int
    candidate_id: str = "CAND-0001"
    filename: str
    similarity_score: float = Field(..., description="Weighted final score (0.0 to 1.0)")
    percentage_score: float = Field(..., description="Score as percentage (0 to 100%)")
    
    # Phase 2: Factor breakdown
    skills_score: float = 0.0
    experience_score: float = 0.0
    projects_score: float = 0.0
    education_score: float = 0.0
    hard_requirement_flags: List[str] = Field(default_factory=list)
    
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preview_snippet: str = ""
    anonymized_preview: str = ""

    # Phase 3: Explainability & HR Controls
    hr_status: str = "Shortlisted"
    hr_notes: str = ""
    identity_revealed: bool = False
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    interview_questions: List[Dict[str, str]] = Field(default_factory=list)
    score_rationale: str = ""

class HROverrideRequest(BaseModel):
    hr_status: Optional[str] = None
    hr_notes: Optional[str] = None
    identity_revealed: Optional[bool] = None

class RankingRequest(BaseModel):
    job_id: int
    resume_ids: Optional[List[int]] = None
    engine: str = Field("transformer", json_schema_extra={"example": "transformer"})
    mode: str = Field("multifactor", json_schema_extra={"example": "multifactor"})
    weights: Optional[ScoringWeightsSchema] = None

class RankingResponse(BaseModel):
    job_id: int
    job_title: str
    total_candidates: int
    engine_used: str
    scoring_mode: str = "multifactor"
    ranked_at: datetime
    weights_used: Optional[ScoringWeightsSchema] = None
    candidates: List[RankedCandidate]
