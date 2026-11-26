import re

from app.skill_vocabulary import extract_skills


DOMAIN_PATTERNS = {
    "Frontend Development":
        r"\b(?:front[- ]?end|frontend development)\b",

    "Web Development":
        r"\b(?:web development|web developer|wordpress)\b",

    "Software Development":
        r"\b(?:software development|software engineering|"
        r"software engineer)\b",

    "Artificial Intelligence":
        r"\b(?:artificial intelligence|AI)\b",

    "Machine Learning":
        r"\b(?:machine learning|ML)\b",

    "Data Analysis":
        r"\b(?:data analysis|data analytics|data analyst)\b",

    "Data Science":
        r"\b(?:data science|data scientist)\b",

    "Business Analysis":
        r"\b(?:business analysis|business analyst)\b",

    "Product Management":
        r"\b(?:product management|product manager)\b",

    "Cybersecurity":
        r"\b(?:cybersecurity|information security)\b",

    "Information Technology":
        r"(?i:\binformation technology\b)|\bIT\b",
}


def detect_experience_domains(text):
    """Identify recognized experience domains."""

    return [
        domain
        for domain, pattern in DOMAIN_PATTERNS.items()
        if re.search(pattern, text, re.IGNORECASE)
    ]


def parse_duration_months(duration):
    """Convert an explicitly stated duration into months."""

    if not isinstance(duration, str):
        return None

    duration = duration.strip()

    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(months?|years?)",
        duration,
        re.IGNORECASE
    )

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()

    if unit.startswith("year"):
        value *= 12

    return value


def detect_minimum_experience(text):
    """Detect supported numeric prior experience requirements."""

    pattern = (
        r"\b(\d+(?:\.\d+)?)"
        r"(?:\s*(?:-|–|to)\s*\d+(?:\.\d+)?)?"
        r"\+?\s*(years?|months?)\b"
        r"['’]?\s*(?:of\s+)?"
        r"(?:[\w/-]+\s+){0,5}experience\b"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE
    )

    durations = []

    for match in matches:

        value = float(match.group(1))

        if match.group(2).lower().startswith("year"):
            value *= 12

        durations.append(value)

    return max(durations) if durations else None


def normalize_experience_records(records):
    """Normalize resume experience without inventing durations."""

    normalized = []

    for record in records:

        role = record.get("role") or ""
        company = record.get("company") or ""
        duration = record.get("duration") or ""

        responsibilities = record.get(
            "responsibilities", []
        )

        text = " ".join([
            role,
            *responsibilities
        ])

        normalized.append({
            "role": role,
            "company": company,
            "duration": duration,

            "duration_months":
                parse_duration_months(duration),

            "domains":
                detect_experience_domains(text),

            "skills": extract_skills(text),

            "is_internship": bool(
                re.search(
                    r"\bintern(?:ship)?\b",
                    role,
                    re.IGNORECASE
                )
            ),

            "is_training": bool(
                re.search(
                    r"\btraining\b",
                    text,
                    re.IGNORECASE
                )
            ),
        })

    return normalized


