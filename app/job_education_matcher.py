import re
from datetime import date


DEGREE_PATTERNS = {
    "doctorate": r"\b(?:ph\.?d\.?|doctorate|doctoral)\b",
    "masters": r"\b(?:master(?:'s|s)?|m\.?sc\.?|m\.?s\.?|m\.?tech\.?|mba)\b",
    "bachelors": r"\b(?:bachelor(?:'s|s)?|b\.?sc\.?|b\.?s\.?|b\.?tech\.?|undergraduate)\b",
    "associate": r"\bassociate(?:'s|s)?\b",
    "secondary": r"\b(?:high school|secondary school|ged)\b",
}


FIELD_PATTERNS = {
    "Computer Science": r"\bcomputer science\b",
    "Computer Engineering": r"\bcomputer engineering\b",
    "Software Engineering": r"\bsoftware engineering\b",
    "Information Technology": r"\b(?:information technology|IT)\b",
    "Artificial Intelligence": r"\b(?:artificial intelligence|AI)\b",
    "Machine Learning": r"\b(?:machine learning|ML)\b",
    "Data Science": r"\bdata science\b",
    "Information Systems": r"\binformation systems\b",
    "Electrical Engineering": r"\belectrical engineering\b",
    "Engineering": r"\bengineering\b",
    "Statistics": r"\bstatistics\b",
    "Mathematics": r"\bmathematics\b",
    "Business Administration": r"\bbusiness administration\b",
    "Economics": r"\beconomics\b",
    "Finance": r"\bfinance\b",
}


def detect_degree_levels(text):
    """Identify degree levels mentioned in education text."""

    return [
        level
        for level, pattern in DEGREE_PATTERNS.items()
        if re.search(pattern, text, re.IGNORECASE)
    ]


def detect_fields(text):
    """Identify recognized academic fields."""

    fields = []

    for field, pattern in FIELD_PATTERNS.items():

        flags = (
            0
            if field == "Information Technology"
            else re.IGNORECASE
        )

        if re.search(pattern, text, flags):
            fields.append(field)

    return fields


def detect_education_status(dates, reference_year=None):
    """Infer education status from recorded date ranges."""

    if reference_year is None:
        reference_year = date.today().year

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        dates or ""
    )

    if len(years) < 2:
        return "unknown"

    start_year = int(years[0])
    end_year = int(years[-1])

    if start_year > end_year:
        return "unknown"

    if start_year > reference_year:
        return "not_started"

    if end_year > reference_year:
        return "pursuing"

    if end_year < reference_year:
        return "completed"

    return "unknown"


def normalize_education_records(
    education_records,
    reference_year=None,
):
    """Convert resume education records into matching data."""

    normalized = []

    for record in education_records:

        qualification = record.get(
            "qualification", ""
        ) or ""

        dates = record.get("dates", "") or ""

        normalized.append({
            "qualification": qualification,
            "degree_levels": detect_degree_levels(
                qualification
            ),
            "fields": detect_fields(
                qualification
            ),
            "status": detect_education_status(
                dates,
                reference_year
            ),
            "integrated_program": bool(
                re.search(
                    r"\bintegrated\b",
                    qualification,
                    re.IGNORECASE
                )
            ),
            "dates": dates,
            "institution": record.get("institution"),
            "result": record.get("result"),
        })

    return normalized


def detect_additional_constraints(text):
    """Flag restrictions requiring further verification."""

    constraints = []

    patterns = {
        "academic_performance":
            r"\b(?:gpa|cgpa|grade point average)\b",

        "graduation_date":
            r"\bgraduat\w*\b.{0,60}\b20\d{2}\b",

        "academic_year":
            r"\b(?:junior|senior|sophomore|freshman)\b",

        "work_authorization":
            r"\b(?:work authorization|authorized to work|"
            r"optional practical training|OPT)\b",

        "geographic_enrollment":
            r"\b(?:United States|USA|U\.S\.)\b",

        "equivalent_experience":
            r"\bequivalent\b.{0,60}\bexperience\b",

        "institution_requirements":
            r"\b(?:accredited|top-tier)\b",

        "coursework":
            r"\b(?:coursework|course in|courses in)\b",

        "recent_graduation":
            r"\brecently graduated\b",

        "multiple_education_clauses":
            r"\|",
    }

    for name, pattern in patterns.items():

        if re.search(pattern, text, re.IGNORECASE):
            constraints.append(name)

    return constraints


