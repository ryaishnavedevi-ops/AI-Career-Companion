
from .database import SessionLocal
from .models import Resume, ResumeExtraction
from .resume_parser import extract_resume_text
from .structured_extractor import extract_structured_data

import logging

from .ai_extractor import extract_resume_with_ai

logger = logging.getLogger(__name__)


def extract_with_fallback(resume_text):
    try:
        result = extract_resume_with_ai(resume_text)
        logger.info("Resume extracted using Gemini AI")
        return result

    except Exception as error:
        logger.warning(
            "Gemini extraction failed; using rule-based fallback: %s",
            error
        )
        return extract_structured_data(resume_text)


def process_resume(resume_id: str):
    db = SessionLocal()

    try:
        resume = db.get(Resume, resume_id)

        if resume is None:
            raise ValueError("Resume not found")

        text = extract_resume_text(resume.file_path)

        if not text.strip():
            raise ValueError("No readable text found in resume")

        structured_data = extract_with_fallback(text)

        extraction = (
            db.query(ResumeExtraction)
            .filter(ResumeExtraction.resume_id == resume_id)
            .first()
        )

        if extraction is None:
            extraction = ResumeExtraction(
                resume_id=resume_id,
                extracted_data=structured_data
            )
            db.add(extraction)
        else:
            extraction.extracted_data = structured_data

        resume.parsing_status = "completed"

        db.commit()

        return structured_data

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
