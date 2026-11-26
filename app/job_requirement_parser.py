import re

from app.skill_vocabulary import extract_skills


# Explicit alternative skill patterns
ALTERNATIVE_PATTERNS = [
    (
        r"\b(?:linux\s+or\s+windows|"
        r"windows\s+or\s+linux)\b"
    ),
    (
        r"\b(?:python\s+or\s+c\+\+|"
        r"c\+\+\s+or\s+python)(?!\w)"
    ),
    (
        r"\b(?:power\s*bi\s+or\s+tableau|"
        r"tableau\s+or\s+power\s*bi)\b"
    ),
    (
        r"\b(?:sketch,\s*)?"
        r"adobe\s+xd,?\s+or\s+figma\b"
    ),
    (
        r"\baws,\s*azure,?\s+or\s+gcp\b"
    ),
    (
        r"\bat\s+least\s+one"
        r"(?:\s+or\s+more)?"
        r"\s+of\s+the\s+following\s*:\s*"
        r"java,\s*c\+\+,\s*javascript,\s*python\b"
    ),
]


def detect_alternative_groups(qualifications):
    """Detect explicitly supported alternative skill groups."""

    groups = []
    seen = set()

    if not isinstance(qualifications, list):
        return groups

    for qualification in qualifications:

        if not isinstance(qualification, str):
            continue

        for pattern in ALTERNATIVE_PATTERNS:

            matches = re.finditer(
                pattern,
                qualification,
                re.IGNORECASE
            )

            for match in matches:

                skills = extract_skills(
                    match.group()
                )

                skills = list(dict.fromkeys(skills))

                if len(skills) < 2:
                    continue

                key = frozenset(
                    skill.casefold()
                    for skill in skills
                )

                if key in seen:
                    continue

                seen.add(key)

                groups.append({
                    "type": "any_of",
                    "skills": skills,
                    "source_text": qualification,
                    "matched_text": match.group(),
                })

    return groups


def get_applicable_alternative_groups(
    job_skills,
    alternative_groups,
):
    """Keep groups fully represented in a skill category."""

    available_skills = {
        skill.casefold()
        for skill in job_skills
        if isinstance(skill, str)
    }

    applicable = []

    for group in alternative_groups:

        group_skills = {
            skill.casefold()
            for skill in group["skills"]
        }

        if group_skills.issubset(available_skills):
            applicable.append(group)

    return applicable


def parse_job_skill_requirements(job):
    """Identify required and preferred alternative groups."""

    if not isinstance(job, dict):
        raise ValueError(
            "Job posting must be a dictionary."
        )

    qualifications = job.get("qualifications", [])

    alternative_groups = detect_alternative_groups(
        qualifications
    )

    required_groups = (
        get_applicable_alternative_groups(
            job.get("required_skills", []),
            alternative_groups
        )
    )

    preferred_groups = (
        get_applicable_alternative_groups(
            job.get("preferred_skills", []),
            alternative_groups
        )
    )

    return {
        "job_id": job.get("job_id"),
        "job_title": job.get("job_title"),
        "required_alternative_groups": required_groups,
        "preferred_alternative_groups": preferred_groups,
    }