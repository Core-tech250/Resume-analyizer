from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    char_count: int
    word_count: int
    preview_snippet: str
    ocr_used: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResumeUploadResult(BaseModel):
    filename: str
    status: str
    resume_id: Optional[int] = None
    char_count: Optional[int] = None
    word_count: Optional[int] = None
    error: Optional[str] = None
    ocr_used: bool = False

class ResumeUploadResponse(BaseModel):
    total_uploaded: int
    successful: int
    failed: int
    results: List[ResumeUploadResult]