def match_job_experience(profile, job):
    """Evaluate preliminary experience alignment."""

    requirement = job.get("experience_requirements")

    result = {
        "status": "unknown",
        "match_ratio": None,
        "requirement": requirement,
        "minimum_months": None,
        "required_domains": [],
        "required_skills": [],
        "matched_evidence": [],
        "unresolved_constraints": [],
        "preferred": False,
        "reason": "",
    }

    if not isinstance(requirement, str) or not requirement.strip():

        result["status"] = "not_specified"

        result["reason"] = (
            "No extracted experience requirement."
        )

        return result

    constraints = result["unresolved_constraints"]

    # Identify non-experience restrictions.

    if re.search(
        r"\b(?:hours?\s+per\s+week|"
        r"duration\s+is|month\s+contract|"
        r"months?\s+internship)\b",
        requirement,
        re.IGNORECASE
    ):
        constraints.append("internship_commitment")

    if re.search(
        r"\b(?:years?\s+(?:in\s+)?college|"
        r"college\s+experience|"
        r"currently enrolled)\b",
        requirement,
        re.IGNORECASE
    ):
        constraints.append("academic_eligibility")

    if re.search(
        r"\byears?\s+of\s+age\b",
        requirement,
        re.IGNORECASE
    ):
        constraints.append("age_eligibility")

    if re.search(
        r"\bequivalent\b",
        requirement,
        re.IGNORECASE
    ):
        constraints.append("equivalent_experience")

    if "|" in requirement:
        constraints.append("multiple_experience_clauses")

    # Identify optional experience requirements.

    result["preferred"] = bool(
        re.search(
            r"\b(?:preferred|is a plus|"
            r"encouraged|desirable)\b",
            requirement,
            re.IGNORECASE
        )
    )

    if result["preferred"]:
        constraints.append(
            "preferred_experience_requirement"
        )

    # Identify alternatives to professional experience.

    project_allowed = bool(
        re.search(
            r"\b(?:projects?|coursework|courses?)\b",
            requirement,
            re.IGNORECASE
        )
    )

    if project_allowed:
        constraints.append(
            "project_or_coursework_alternative"
        )

    if re.search(
        r"\b(?:experience or interest|"
        r"knowledge or prior experience)\b",
        requirement,
        re.IGNORECASE
    ):
        constraints.append(
            "knowledge_or_interest_alternative"
        )

    if re.search(
        r"\b(?:no (?:prior |previous )?experience required|"
        r"experience is not required)\b",
        requirement,
        re.IGNORECASE
    ) and not constraints:

        result["status"] = "matched"
        result["match_ratio"] = 1.0
        result["reason"] = "Prior experience is not required."

        return result

    domains = detect_experience_domains(requirement)
    skills = extract_skills(requirement)

    result["required_domains"] = domains
    result["required_skills"] = skills

    minimum_months = detect_minimum_experience(
        requirement
    )

    if "academic_eligibility" in constraints:
        minimum_months = None

    result["minimum_months"] = minimum_months

    has_experience_requirement = bool(
        re.search(
            r"\bexperience\b",
            requirement,
            re.IGNORECASE
        )
    )

    if not has_experience_requirement:

        result["reason"] = (
            "No clear prior experience requirement detected."
        )

        return result

    if (
        "academic_eligibility" in constraints
        and not domains
        and not skills
    ):

        result["reason"] = (
            "The requirement concerns academic eligibility "
            "rather than confirmed professional experience."
        )

        return result

    records = normalize_experience_records(
        profile.get("experience", [])
    )

    internship_required = bool(
        re.search(
            r"\binternship experience\b",
            requirement,
            re.IGNORECASE
        )
    )

    for record in records:

        matched_domains = sorted(
            set(domains).intersection(record["domains"])
        )

        matched_skills = sorted(
            set(skills).intersection(record["skills"])
        )

        if not matched_domains and not matched_skills:
            continue

        if internship_required and not record["is_internship"]:
            continue

        evidence = {
            **record,
            "source": "experience",
            "matched_domains": matched_domains,
            "matched_skills": matched_skills,
        }

        result["matched_evidence"].append(evidence)

    # Projects count only when explicitly accepted.

    if project_allowed:

        for project in profile.get("projects", []):

            text = " ".join([
                project.get("title") or "",
                project.get("category") or "",
                *project.get("technologies", [])
            ])

            project_domains = detect_experience_domains(text)
            project_skills = extract_skills(text)

            matched_domains = sorted(
                set(domains).intersection(project_domains)
            )

            matched_skills = sorted(
                set(skills).intersection(project_skills)
            )

            if matched_domains or matched_skills:

                result["matched_evidence"].append({
                    "source": "project",
                    "title": project.get("title"),
                    "duration_months": None,
                    "matched_domains": matched_domains,
                    "matched_skills": matched_skills,
                })

    evidence = result["matched_evidence"]

    if not evidence:

        result["reason"] = (
            "No confirmed relevant experience evidence."
        )

        return result

    # Do not equate internship training with employment.

    if any(
        item.get("is_training")
        for item in evidence
    ):
        constraints.append(
            "training_equivalence_unverified"
        )

    if minimum_months is not None:

        known_durations = [
            item["duration_months"]
            for item in evidence
            if item.get("duration_months") is not None
            and not item.get("is_training")
        ]

        # Avoid summing potentially overlapping periods.

        longest_duration = max(
            known_durations,
            default=0
        )

        if longest_duration < minimum_months:

            constraints.append(
                "minimum_duration_not_confirmed"
            )

    # Multiple domains or skills may have complex AND/OR logic.

    if len(domains) > 1 or len(skills) > 1:

        constraints.append(
            "complex_experience_requirement"
        )

    # A skill mention alone does not establish full role alignment.

    if domains and not any(
        item["matched_domains"]
        for item in evidence
    ):
        constraints.append(
            "domain_alignment_unverified"
        )

    if constraints:

        result["status"] = "partial_match"

        result["reason"] = (
            "Relevant experience evidence found, "
            "but additional criteria require verification."
        )

    else:

        result["status"] = "matched"
        result["match_ratio"] = 1.0

        result["reason"] = (
            "Recognized experience criteria align "
            "with available resume evidence."
        )

    return result