import re

from app.skill_vocabulary import extract_skills
from app.job_experience_matcher import detect_experience_domains


ACTIVITY_PATTERNS = {
    "Data Collection":
        r"\b(?:collect(?:ing|ed)?\s+data|"
        r"data collection|gather(?:ing|ed)?\s+data)\b",

    "Data Preprocessing":
        r"\b(?:data preprocessing|preprocess\w*\s+data|"
        r"data cleaning|clean(?:ing|ed)?\s+data|"
        r"missing values|encoding categorical features)\b",

    "Data Analysis":
        r"\b(?:data analysis|data analytics|"
        r"analy[sz]\w*\s+data|"
        r"interpret\w*\s+data)\b",

    "Data Visualization":
        r"\b(?:data visualization|visuali[sz]ations?|"
        r"visuali[sz]\w*\s+data|dashboards?)\b",

    "Model Training":
        r"\b(?:model training|"
        r"train\w*\s+(?:\w+\s+){0,4}models?|"
        r"develop\w*\s+(?:a\s+)?machine learning model)\b",

    "Model Evaluation":
        r"\b(?:model evaluation|model performance|"
        r"evaluat\w*\s+(?:\w+\s+){0,4}models?|"
        r"prediction performance)\b",

    "Application Development":
        r"\b(?:application development|"
        r"develop\w*\s+(?:\w+\s+){0,4}applications?|"
        r"software development|"
        r"build\w*\s+(?:\w+\s+){0,4}applications?|"
        r"built\w*\s+(?:\w+\s+){0,4}applications?)\b",

    "User Interface Development":
        r"\b(?:user interfaces?|user-friendly interfaces?|"
        r"input interfaces?|web interfaces?|"
        r"frontend development|UI design)\b",

    "Backend Development":
        r"\b(?:backend development|backend features|"
        r"backend functionality|backend functionalities)\b",

    "API Integration":
        r"\b(?:API integration|"
        r"integrat\w*\s+(?:\w+\s+){0,3}APIs?|"
        r"powered by\s+(?:\w+\s+){0,5}API)\b",

    "Prompt Engineering":
        r"\bprompt engineering\b",

    "Application Deployment":
        r"\b(?:application deployment|"
        r"deploy\w*\s+(?:\w+\s+){0,4}applications?)\b",

    "Software Testing":
        r"\b(?:software testing|unit testing|"
        r"integration testing|test automation|"
        r"test\w*\s+(?:\w+\s+){0,3}software)\b",

    "Debugging":
        r"\bdebugg?\w*\b",

    "Documentation":
        r"\b(?:documentation|"
        r"documenting software|technical documentation)\b",

    "Database Management":
        r"\b(?:database management|"
        r"database design|database administration)\b",

    "Data Modeling":
        r"\bdata model(?:ing|ling)\b",

    "Data Warehousing":
        r"\bdata warehousing\b",

    "Market Research":
        r"\bmarket research\b",

    "User Research":
        r"\buser research\b",

    "Product Strategy":
        r"\bproduct strategy\b",

    "Prototyping":
        r"\b(?:prototyping|prototypes?)\b",

    "Security Monitoring":
        r"\b(?:security monitoring|"
        r"monitor\w*\s+(?:\w+\s+){0,3}security|"
        r"monitor\w*\s+(?:\w+\s+){0,3}vulnerabilities)\b",

    "Vulnerability Assessment":
        r"\b(?:vulnerability assessment|"
        r"security vulnerabilities|"
        r"identify\w*\s+(?:\w+\s+){0,3}vulnerabilities)\b",

    "Access Control":
        r"\baccess control\b",

    "Incident Response":
        r"\bincident response\b",

    "Cloud Infrastructure":
        r"\bcloud infrastructure\b",
}


def join_text(value):
    """Convert text or a list of strings into text."""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(
            item
            for item in value
            if isinstance(item, str)
        )

    return ""


def extract_activities(text):
    """Extract recognized practical activities."""

    if not isinstance(text, str):
        return []

    return [
        activity
        for activity, pattern in ACTIVITY_PATTERNS.items()
        if re.search(pattern, text, re.IGNORECASE)
    ]


