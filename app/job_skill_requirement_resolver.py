import re

from app.skill_vocabulary import extract_skills


CERTIFICATION_SKILLS = {
    "CCNA",
    "CompTIA Security+",
    "CompTIA Network+",
}


FUTURE_CERTIFICATION_PATTERN = re.compile(
    r"\b(?:willing(?:ness)?\s+to|"
    r"expected\s+to)\s+"
    r"(?:work\s+towards?|pursue|obtain|earn)"
    r"\s+(?:industry\s+)?certifications?\b",
    re.IGNORECASE,
)


PROGRAMMING_ALTERNATIVE_PATTERN = re.compile(
    r"\b(?:at\s+least\s+one|one\s+or\s+more)"
    r"\s+(?:programming|programing)"
    r"\s+or\s+scripting\s+languages?\b",
    re.IGNORECASE,
)


def split_qualification_clauses(qualifications):
    """Separate explicit qualification statements conservatively."""

    clauses = []

    for text in qualifications:

        if not isinstance(text, str):
            continue

        parts = re.split(
            r"(?<=[.!?])\s+|;\s*|\n+",
            text
        )

        clauses.extend(
            part.strip()
            for part in parts
            if part.strip()
        )

    return clauses


def resolve_skill_requirements(job):
    """Resolve narrowly defined contextual skill requirements."""

    required = list(job.get("required_skills") or [])
    preferred = list(job.get("preferred_skills") or [])

    qualifications = [
        text
        for text in (job.get("qualifications") or [])
        if isinstance(text, str)
    ]

    qualifications = split_qualification_clauses(
        qualifications
    )

    adjustments = []
    alternative_groups = []

    # Certifications mentioned exclusively as future
    # learning goals are not existing qualifications.

    for certification in CERTIFICATION_SKILLS:

        mentions = [
            text for text in qualifications
            if certification in extract_skills(text)
        ]

        if not mentions:
            continue

        future_only = all(
            FUTURE_CERTIFICATION_PATTERN.match(
                text.strip(" -*")
            )
            for text in mentions
        )

        if not future_only:
            continue

        # Preserve ambiguous mixed statements.
        mandatory_language = re.compile(
            r"\b(?:must|required|mandatory|"
            r"prerequisite|currently hold|"
            r"current certification)\b",
            re.IGNORECASE,
        )

        ambiguous_mentions = []

        for text in mentions:

            # Separate unrelated citizenship requirements
            # found after merged certification lists.
            certification_text = re.split(
                r"\b(?:U\.?S\.?|United States)"
                r"\s+citizenship\b",
                text,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]

            if mandatory_language.search(
                certification_text
            ):
                ambiguous_mentions.append(text)

        if ambiguous_mentions:
            continue

        # Avoid removing certifications independently
        # mentioned in other structured requirements.

        other_texts = []

        for field in [
            "education_requirements",
            "experience_requirements",
            "responsibilities",
        ]:

            value = job.get(field)

            if isinstance(value, str):
                other_texts.append(value)

            elif isinstance(value, list):
                other_texts.extend(
                    item for item in value
                    if isinstance(item, str)
                )

        if any(
            certification in extract_skills(text)
            for text in other_texts
        ):
            continue

        for category, skills in [
            ("required", required),
            ("preferred", preferred),
        ]:

            if certification in skills:

                skills.remove(certification)

                adjustments.append({
                    "type": "future_certification",
                    "skill": certification,
                    "original_category": category,
                    "source_text": mentions,
                    "reason": (
                        "Certification is described as "
                        "a future learning goal."
                    ),
                })

    # Collect additional structured requirement evidence.

    additional_requirement_texts = []

    for field in [
        "education_requirements",
        "experience_requirements",
        "responsibilities",
    ]:

        value = job.get(field)

        if isinstance(value, str):
            additional_requirement_texts.append(value)

        elif isinstance(value, list):
            additional_requirement_texts.extend(
                item for item in value
                if isinstance(item, str)
            )

    additional_requirement_texts = (
        split_qualification_clauses(
            additional_requirement_texts
        )
    )

    optional_language = re.compile(
        r"\b(?:preferred|optional|desirable|"
        r"ideally|not\s+required|nice\s+to\s+have|"
        r"not\s+mandatory|not\s+necessary)\b",
        re.IGNORECASE,
    )

    mandatory_language = re.compile(
        r"\b(?:must|required|mandatory|"
        r"minimum\s+requirement)\b",
        re.IGNORECASE,
    )

    # Preserve explicitly stated programming alternatives.

    for text in qualifications:

        match = PROGRAMMING_ALTERNATIVE_PATTERN.search(
            text
        )

        if not match:
            continue

        # Do not promote optional or ambiguous statements.
        if optional_language.search(text):
            continue

        if not mandatory_language.search(text):
            continue

        # Only resolve the category when Scripting
        # is already an extracted required skill.

        if "Scripting" not in required:
            continue

        # Preserve independent scripting requirements.

        independent_scripting = any(
            bool(
                {"Programming", "Scripting"}.intersection(
                    extract_skills(
                        PROGRAMMING_ALTERNATIVE_PATTERN.sub(
                            "", other
                        )
                    )
                )
            )
            for other in (
                qualifications
                + additional_requirement_texts
            )
        )

        if independent_scripting:
            continue

        if "Programming" not in required:
            required.append("Programming")

        alternative_groups.append({
            "type": "any_of",
            "skills": ["Programming", "Scripting"],
            "source_text": text,
            "matched_text": match.group(),
        })

        adjustments.append({
            "type": "programming_alternative",
            "skills": ["Programming", "Scripting"],
            "source_text": text,
            "reason": (
                "The posting explicitly accepts "
                "programming or scripting."
            ),
        })

        break

    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "required_alternative_groups":
            alternative_groups,
        "adjustments": adjustments,
    }
