
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


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