def normalize_project_records(projects):
    """Normalize projects while retaining supporting evidence."""

    normalized = []

    for project in projects:

        title = project.get("title") or ""
        category = project.get("category") or ""

        technologies = join_text(
            project.get("technologies", [])
        )

        description = join_text(
            project.get("description", [])
        )

        project_text = " ".join([
            title,
            category,
            technologies,
            description,
        ])

        activity_evidence = {}

        descriptions = project.get("description", [])

        if isinstance(descriptions, str):
            descriptions = [descriptions]

        for sentence in descriptions:

            if not isinstance(sentence, str):
                continue

            for activity in extract_activities(sentence):

                activity_evidence.setdefault(
                    activity, []
                ).append(sentence)

        normalized.append({
            "title": title,
            "category": category,
            "technologies": project.get(
                "technologies", []
            ),
            "skills": extract_skills(project_text),
            "domains": detect_experience_domains(
                project_text
            ),
            "activities": list(activity_evidence),
            "activity_evidence": activity_evidence,
        })

    return normalized


def match_job_projects(profile, job):
    """Compare project activities against job responsibilities."""

    responsibilities = join_text(
        job.get("responsibilities", [])
    )

    required_activities = extract_activities(
        responsibilities
    )

    projects = normalize_project_records(
        profile.get("projects", [])
    )

    job_skill_text = " ".join([
        join_text(job.get("required_skills", [])),
        join_text(job.get("preferred_skills", [])),
        responsibilities,
    ])

    job_skills = set(
        extract_skills(job_skill_text)
    )

    job_domains = set(
        detect_experience_domains(
            job.get("domain") or ""
        )
    )

    result = {
        "status": "unknown",
        "match_ratio": None,
        "total_activities": len(required_activities),
        "matched_count": 0,
        "unmatched_count": None,
        "required_activities": required_activities,
        "matched_activities": [],
        "unmatched_activities": [],
        "project_matches": [],
        "matched_evidence": [],
        "reason": "",
    }

    if not responsibilities.strip():

        result["status"] = "not_specified"

        result["reason"] = (
            "No extracted job responsibilities."
        )

        return result

    if not required_activities:

        result["reason"] = (
            "Responsibilities are present, but no supported "
            "practical activity patterns were recognized."
        )

        return result

    if not projects:

        result["reason"] = (
            "No student project records available."
        )

        return result

    all_matched_activities = set()

    for project in projects:

        matched_activities = sorted(
            set(required_activities).intersection(
                project["activities"]
            )
        )

        matched_skills = sorted(
            job_skills.intersection(
                project["skills"]
            )
        )

        matched_domains = sorted(
            job_domains.intersection(
                project["domains"]
            )
        )

        if not (
            matched_activities
            or matched_skills
            or matched_domains
        ):
            continue

        all_matched_activities.update(
            matched_activities
        )

        result["project_matches"].append({
            "title": project["title"],
            "category": project["category"],
            "matched_activities": matched_activities,
            "matched_skills": matched_skills,
            "matched_domains": matched_domains,
            "activity_match_ratio": (
                len(matched_activities)
                / len(required_activities)
            ),
        })

        for activity in matched_activities:

            result["matched_evidence"].append({
                "activity": activity,
                "project": project["title"],
                "sources": project[
                    "activity_evidence"
                ].get(activity, []),
            })

    matched = [
        activity
        for activity in required_activities
        if activity in all_matched_activities
    ]

    unmatched = [
        activity
        for activity in required_activities
        if activity not in all_matched_activities
    ]

    result["matched_activities"] = matched
    result["unmatched_activities"] = unmatched

    result["matched_count"] = len(matched)
    result["unmatched_count"] = len(unmatched)

    result["match_ratio"] = (
        len(matched) / len(required_activities)
    )

    result["status"] = "evaluated"

    result["project_matches"].sort(
        key=lambda item: (
            -item["activity_match_ratio"],
            -len(item["matched_skills"]),
            item["title"],
        )
    )

    result["reason"] = (
        f"Project descriptions provide evidence for "
        f"{len(matched)} of "
        f"{len(required_activities)} recognized "
        f"job activities."
    )

    return result