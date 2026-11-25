
from pydantic import BaseModel, Field
from typing import Optional, Literal


class JobPosting(BaseModel):
    job_id: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = Field(min_length=1)

    employment_type: Literal[
        "Internship", "Full-time", "Part-time"
    ] = "Internship"

    work_mode: Literal[
        "Remote", "On-site", "Hybrid", "Not specified"
    ] = "Not specified"

    job_description: str = Field(min_length=1)

    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)

    experience_requirements: Optional[str] = None
    education_requirements: Optional[str] = None

    domain: str = Field(min_length=1)

    source_type: Literal["Real", "Synthetic"]
    source_url: Optional[str] = None
    collected_date: Optional[str] = None
