
import json
from pathlib import Path

from app.job_preprocessor import load_internship_candidates
from app.job_classifier import classify_job_domain
from app.job_extractor import (
    extract_job_sections,
    extract_job_skills,
    extract_education_requirements,
    extract_experience_requirements,
    split_job_statements
)
from app.job_schema import JobPosting


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "internships_draft.json"
OVERRIDES_PATH = BASE_DIR / "data" / "job_overrides.json"


def convert_job(row):
    description = row["description"].strip()

    sections = extract_job_sections(description)
    skills = extract_job_skills(sections)

    education = extract_education_requirements(sections)
    experience = extract_experience_requirements(sections)

    responsibilities = split_job_statements(
        sections["responsibilities"]
    )

    qualifications = split_job_statements(
        sections["required_qualifications"]
        + sections["preferred_qualifications"]
    )

    work_mode = (
        "Remote"
        if row.get("remote_allowed", "").strip() == "1"
        else "Not specified"
    )

    job = JobPosting(
        job_id=row["job_id"].strip(),
        job_title=row["title"].strip(),
        company=row["company_name"].strip(),
        location=row["location"].strip(),
        employment_type="Internship",
        work_mode=work_mode,
        job_description=description,
        responsibilities=list(dict.fromkeys(responsibilities)),
        required_skills=skills["required_skills"],
        preferred_skills=skills["preferred_skills"],
        qualifications=list(dict.fromkeys(qualifications)),
        experience_requirements=" | ".join(experience) if experience else None,
        education_requirements=" | ".join(education) if education else None,
        domain=classify_job_domain(row["title"], description),
        source_type="Real",
        source_url=row["job_posting_url"].strip(),
        collected_date=None
    )

    return job.model_dump()


def generate_dataset():
    candidates, stats = load_internship_candidates()

    with open(OVERRIDES_PATH, "r", encoding="utf-8") as file:
        overrides = json.load(file)

    structured_jobs = []
    applied_overrides = 0

    for row in candidates:
        job = convert_job(row)
        job_id = job["job_id"]

        if job_id in overrides:
            job.update(overrides[job_id])
            applied_overrides += 1

        validated_job = JobPosting(**job)
        structured_jobs.append(validated_job.model_dump())

    if applied_overrides != len(overrides):
        raise ValueError("Some manual overrides were not applied.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            structured_jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n--- Structured Dataset Generation ---")
    print(f"Input candidates: {len(candidates)}")
    print(f"Generated records: {len(structured_jobs)}")
    print(f"Manual overrides applied: {applied_overrides}")
    print(f"Output file: {OUTPUT_PATH}")

    return structured_jobs


if __name__ == "__main__":
    generate_dataset()
