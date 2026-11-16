
import re

SECTION_ALIASES = {
    "SKILLS": "skills",
    "TECHNICAL SKILLS": "skills",
    "SOFT SKILLS": "skills",
    "CORE COMPETENCIES": "skills",

    "EDUCATION": "education",
    "ACADEMIC QUALIFICATIONS": "education",

    "EXPERIENCE": "experience",
    "WORK EXPERIENCE": "experience",
    "PROFESSIONAL EXPERIENCE": "experience",
    "INTERNSHIPS": "experience",
    "INDUSTRY EXPOSURE": "experience",

    "PROJECTS": "projects",
    "ACADEMIC PROJECTS": "projects",
    "PERSONAL PROJECTS": "projects",

    "CERTIFICATIONS": "certifications",
    "CERTIFICATES": "certifications",

    "AWARDS": "awards",
    "ACHIEVEMENTS": "awards",
    "CO-CURRICULAR ACHIEVEMENTS": "awards",
    "EXTRA-CURRICULAR ACHIEVEMENTS": "awards",

    "LANGUAGES": "languages",
    "LANGUAGES KNOWN": "languages",
}

OTHER_HEADINGS = {
    "PROFESSIONAL SUMMARY",
    "SUMMARY",
    "PROFILE",
    "OBJECTIVE",
    "PERSONAL DETAILS",
    "INTERESTS",
    "HOBBIES",
    "DECLARATION",
}


def extract_structured_data(text):
    result = {
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "awards": [],
        "languages": [],
    }

    current_section = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        normalized = re.sub(
            r"\s+", " ", line
        ).strip().upper().rstrip(":")

        if normalized in SECTION_ALIASES:
            current_section = SECTION_ALIASES[normalized]
            continue

        if normalized in OTHER_HEADINGS:
            current_section = None
            continue

        if normalized.startswith("LANGUAGES:"):
            value = line.split(":", 1)[1].strip()
            result["languages"].extend(
                item.strip()
                for item in value.split(",")
                if item.strip()
            )
            continue

        if current_section:
            result[current_section].append(line)

    return result
