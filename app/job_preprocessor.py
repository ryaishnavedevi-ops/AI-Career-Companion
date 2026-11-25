
import csv
import re
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATASET_PATH = BASE_DIR / "data" / "raw" / "postings.csv"

ALLOWED_EXPERIENCE_LEVELS = {
    "Internship",
    "Entry level",
    ""
}

EXCLUDED_JOB_IDS = {
    
    "3891070452": "Training and placement program rather than a specific internship",
    "3895814058": "Insufficient responsibilities and qualification information",
    "3901345525": "Course review program with limited technical relevance",
    "3901946176": "Insufficient detailed job information",
    "3891250319": "Duplicate Year Up training and placement program",

    
    "3889710922": "Research study participation",
    "3901956625": "Senior-level engineering role",
    "3903835209": "Marketing-focused internship",
    "3904924071": "Workforce development and grant activities",
    "3904599802": "Regular entry-level engineering position, not an internship",
    "3905829047": "Redundant network engineering posting with equivalent requirements",
    "3887596418": "Redundant Audio AI opening with inconsistent title year",
    "3903818851": "Administrative data entry and vendor cleanup role",
    "3903836754": "Duplicate administrative data entry posting",
    "3884820711": "Self-paced training and skill development program",
    "3885110498": "Banking operations, customer service and sales-focused role",
    "3887934099": "Administrative security operations role",
    "3894563041": "Missing job responsibilities and qualifications",
    "3895200369": "Venture capital and financial valuation role",
    "3901154660": "Study and training-based internship program",
    "3901695820": "Insufficient technical responsibilities and requirements",
    "3901984082": "Customer pricing and purchase order operations",
    "3902353887": "General business operations and strategy role",
    "3902757439": "Product marketing and promotional materials",
    "3904720278": "Administrative project coordination role"
}

INTERNSHIP_TITLE_PATTERN = re.compile(
    r"\b(intern|internship|interns)\b",
    re.IGNORECASE
)

TECH_PATTERN = re.compile(
    r"\b("
    r"software|developer|data science|data analyst|"
    r"data engineer|machine learning|artificial intelligence|"
    r"frontend|front end|backend|back end|"
    r"full stack|full-stack|cybersecurity|cyber security|"
    r"devops|cloud|computer science|information technology|"
    r"web development|mobile app|ui/ux|ux design|ui design|"
    r"software testing|analytics|programming|data analytics|"
    r"AI|ML|NLP|IT|QA|robotics|automation|database|"
    r"business intelligence|information security|"
    r"network engineer|systems engineer|technical support|"
    r"computer vision|deep learning|web design|"
    r"digital technology|informatics|data analysis|"
    r"data scientist|application development|"
    r"SDE|SWE|SOC analyst|digital forensics|DFIR|"
    r"network engineering|user experience|"
    r"computational imaging|systems administrator|"
    r"data quality|geographic information systems|GIS|"
    r"FedRAMP|quantum benchmarking|quality assurance|"
    r"UX games|PC technician|data intern|"
    r"mobile product design|seasonal technology|"
    r"business analyst|product management|product manager|"
    r"hardware engineering|hardware engineer|test engineer"
    r")\b",
    re.IGNORECASE
)



def load_internship_candidates():
    candidates = []
    stats = Counter()

    seen_ids = set()
    seen_postings = set()
    seen_descriptions = set()

    with open(
        RAW_DATASET_PATH,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            stats["total_records"] += 1

            is_standard_internship = (
                row["formatted_work_type"] == "Internship"
            )

            is_additional_internship = (
                row["formatted_work_type"] != "Internship"
                and row["formatted_experience_level"] == "Internship"
                and INTERNSHIP_TITLE_PATTERN.search(row["title"])
                and TECH_PATTERN.search(row["title"])
            )

            if not (
                is_standard_internship
                or is_additional_internship
            ):
                continue

            if is_standard_internship:
                stats["internship_records"] += 1
            else:
                stats["additional_internships"] += 1

            if (
                row["formatted_experience_level"]
                not in ALLOWED_EXPERIENCE_LEVELS
            ):
                continue

            stats["eligible_experience"] += 1

            title = row["title"].strip()

            if not TECH_PATTERN.search(title):
                continue

            stats["technology_candidates"] += 1

            required_fields = [
                "job_id",
                "title",
                "company_name",
                "location",
                "description",
                "job_posting_url"
            ]

            if any(
                not row.get(field, "").strip()
                for field in required_fields
            ):
                stats["incomplete_records"] += 1
                continue

            if len(row["description"].strip()) < 100:
                stats["short_descriptions"] += 1
                continue
            
            if (
                row["company_name"].strip().casefold() == "data glacier"
                and "will not utilize this work for their benefit"
                in " ".join(row["description"].casefold().split())
            ):
                stats["excluded_records"] += 1
                continue
            job_id = row["job_id"].strip()

            if job_id in EXCLUDED_JOB_IDS:
                stats["excluded_records"] += 1
                continue

            posting_key = (
                row["title"].strip().casefold(),
                row["company_name"].strip().casefold(),
                row["location"].strip().casefold(),
                " ".join(
                    row["description"].casefold().split()
                )
            )

            if job_id in seen_ids:
                stats["duplicate_ids"] += 1
                continue

            if posting_key in seen_postings:
                stats["duplicate_postings"] += 1
                continue

            description_key = (
                row["company_name"].strip().casefold(),
                row["location"].strip().casefold(),
                " ".join(
                    row["description"].casefold().split()
                )
            )

            if description_key in seen_descriptions:
                stats["duplicate_descriptions"] += 1
                continue

            seen_ids.add(job_id)
            seen_postings.add(posting_key)
            seen_descriptions.add(description_key)

            candidates.append(row)

    return candidates, stats


def main():
    candidates, stats = load_internship_candidates()

    print("\n--- Dataset Preprocessing Report ---")

    print(f"Total raw records: {stats['total_records']}")
    print(f"Internship records: {stats['internship_records']}")
    print(f"Additional internship records: {stats['additional_internships']}")
    print(f"Eligible experience levels: {stats['eligible_experience']}")
    print(f"Technology candidates: {stats['technology_candidates']}")
    print(f"Incomplete records: {stats['incomplete_records']}")
    print(f"Short descriptions: {stats['short_descriptions']}")
    print(f"Duplicate IDs: {stats['duplicate_ids']}")
    print(f"Duplicate postings: {stats['duplicate_postings']}")
    print(f"Duplicate descriptions: {stats['duplicate_descriptions']}")
    print(f"Excluded records: {stats['excluded_records']}")
    print(f"Remaining candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
