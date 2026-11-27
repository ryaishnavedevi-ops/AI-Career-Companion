import re
from copy import deepcopy

from app.job_query_builder import SOFT_SKILLS


PROGRAMMING_LANGUAGES = {
    "python",
    "java",
    "javascript",
    "c",
    "c++",
    "c#",
    "go",
    "rust",
    "kotlin",
    "swift",
    "typescript",
    "ruby",
    "php",
    "matlab",
    "r",
}


def enrich_student_profile(profile):
    """Add conservative, traceable skill implications."""

    enriched = deepcopy(profile)

    skills = enriched.setdefault("skills", [])

    evidence = enriched.setdefault(
        "skill_evidence", []
    )

    inferred_skills = enriched.setdefault(
        "inferred_skills", []
    )

    skill_lookup = {
        skill.casefold(): skill
        for skill in skills
    }

    def add_inferred_skill(skill, sources):

        if skill.casefold() in skill_lookup:
            return

        skills.append(skill)

        inferred_skills.append(skill)

        skill_lookup[skill.casefold()] = skill

        evidence.append({
            "skill": skill,
            "sources": sources
        })

    programming_evidence = [
        {
            "source": "skill_implication",
            "detail": skill
        }
        for key, skill in skill_lookup.items()
        if key in PROGRAMMING_LANGUAGES
    ]

    if programming_evidence:

        add_inferred_skill(
            "Programming",
            programming_evidence
        )

    if {
        "html",
        "css",
        "javascript"
    }.issubset(skill_lookup):

        add_inferred_skill(
            "Frontend Development",
            [
                {
                    "source": "skill_implication",
                    "detail": "HTML, CSS and JavaScript"
                }
            ]
        )

    for project in enriched.get("projects", []):

        descriptions = project.get(
            "description", []
        )

        if isinstance(descriptions, str):
            descriptions = [descriptions]

        for description in descriptions:

            if not isinstance(description, str):
                continue

            if re.search(
                r"\b(?:developed|built|implemented)"
                r"\s+(?:\w+\s+){0,6}"
                r"(?:application|software|web app)\b",
                description,
                re.IGNORECASE
            ):

                add_inferred_skill(
                    "Software Development",
                    [
                        {
                            "source": "project_description",
                            "detail": (
                                f"{project.get('title', '')}: "
                                f"{description}"
                            )
                        }
                    ]
                )

    statistics = enriched.get(
        "profile_statistics"
    )

    if isinstance(statistics, dict):

        statistics["total_skills"] = len(skills)

        statistics["inferred_skills"] = len(
            inferred_skills
        )

    return enriched


def assess_technical_requirements(job):
    """Assess available technical requirement information."""

    soft_skills = {
        skill.casefold()
        for skill in SOFT_SKILLS
    }

    required = job.get(
        "required_skills", []
    ) or []

    preferred = job.get(
        "preferred_skills", []
    ) or []

    technical_required = [
        skill for skill in required
        if skill.casefold() not in soft_skills
    ]

    technical_preferred = [
        skill for skill in preferred
        if skill.casefold() not in soft_skills
    ]

    if technical_required:

        status = "technical_required_available"

        factor = 1.0

        reason = (
            "Extracted mandatory technical skills "
            "are available for comparison."
        )

    elif technical_preferred:

        status = "technical_preferred_only"

        factor = 0.75

        reason = (
            "Technical skills are available only "
            "as preferred requirements."
        )

    else:

        status = "insufficient_technical_requirements"

        factor = 0.50

        reason = (
            "No extracted technical required or "
            "preferred skills are available."
        )

    return {
        "status": status,
        "technical_required_skills":
            technical_required,
        "technical_preferred_skills":
            technical_preferred,
        "technical_required_count":
            len(technical_required),
        "technical_preferred_count":
            len(technical_preferred),
        "ranking_factor": factor,
        "reason": reason,
    }



