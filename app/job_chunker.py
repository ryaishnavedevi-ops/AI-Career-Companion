
import json
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR / "data" / "internships.json"
CHUNKS_PATH = BASE_DIR / "data" / "job_chunks.json"

MAX_CHUNK_WORDS = 250
CHUNK_OVERLAP_WORDS = 30


def load_jobs():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def clean_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def format_list(items):
    return "\n".join(
        f"- {clean_text(item)}"
        for item in items
        if clean_text(item)
    )


def split_long_text(text):
    words = text.split()

    if not words:
        return []

    if len(words) <= MAX_CHUNK_WORDS:
        return [text]

    parts = []
    start = 0

    while start < len(words):
        end = min(start + MAX_CHUNK_WORDS, len(words))

        parts.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - CHUNK_OVERLAP_WORDS

    return parts


def create_section_chunks(job, section, content):
    if not content or not content.strip():
        return []

    chunks = []

    context = (
        f"Job Title: {job['job_title']}\n"
        f"Company: {job['company']}\n"
        f"Domain: {job['domain']}\n"
        f"Location: {job['location']}\n"
        f"Section: {section}\n"
    )

    parts = split_long_text(content)

    for index, part in enumerate(parts, start=1):
        chunk = {
            "chunk_id": f"{job['job_id']}_{section}_{index}",
            "job_id": job["job_id"],
            "job_title": job["job_title"],
            "company": job["company"],
            "location": job["location"],
            "domain": job["domain"],
            "section": section,
            "chunk_number": index,
            "text": context + "\n" + part
        }

        chunks.append(chunk)

    return chunks


def chunk_job(job):
    chunks = []

    # 1. Job overview
    overview = (
        f"Employment Type: {job['employment_type']}\n"
        f"Work Mode: {job['work_mode']}\n"
        f"Description: {clean_text(job['job_description'])}"
    )

    chunks.extend(
        create_section_chunks(job, "overview", overview)
    )

    # 2. Responsibilities
    responsibilities = format_list(
        job.get("responsibilities", [])
    )

    chunks.extend(
        create_section_chunks(
            job, "responsibilities", responsibilities
        )
    )

    # 3. Required and preferred skills
    skill_sections = []

    if job.get("required_skills"):
        skill_sections.append(
            "Required Skills: "
            + ", ".join(job["required_skills"])
        )

    if job.get("preferred_skills"):
        skill_sections.append(
            "Preferred Skills: "
            + ", ".join(job["preferred_skills"])
        )

    chunks.extend(
        create_section_chunks(
            job, "skills", "\n".join(skill_sections)
        )
    )

    # 4. Qualifications and eligibility
    qualification_sections = []

    if job.get("qualifications"):
        qualification_sections.append(
            "Qualifications:\n"
            + format_list(job["qualifications"])
        )

    if job.get("education_requirements"):
        qualification_sections.append(
            "Education Requirements: "
            + clean_text(job["education_requirements"])
        )

    if job.get("experience_requirements"):
        qualification_sections.append(
            "Experience Requirements: "
            + clean_text(job["experience_requirements"])
        )

    chunks.extend(
        create_section_chunks(
            job,
            "qualifications",
            "\n".join(qualification_sections)
        )
    )

    return chunks


def generate_chunks():
    jobs = load_jobs()
    all_chunks = []

    for job in jobs:
        all_chunks.extend(chunk_job(job))

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as file:
        json.dump(
            all_chunks,
            file,
            indent=4,
            ensure_ascii=False
        )

    section_counts = Counter(
        chunk["section"] for chunk in all_chunks
    )

    unique_jobs = {
        chunk["job_id"] for chunk in all_chunks
    }

    unique_chunks = {
        chunk["chunk_id"] for chunk in all_chunks
    }

    print("\n--- Job Chunking Report ---")
    print(f"Total job postings: {len(jobs)}")
    print(f"Total chunks generated: {len(all_chunks)}")
    print(f"Unique jobs represented: {len(unique_jobs)}")
    print(f"Unique chunk IDs: {len(unique_chunks)}")
    print(
        f"Average chunks per job: "
        f"{len(all_chunks) / len(jobs):.2f}"
        if jobs else "Average chunks per job: 0"
    )

    print("\n--- Chunk Distribution ---")

    for section, count in section_counts.items():
        print(f"{section}: {count}")

    print(f"\nOutput file: {CHUNKS_PATH}")

    return all_chunks


if __name__ == "__main__":
    generate_chunks()
