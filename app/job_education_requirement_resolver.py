import re


MANDATORY_SECTION_PATTERN = re.compile(
    r"^\s*(?:minimum|required|basic|mandatory)\s+"
    r"(?:qualifications|requirements)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


SECTION_END_PATTERN = re.compile(
    r"^\s*(?:preferred qualifications|"
    r"preferred requirements|"
    r"desired qualifications|"
    r"nice to have|"
    r"bonus qualifications|"
    r"responsibilities|"
    r"benefits|"
    r"compensation)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


DOCTORAL_STUDENT_PATTERN = re.compile(
    r"\b(?:ph\.?d\.?|doctoral|doctorate)\s+"
    r"(?:degree\s+)?students?\b",
    re.IGNORECASE,
)


AMBIGUOUS_PATTERN = re.compile(
    r"\b(?:or|preferred|ideally|equivalent|"
    r"alternatively|desirable|optional)\b",
    re.IGNORECASE,
)


def resolve_education_requirement(job):
    """Recover narrowly defined mandatory education criteria."""

    existing = job.get("education_requirements")

    if isinstance(existing, str) and existing.strip():
        return {
            "requirement": existing.strip(),
            "source": "structured_education_requirements",
            "mandatory": None,
            "strict_degree_level": None,
        }

    description = job.get("job_description") or ""

    for heading in MANDATORY_SECTION_PATTERN.finditer(description):

        section = description[heading.end():]

        end = SECTION_END_PATTERN.search(section)

        if end:
            section = section[:end.start()]

        for line in section.splitlines():

            line = line.strip()

            if not line:
                continue

            match = DOCTORAL_STUDENT_PATTERN.search(line)

            if not match:
                continue

            # Preserve the doctoral qualification sentence.
            remainder = line[match.end():]

            sentence_end = re.search(
                r"\.(?=\s|[A-Z]|$)",
                remainder
            )

            if sentence_end:
                remainder = remainder[:sentence_end.start()]

            clause = (
                match.group(0) + remainder
            ).strip()

            # Avoid treating alternative degree paths
            # as confirmed doctoral-only requirements.
            if AMBIGUOUS_PATTERN.search(clause):

                if not re.search(
                    r"\bor related (?:areas|fields|disciplines)\b",
                    clause,
                    re.IGNORECASE
                ):
                    continue

                cleaned = re.sub(
                    r"\bor related (?:areas|fields|disciplines)\b",
                    "",
                    clause,
                    flags=re.IGNORECASE
                )

                if AMBIGUOUS_PATTERN.search(cleaned):
                    continue

            if re.search(
                r"\b(?:master|bachelor|undergraduate|"
                r"m\.?sc\.?|b\.?sc\.?)\b",
                clause,
                re.IGNORECASE
            ):
                continue

            # Require the doctoral phrase to begin
            # the qualification statement.
            prefix = line[:match.start()].strip(" -*")

            if prefix:
                continue

            return {
                "requirement": clause,
                "source": "mandatory_qualification_section",
                "mandatory": True,
                "strict_degree_level": "doctorate",
            }

    return {
        "requirement": None,
        "source": "not_specified",
        "mandatory": None,
        "strict_degree_level": None,
    }
