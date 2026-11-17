
import re


import unicodedata


def clean_resume_line(line):
    line = unicodedata.normalize("NFKC", line)

    # Normalize common PDF ligatures and whitespace.
    line = line.replace("\u00a0", " ")
    line = re.sub(r"\s+", " ", line)

    return line.strip()


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

        line = clean_resume_line(raw_line)

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


def group_project_lines(project_lines):
    """
    Prepare extracted project lines for future grouping.
    Does not identify individual projects yet.
    """
    cleaned_lines = []

    for line in project_lines:
        cleaned = clean_resume_line(line)

        if cleaned:
            cleaned_lines.append(cleaned)

    return {
        "raw_lines": cleaned_lines,
        "line_count": len(cleaned_lines),
    }

def build_project_record(project_lines):
    """
    Convert one project's lines into a structured record.

    Assumes:
    1. Title
    2. Category
    3. Comma-separated technologies
    4. Description and optional link
    """
    lines = [
        clean_resume_line(line)
        for line in project_lines
        if clean_resume_line(line)
    ]

    if len(lines) < 3:
        return None

    record = {
        "title": lines[0],
        "category": lines[1],
        "technologies": [
            tech.strip()
            for tech in lines[2].split(",")
            if tech.strip()
        ],
        "description": [],
        "link": None,
    }

    for line in lines[3:]:
        if line.lower().startswith("project link:"):
            record["link"] = line.split(":", 1)[1].strip()
        elif (
            record["description"]
            and not record["description"][-1].endswith((".", "!", "?"))
        ):
            record["description"][-1] += " " + line
        else:
            record["description"].append(line)

    return record


def extract_project_records(project_lines):
    """
    Group project lines using the observed resume format:
    title -> category -> technologies -> descriptions.

    This is a format-specific heuristic, not a universal
    resume project parser.
    """
    lines = [
        clean_resume_line(line)
        for line in project_lines
        if clean_resume_line(line)
    ]

    project_starts = []

    for i in range(len(lines) - 2):
        category = lines[i + 1]
        technologies = lines[i + 2]

        if (
            category.lower().endswith("project")
            and "," in technologies
        ):
            project_starts.append(i)

    projects = []

    for index, start in enumerate(project_starts):
        end = (
            project_starts[index + 1]
            if index + 1 < len(project_starts)
            else len(lines)
        )

        project = build_project_record(lines[start:end])

        if project:
            projects.append(project)

    return projects


def extract_experience_records(experience_lines):
    """
    Group experience lines using the observed resume format.

    Assumes each internship contains:
    company, details, role, duration/status,
    followed by responsibility sentences.
    """
    lines = [
        clean_resume_line(line)
        for line in experience_lines
        if isinstance(line, str) and clean_resume_line(line)
    ]

    records = []
    index = 0

    while index < len(lines):
        if index + 3 >= len(lines):
            break

        company = lines[index]
        details = lines[index + 1]
        role = lines[index + 2]
        duration = lines[index + 3]

        # Only recognize blocks with an internship role.
        if not re.search(r"\b(intern|internship)\b", role, re.I):
            index += 1
            continue

        index += 4
        responsibilities = []

        while index < len(lines):
            # A new block begins when the third line
            # looks like an internship role.
            if (
                index + 3 < len(lines)
                and re.search(
                     r"\binternship\b",
                    lines[index + 1],
                    re.I,
                )
                and re.search(
                    r"\bintern\b",
                    lines[index + 2],
                    re.I
                )
            ):
                break

            responsibilities.append(lines[index])
            index += 1

        records.append({
            "company": company,
            "details": details,
            "role": role,
            "duration": duration,
            "responsibilities": responsibilities,
        })

    return records

def extract_education_records(education_lines):
    """
    Group education lines using the observed resume format:
    qualification, dates, institution, academic result.
    """
    lines = [
        clean_resume_line(line)
        for line in education_lines
        if isinstance(line, str) and clean_resume_line(line)
    ]

    records = []

    for index in range(0, len(lines), 4):
        group = lines[index:index + 4]

        if len(group) != 4:
            continue

        records.append({
            "qualification": group[0],
            "dates": group[1],
            "institution": group[2],
            "result": group[3],
        })

    return records


def extract_award_records(award_lines):
    """
    Combine PDF-wrapped award and achievement lines
    into complete entries.
    """
    lines = [
        clean_resume_line(line)
        for line in award_lines
        if isinstance(line, str) and clean_resume_line(line)
    ]

    records = []
    current = ""

    for line in lines:
        if current:
            current += " " + line
        else:
            current = line

        if current.endswith((".", "!", "?")):
            records.append({
                "description": current
            })
            current = ""

    if current:
        records.append({
            "description": current
        })

    return records


def extract_skill_records(skill_lines):
    """
    Convert raw resume skills into categorized skill records.
    """

    records = []
    soft_skills = []

    for raw_line in skill_lines:
        if not isinstance(raw_line, str):
            continue

        line = clean_resume_line(raw_line)

        if not line:
            continue

        if ":" in line:
            category, values = line.split(":", 1)

            skills = [
                skill.strip()
                for skill in values.split(",")
                if skill.strip()
            ]

            if skills:
                records.append({
                    "category": category.strip(),
                    "skills": skills,
                })
        else:
            soft_skills.append(line)

    if soft_skills:
        records.append({
            "category": "Soft Skills",
            "skills": soft_skills,
        })

    return records