def assess_technical_alignment(comparison):
    """Assess technical alignment using resolved matching evidence."""

    soft_skills = {
        skill.casefold()
        for skill in SOFT_SKILLS
    }

    components = comparison["components"]

    def summarize(component):

        technical_skills = []
        matched_skills = []
        missing_requirements = []

        total = 0
        matched = 0

        for requirement in component.get(
            "requirement_results", []
        ):

            options = requirement.get("skills", [])

            if not options:
                continue

            # Mixed soft/technical alternatives do not
            # establish a mandatory technical requirement.
            if any(
                skill.casefold() in soft_skills
                for skill in options
            ):
                continue

            total += 1

            technical_skills.extend(options)

            matched_options = [
                skill
                for skill in requirement.get(
                    "matched_options", []
                )
                if skill.casefold() not in soft_skills
            ]

            if (
                requirement.get("satisfied") is True
                and matched_options
            ):

                matched += 1
                matched_skills.extend(matched_options)

            else:

                missing_requirements.append(
                    requirement.get("requirement")
                    or " OR ".join(options)
                )

        return {
            "skills": list(dict.fromkeys(technical_skills)),
            "matched_skills": list(dict.fromkeys(matched_skills)),
            "missing_requirements": missing_requirements,
            "total_requirements": total,
            "matched_requirements": matched,
            "match_ratio": (
                matched / total if total else None
            ),
        }

    required = summarize(
        components["required_skills"]
    )

    preferred = summarize(
        components["preferred_skills"]
    )

    # Preserve existing assessment status names.
    assessment = assess_technical_requirements({
        "required_skills": required["skills"],
        "preferred_skills": preferred["skills"],
    })

    if required["total_requirements"]:

        if required["matched_requirements"]:

            alignment_status = (
                "required_technical_evidence_available"
            )

            factor = 1.0

            reason = (
                "At least one required technical "
                "requirement is supported by student evidence."
            )

        else:

            alignment_status = (
                "no_required_technical_match"
            )

            factor = 0.50

            reason = (
                "Technical requirements are available, "
                "but none are supported by recorded "
                "student skill evidence."
            )

    elif preferred["total_requirements"]:

        if preferred["matched_requirements"]:

            alignment_status = (
                "preferred_technical_evidence_available"
            )

            factor = 0.75

            reason = (
                "Technical alignment is supported "
                "by preferred skill evidence only."
            )

        else:

            alignment_status = (
                "no_preferred_technical_match"
            )

            factor = 0.50

            reason = (
                "Preferred technical requirements exist, "
                "but no matching skill evidence is available."
            )

    else:

        alignment_status = (
            "technical_requirements_unavailable"
        )

        factor = 0.50

        reason = (
            "No resolved technical skill requirements "
            "are available. Technical compatibility "
            "cannot be established from skill matching."
        )

    assessment.update({
        "alignment_status": alignment_status,

        "required_technical_alignment": required,

        "preferred_technical_alignment": preferred,

        "ranking_factor": factor,

        "reason": reason,

        "assessment_basis":
            "resolved_skill_requirement_results",
    })

    return assessment


ELIGIBILITY_PATTERNS = {
    "citizenship_requirement": (
        r"\b(?:"
        r"must\s+be\s+(?:a\s+)?"
        r"(?:U\.?S\.?|United States)\s+citizen"
        r"|(?:U\.?S\.?|United States)\s+"
        r"citizenship\s+(?:is\s+)?required"
        r"|requires?\s+(?:U\.?S\.?|United States)"
        r"\s+citizenship"
        r")\b"
    ),

    "security_clearance_mention": (
        r"\bsecurity\s+clearance\b"
    ),

    "work_authorization_mention": (
        r"\b(?:"
        r"work\s+authorization"
        r"|authorized\s+to\s+work"
        r"|visa\s+sponsorship"
        r"|employment\s+sponsorship"
        r")\b"
    ),
}


def detect_additional_eligibility(job):
    """Flag eligibility information for manual review."""

    text_parts = []

    for field in [
        "qualifications",
        "responsibilities",
        "education_requirements",
        "experience_requirements",
        "job_description",
    ]:

        value = job.get(field)

        if isinstance(value, str):

            text_parts.append(value)

        elif isinstance(value, list):

            text_parts.extend(
                item for item in value
                if isinstance(item, str)
            )

    reviews = []

    for name, pattern in ELIGIBILITY_PATTERNS.items():

        evidence = []

        for text in text_parts:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                evidence.append(match.group(0))

        if evidence:

            reviews.append({
                "component": "additional_eligibility",
                "status": "unknown",
                "constraints": [name],
                "evidence": list(
                    dict.fromkeys(evidence)
                ),
                "reason": (
                    "The posting contains eligibility "
                    "information requiring verification."
                )
            })

    return reviews


def refine_job_scoring(scoring, job, comparison=None):
    """Refine ranking without changing base compatibility."""

    refined = deepcopy(scoring)

    technical_assessment = (
        assess_technical_alignment(comparison)
        if comparison is not None
        else assess_technical_requirements(job)
    )

    original_ranking = refined["ranking_score"]

    refined["base_ranking_score"] = (
        original_ranking
    )

    refined["technical_assessment"] = (
        technical_assessment
    )

    refined["ranking_score"] = (
        original_ranking
        * technical_assessment["ranking_factor"]
        if original_ranking is not None
        else None
    )

    additional_reviews = (
        detect_additional_eligibility(job)
    )

    refined["eligibility_review"].extend(
        additional_reviews
    )

    refined["eligibility_review_required"] = bool(
        refined["eligibility_review"]
    )

    return refined