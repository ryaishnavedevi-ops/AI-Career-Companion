
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import Candidate
from ..schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse
)

router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=201
)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    candidate = Candidate(**student.model_dump())
    db.add(candidate)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Student email already exists"
        )

    db.refresh(candidate)
    return candidate


@router.get(
    "/{candidate_id}",
    response_model=StudentResponse
)
def get_student(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return candidate


@router.put(
    "/{candidate_id}",
    response_model=StudentResponse
)
def update_student(
    candidate_id: str,
    student: StudentUpdate,
    db: Session = Depends(get_db)
):
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    updates = student.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)

    return candidate