def match_job_education(
    profile,
    job,
    reference_year=None,
):
    """Evaluate education alignment conservatively."""

    requirement = job.get("education_requirements")

    if not isinstance(requirement, str) or not requirement.strip():

        return {
            "status": "not_specified",
            "match_ratio": None,
            "requirement": requirement,
            "matched_evidence": [],
            "unresolved_constraints": [],
            "reason": "No extracted education requirement.",
        }

    required_levels = detect_degree_levels(requirement)
    required_fields = detect_fields(requirement)

    constraints = detect_additional_constraints(
        requirement
    )

    pursuing_required = bool(
        re.search(
            r"\b(?:currently pursuing|currently enrolled|"
            r"actively enrolled|must be enrolled|"
            r"working towards|pursuing)\b",
            requirement,
            re.IGNORECASE
        )
    )

    completed_required = bool(
        re.search(
            r"\b(?:completed|graduated|must hold)\b",
            requirement,
            re.IGNORECASE
        )
    )

    records = normalize_education_records(
        profile.get("education", []),
        reference_year
    )

    evidence = []

    for record in records:

        student_levels = set(record["degree_levels"])
        student_fields = set(record["fields"])

        higher_education = bool(
            student_levels.intersection({
                "associate",
                "bachelors",
                "masters",
                "doctorate",
            })
        )

        if required_levels:

            level_match = bool(
                student_levels.intersection(
                    required_levels
                )
            )

        else:
            level_match = higher_education

        field_match = (
            bool(
                student_fields.intersection(
                    required_fields
                )
            )
            if required_fields
            else None
        )

        if pursuing_required and completed_required:

            status_match = None

        elif pursuing_required:

            status_match = (
                None
                if record["status"] == "unknown"
                else record["status"] == "pursuing"
            )

        elif completed_required:

            status_match = (
                None
                if record["status"] == "unknown"
                else record["status"] == "completed"
            )

        else:
            status_match = None

        evidence.append({
            "qualification": record["qualification"],
            "institution": record["institution"],
            "education_status": record["status"],
            "integrated_program": record["integrated_program"],
            "level_match": level_match,
            "field_match": field_match,
            "status_match": status_match,
            "matched_fields": sorted(
                student_fields.intersection(
                    required_fields
                )
            ),
        })

    matched_evidence = [
        item
        for item in evidence
        if item["level_match"]
        and item["field_match"] is not False
        and item["status_match"] is not False
    ]

    if any(
        item["integrated_program"]
        for item in matched_evidence
    ) and required_levels:

        constraints.append(
            "integrated_program_eligibility"
        )

    if pursuing_required and completed_required:

        constraints.append(
            "ambiguous_enrollment_requirement"
        )

    if not pursuing_required and not completed_required:

        constraints.append(
            "degree_completion_status_unspecified"
        )

    if (
        pursuing_required or completed_required
    ) and any(
        item["status_match"] is None
        for item in matched_evidence
    ):

        constraints.append(
            "enrollment_status_unverified"
        )

    if not required_levels and not required_fields:

        constraints.append(
            "degree_or_field_requirement_unclear"
        )

    constraints = list(dict.fromkeys(constraints))

    if not records:

        status = "unknown"
        ratio = None
        reason = "No student education records available."

    elif matched_evidence and constraints:

        status = "partial_match"
        ratio = None
        reason = (
            "Basic education alignment found, "
            "but additional criteria require verification."
        )

    elif matched_evidence:

        status = "matched"
        ratio = 1.0
        reason = (
            "Recognized education criteria align "
            "with the student profile."
        )

    else:

        status = "unknown"
        ratio = None
        reason = (
            "No confirmed education match. "
            "Additional eligibility review is required."
        )

    return {
        "status": status,
        "match_ratio": ratio,
        "requirement": requirement,
        "required_degree_levels": required_levels,
        "required_fields": required_fields,
        "pursuing_required": pursuing_required,
        "completed_required": completed_required,
        "matched_evidence": matched_evidence,
        "education_comparison": evidence,
        "unresolved_constraints": constraints,
        "reason": reason,
    }