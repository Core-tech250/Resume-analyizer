from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class JobProfileCreate(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Senior Python & Backend Engineer"})
    department: Optional[str] = Field("Engineering", json_schema_extra={"example": "Engineering"})
    min_experience_years: float = Field(0.0, ge=0.0, json_schema_extra={"example": 3.0})
    min_education: str = Field("Bachelor's", json_schema_extra={"example": "Bachelor's in Computer Science"})
    required_skills: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Python", "FastAPI", "SQL", "Docker"]})
    nice_to_have_skills: List[str] = Field(default_factory=list, json_schema_extra={"example": ["PostgreSQL", "Redis", "NLP", "CI/CD"]})
    description: str = Field(..., json_schema_extra={"example": "We are looking for a backend engineer to design robust APIs."})

class JobProfileResponse(BaseModel):
    id: int
    title: str
    department: Optional[str]
    min_experience_years: float
    min_education: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
