
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from .database import Base


def current_time():
    return datetime.now(timezone.utc)


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    location = Column(String(255), nullable=True)
    professional_summary = Column(String(2000), nullable=True)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(
        DateTime,
        default=current_time,
        onupdate=current_time
    )

    resumes = relationship(
        "Resume",
        back_populates="candidate"
    )


class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    candidate_id = Column(
        String(36),
        ForeignKey("candidates.candidate_id"),
        nullable=False
    )

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)

    upload_date = Column(DateTime, default=current_time)
    parsing_status = Column(
        String(30),
        default="pending"
    )

    candidate = relationship(
        "Candidate",
        back_populates="resumes"
    )

from sqlalchemy import JSON


class ResumeExtraction(Base):
    __tablename__ = "resume_extractions"

    extraction_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    resume_id = Column(
        String(36),
        ForeignKey("resumes.resume_id"),
        nullable=False,
        unique=True
    )

    extracted_data = Column(JSON, nullable=False)

    extracted_at = Column(
        DateTime,
        default=current_time
    )
