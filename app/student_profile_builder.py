from sqlalchemy.orm import Session

from app.models import Candidate, Resume, ResumeExtraction

from app.structured_extractor import (
    extract_skill_records,
    extract_project_records,
    extract_experience_records,
    extract_education_records,
    extract_award_records,
)

from app.skill_vocabulary import extract_skills


def get_section(extracted_data, section):
    """Safely retrieve a resume section as a list of strings."""

    if not isinstance(extracted_data, dict):
        return []

    values = extracted_data.get(section, [])

    if not isinstance(values, list):
        return []

    return [
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    ]


def normalize_skill(skill):
    """Standardize recognized skills and preserve compound entries."""

    skill = skill.strip()

    if not skill:
        return []

    normalized = extract_skills(skill)

    if not normalized:
        return [skill]

    # Preserve compound entries containing additional tool information
    if "(" in skill and ")" in skill:
        if skill.casefold() not in {
            item.casefold() for item in normalized
        }:
            normalized.append(skill)

    return list(dict.fromkeys(normalized))


def build_skill_evidence(
    skill_records,
    project_records,
    experience_records,
    certification_lines,
):
    """Collect skills and record their supporting resume evidence."""

    evidence = {}

    def add_skill(skill, source, detail):
        key = skill.casefold()

        if key not in evidence:
            evidence[key] = {
                "skill": skill,
                "sources": [],
            }

        source_record = {
            "source": source,
            "detail": detail,
        }

        if source_record not in evidence[key]["sources"]:
            evidence[key]["sources"].append(source_record)

    # 1. Explicitly listed resume skills
    for record in skill_records:
        category = record.get("category", "General")

        for skill in record.get("skills", []):
            for normalized in normalize_skill(skill):
                add_skill(
                    normalized,
                    "explicit_skill",
                    category,
                )

    # 2. Skills identified from projects
    for project in project_records:
        title = project.get("title") or "Untitled project"

        technologies = project.get("technologies") or []

        if isinstance(technologies, str):
            technologies = [technologies]

        for technology in technologies:
            for normalized in normalize_skill(technology):
                add_skill(
                    normalized,
                    "project_technology",
                    title,
                )

        description = project.get("description") or []

        if isinstance(description, str):
            description = [description]

        project_text = " ".join(
            [title] + description
        )

        for skill in extract_skills(project_text):
            add_skill(
                skill,
                "project_description",
                title,
            )

    # 3. Skills identified from experience
    for experience in experience_records:
        company = experience.get("company") or ""
        role = experience.get("role") or ""

        responsibilities = (
            experience.get("responsibilities") or []
        )

        if isinstance(responsibilities, str):
            responsibilities = [responsibilities]

        experience_text = " ".join(
            [role] + responsibilities
        )

        detail = " - ".join(
            value for value in [company, role] if value
        )

        for skill in extract_skills(experience_text):
            add_skill(
                skill,
                "experience",
                detail or "Resume experience",
            )

    # 4. Skills mentioned in certifications
    for certification in certification_lines:
        for skill in extract_skills(certification):
            add_skill(
                skill,
                "certification",
                certification,
            )

    return sorted(
        evidence.values(),
        key=lambda item: item["skill"].casefold(),
    )


def build_student_profile(
    extracted_data,
    candidate_id=None,
    resume_id=None,
    professional_summary=None,
    location=None,
):
    """Build a standardized profile from extracted resume data."""

    if not isinstance(extracted_data, dict):
        raise ValueError(
            "Extracted resume data must be a dictionary."
        )

    skill_lines = get_section(
        extracted_data, "skills"
    )

    project_lines = get_section(
        extracted_data, "projects"
    )

    experience_lines = get_section(
        extracted_data, "experience"
    )

    education_lines = get_section(
        extracted_data, "education"
    )

    certification_lines = get_section(
        extracted_data, "certifications"
    )

    award_lines = get_section(
        extracted_data, "awards"
    )

    language_lines = get_section(
        extracted_data, "languages"
    )

    skill_records = extract_skill_records(skill_lines)

    project_records = extract_project_records(
        project_lines
    )

    experience_records = extract_experience_records(
        experience_lines
    )

    education_records = extract_education_records(
        education_lines
    )

    award_records = extract_award_records(
        award_lines
    )

    skill_evidence = build_skill_evidence(
        skill_records,
        project_records,
        experience_records,
        certification_lines,
    )

    normalized_skills = [
        item["skill"]
        for item in skill_evidence
    ]

    explicit_skills = [
        item["skill"]
        for item in skill_evidence
        if any(
            source["source"] == "explicit_skill"
            for source in item["sources"]
        )
    ]

    inferred_skills = [
        item["skill"]
        for item in skill_evidence
        if item["skill"] not in explicit_skills
    ]

    return {
        "candidate_id": candidate_id,
        "resume_id": resume_id,
        "professional_summary": professional_summary,
        "location": location,

        "skills": normalized_skills,
        "explicit_skills": explicit_skills,
        "inferred_skills": inferred_skills,
        "skill_records": skill_records,
        "skill_evidence": skill_evidence,

        "education": education_records,
        "experience": experience_records,
        "projects": project_records,

        "certifications": certification_lines,
        "awards": award_records,
        "languages": language_lines,

        "profile_statistics": {
            "total_skills": len(normalized_skills),
            "explicit_skills": len(explicit_skills),
            "inferred_skills": len(inferred_skills),
            "education_records": len(education_records),
            "experience_records": len(experience_records),
            "projects": len(project_records),
            "certifications": len(certification_lines),
            "awards": len(award_records),
        },
    }


def load_student_profile(
    db: Session,
    candidate_id: str,
    resume_id: str,
):
    """Load a student's processed resume from the database."""

    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise ValueError("Student not found.")

    resume = db.get(Resume, resume_id)

    if resume is None:
        raise ValueError("Resume not found.")

    if resume.candidate_id != candidate_id:
        raise ValueError(
            "The resume does not belong to this student."
        )

    if resume.parsing_status != "completed":
        raise ValueError(
            "The resume must be processed before matching."
        )

    extraction = (
        db.query(ResumeExtraction)
        .filter(
            ResumeExtraction.resume_id == resume_id
        )
        .first()
    )

    if extraction is None:
        raise ValueError(
            "No extracted resume data found."
        )

    return build_student_profile(
        extracted_data=extraction.extracted_data,
        candidate_id=candidate_id,
        resume_id=resume_id,
        professional_summary=candidate.professional_summary,
        location=candidate.location,
    )