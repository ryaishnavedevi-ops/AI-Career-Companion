import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db

from ..models import (
    Candidate,
    Resume,
    ResumeExtraction
)

from ..schemas import (
    RecommendationRequest,
    RecommendationResponse
)

from ..student_profile_builder import (
    load_student_profile
)

from ..job_ranking_engine import (
    InternshipRecommendationEngine
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.post(
    "/generate",
    response_model=RecommendationResponse
)
def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):

    # Validate student existence

    candidate = db.get(
        Candidate,
        request.candidate_id
    )

    if candidate is None:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    # Validate resume existence

    resume = db.get(
        Resume,
        request.resume_id
    )

    if resume is None:

        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    # Validate candidate-resume relationship

    if resume.candidate_id != request.candidate_id:

        raise HTTPException(
            status_code=403,
            detail="Resume does not belong to this student"
        )

    # Ensure resume processing is complete

    if resume.parsing_status != "completed":

        raise HTTPException(
            status_code=409,
            detail=(
                "Resume must be processed before "
                "generating recommendations"
            )
        )

    # Verify extracted resume data

    extraction = (
        db.query(ResumeExtraction)
        .filter(
            ResumeExtraction.resume_id
            == request.resume_id
        )
        .first()
    )

    if extraction is None:

        raise HTTPException(
            status_code=409,
            detail="No extracted resume data found"
        )

    # Build the structured student profile

    try:

        profile = load_student_profile(
            db,
            request.candidate_id,
            request.resume_id
        )

    except ValueError:

        logger.exception(
            "Student profile construction failed"
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Unable to construct a valid student "
                "profile from the extracted resume"
            )
        )

    # Ensure the profile contains usable search evidence

    from ..job_query_builder import build_search_queries

    try:

        build_search_queries(profile)

    except ValueError:

        raise HTTPException(
            status_code=422,
            detail=(
                "Insufficient resume information "
                "to generate recommendations"
            )
        )

    # Generate explainable internship recommendations

    try:

        engine = InternshipRecommendationEngine()

        result = engine.recommend(
            profile,
            top_k=request.top_k,
            top_k_per_query=10,
            max_candidates=40
        )

    except Exception:

        logger.exception(
            "Internship recommendation generation failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Recommendation service is currently "
                "unavailable. Please try again later."
            )
        )

    return result