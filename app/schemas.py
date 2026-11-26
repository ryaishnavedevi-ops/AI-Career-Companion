
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Any


# Schema for creating a student profile
class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None


# Schema for updating a student profile
class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None


# Schema for returning student information
class StudentResponse(BaseModel):
    candidate_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Schema for generating internship recommendations
class RecommendationRequest(BaseModel):

    candidate_id: str = Field(
        min_length=1,
        max_length=100
    )

    resume_id: str = Field(
        min_length=1,
        max_length=100
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        strict=True
    )


# Schema for returning internship recommendations
class RecommendationResponse(BaseModel):

    candidate_id: str
    resume_id: str

    ranking_statistics: dict[str, Any]

    retrieval_statistics: dict[str, Any]

    queries: list[dict[str, Any]]

    recommendations: list[dict[str, Any]]
