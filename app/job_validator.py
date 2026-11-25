
import json
from pathlib import Path
from collections import Counter

from pydantic import ValidationError
from app.job_schema import JobPosting


DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "internships.json"
)


def validate_dataset(dataset_path=DATASET_PATH):
    with open(dataset_path, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Dataset must contain a JSON array.")

    valid_jobs = []
    errors = []
    seen_ids = set()
    seen_postings = set()

    for index, job in enumerate(jobs, start=1):
        try:
            if not isinstance(job, dict):
                errors.append(f"Record {index}: Invalid record format")
                continue

            validated_job = JobPosting(**job)

            job_id = validated_job.job_id.strip().casefold()

            posting_key = (
                validated_job.job_title.strip().casefold(),
                validated_job.company.strip().casefold(),
                validated_job.location.strip().casefold(),
                validated_job.job_description.strip().casefold(),
            )

            if job_id in seen_ids:
                errors.append(
                    f"Record {index}: Duplicate job ID "
                    f"{validated_job.job_id}"
                )
                continue

            if posting_key in seen_postings:
                errors.append(
                    f"Record {index}: Duplicate job posting"
                )
                continue

            seen_ids.add(job_id)
            seen_postings.add(posting_key)
            valid_jobs.append(validated_job)

        except ValidationError as error:
            errors.append(f"Record {index}: {error}")

    print("\n--- Internship Dataset Validation ---")
    print(f"Total records: {len(jobs)}")
    print(f"Valid records: {len(valid_jobs)}")
    print(f"Invalid or duplicate records: {len(errors)}")

    print("\n--- Domain Distribution ---")
    domains = Counter(job.domain for job in valid_jobs)

    for domain, count in domains.items():
        print(f"{domain}: {count}")

    print("\n--- Source Distribution ---")
    sources = Counter(job.source_type for job in valid_jobs)

    for source, count in sources.items():
        print(f"{source}: {count}")

    if errors:
        print("\n--- Validation Errors ---")
        for error in errors:
            print(error)
    else:
        print("\nNo validation errors found.")

    return valid_jobs, errors


if __name__ == "__main__":
    validate_dataset()
