from app.student_profile_builder import normalize_skill
from app.job_requirement_parser import (
    parse_job_skill_requirements,
)


def normalize_skill_list(skills):
    """Normalize and deduplicate a collection of skills."""

    normalized = {}

    if not isinstance(skills, list):
        return normalized

    for skill in skills:

        if not isinstance(skill, str):
            continue

        for value in normalize_skill(skill):

            key = value.casefold()

            if key not in normalized:
                normalized[key] = value

    return normalized


def build_evidence_lookup(profile):
    """Create a lookup for supporting resume evidence."""

    lookup = {}

    for record in profile.get("skill_evidence", []):

        skill = record.get("skill")

        if not isinstance(skill, str):
            continue

        lookup[skill.casefold()] = record.get(
            "sources", []
        )

    return lookup


def compare_skills(
    student_skills,
    job_skills,
    evidence_lookup=None,
    alternative_groups=None,
):
    """Compare individual and alternative skill requirements."""

    if evidence_lookup is None:
        evidence_lookup = {}

    if alternative_groups is None:
        alternative_groups = []

    student_lookup = normalize_skill_list(
        student_skills
    )

    job_lookup = normalize_skill_list(
        job_skills
    )

    matched_skills = []
    missing_skills = []
    matched_evidence = []

    requirement_results = []
    alternative_results = []

    grouped_keys = set()

    # Evaluate alternative skill groups first.

    for group in alternative_groups:

        group_lookup = normalize_skill_list(
            group.get("skills", [])
        )

        group_keys = set(group_lookup)

        if len(group_keys) < 2:
            continue

        if not group_keys.issubset(job_lookup):
            continue

        # Avoid counting overlapping groups twice.

        if group_keys.intersection(grouped_keys):
            continue

        grouped_keys.update(group_keys)

        matched_options = [
            skill
            for key, skill in group_lookup.items()
            if key in student_lookup
        ]

        satisfied = bool(matched_options)

        group_label = " OR ".join(
            group_lookup.values()
        )

        group_result = {
            "type": "any_of",
            "requirement": group_label,
            "skills": list(group_lookup.values()),
            "matched_options": matched_options,
            "satisfied": satisfied,
            "source_text": group.get("source_text"),
        }

        alternative_results.append(group_result)
        requirement_results.append(group_result)

        if satisfied:

            for skill in matched_options:

                matched_skills.append(skill)

                matched_evidence.append({
                    "skill": skill,
                    "sources": evidence_lookup.get(
                        skill.casefold(), []
                    ),
                })

        else:

            missing_skills.append(group_label)

    # Evaluate remaining individual skills.

    for key, skill in job_lookup.items():

        if key in grouped_keys:
            continue

        satisfied = key in student_lookup

        requirement_results.append({
            "type": "individual",
            "requirement": skill,
            "skills": [skill],
            "matched_options": (
                [skill] if satisfied else []
            ),
            "satisfied": satisfied,
        })

        if satisfied:

            matched_skills.append(skill)

            matched_evidence.append({
                "skill": skill,
                "sources": evidence_lookup.get(
                    key, []
                ),
            })

        else:

            missing_skills.append(skill)

    total_requirements = len(requirement_results)

    matched_count = sum(
        1
        for result in requirement_results
        if result["satisfied"]
    )

    missing_count = (
        total_requirements - matched_count
    )

    match_ratio = (
        matched_count / total_requirements
        if total_requirements > 0
        else None
    )

    return {
        "status": (
            "evaluated"
            if total_requirements > 0
            else "not_specified"
        ),

        "total_skills": len(job_lookup),

        "total_requirements": total_requirements,

        "matched_count": matched_count,

        "missing_count": missing_count,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "matched_evidence": matched_evidence,

        "alternative_groups": alternative_results,

        "requirement_results": requirement_results,

        "match_ratio": match_ratio,
    }


def match_job_skills(profile, job):
    """Evaluate required and preferred internship skills."""

    if not isinstance(profile, dict):
        raise ValueError(
            "Student profile must be a dictionary."
        )

    if not isinstance(job, dict):
        raise ValueError(
            "Job posting must be a dictionary."
        )

    student_skills = profile.get("skills", [])

    evidence_lookup = build_evidence_lookup(
        profile
    )

    requirements = parse_job_skill_requirements(
        job
    )

    required_match = compare_skills(
        student_skills=student_skills,
        job_skills=job.get("required_skills", []),
        evidence_lookup=evidence_lookup,
        alternative_groups=requirements[
            "required_alternative_groups"
        ],
    )

    preferred_match = compare_skills(
        student_skills=student_skills,
        job_skills=job.get("preferred_skills", []),
        evidence_lookup=evidence_lookup,
        alternative_groups=requirements[
            "preferred_alternative_groups"
        ],
    )

    return {
        "job_id": job.get("job_id"),

        "job_title": job.get("job_title"),

        "required_skills": required_match,

        "preferred_skills": preferred_match,
    }