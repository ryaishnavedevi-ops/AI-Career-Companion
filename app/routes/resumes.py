
import uuid
import zipfile
from pathlib import Path
from io import BytesIO

from app.models import ResumeExtraction
from app.extraction_service import process_resume


from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, Resume

router = APIRouter(prefix="/resumes", tags=["Resumes"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload/{candidate_id}", status_code=201)
async def upload_resume(
    candidate_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    original_name = Path(
        (file.filename or "").replace("\\", "/")
    ).name
    extension = Path(original_name).suffix.lower()

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )

    try:
        contents = await file.read(MAX_FILE_SIZE + 1)
    finally:
        await file.close()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 5 MB"
        )

    if extension == ".pdf":
        valid_file = contents.startswith(b"%PDF-")
    else:
        try:
            with zipfile.ZipFile(BytesIO(contents)) as archive:
                valid_file = (
                    "word/document.xml" in archive.namelist()
                )
        except (zipfile.BadZipFile, OSError):
            valid_file = False

    if not valid_file:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF or DOCX file"
        )

    resume_id = str(uuid.uuid4())
    saved_name = f"{resume_id}{extension}"
    file_path = UPLOAD_DIR / saved_name

    try:
        file_path.write_bytes(contents)

        resume = Resume(
            resume_id=resume_id,
            candidate_id=candidate_id,
            file_name=original_name,
            file_path=str(file_path),
            file_type=extension,
            file_size=len(contents),
            parsing_status="pending"
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    return {
        "message": "Resume uploaded successfully",
        "resume_id": resume.resume_id,
        "candidate_id": resume.candidate_id,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "file_size": resume.file_size,
        "parsing_status": resume.parsing_status
    }


@router.post("/process/{resume_id}")

def process_uploaded_resume(
    resume_id: str,
    db: Session = Depends(get_db)
):
    resume = db.get(Resume, resume_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    try:
        extracted_data = process_resume(resume_id)

    except (ValueError, OSError, RuntimeError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    return {
        "message": "Resume processed successfully",
        "resume_id": resume_id,
        "parsing_status": "completed",
        "extracted_data": extracted_data
    }


@router.get("/extracted/{resume_id}")
def get_extracted_resume(
    resume_id: str,
    db: Session = Depends(get_db)
):
    extraction = (
        db.query(ResumeExtraction)
        .filter(
            ResumeExtraction.resume_id == resume_id
        )
        .first()
    )

    if extraction is None:
        raise HTTPException(
            status_code=404,
            detail="No extracted data found for this resume"
        )

    return {
        "resume_id": resume_id,
        "extracted_data": extraction.extracted_data
    }
