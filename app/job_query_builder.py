from app.skill_vocabulary import extract_skills


SOFT_SKILLS = {
    "communication",
    "teamwork",
    "collaboration",
    "problem-solving",
    "analytical skills",
    "time management",
    "adaptability",
    "leadership",
    "attention to detail",
    "customer service",
    "willingness to learn",
}


DOMAIN_KEYWORDS = {
    "Artificial Intelligence": [
        "artificial intelligence",
        "ai",
        "ai-ml",
    ],
    "Machine Learning": [
        "machine learning",
        "ml",
        "ai-ml",
    ],
    "Generative AI": [
        "generative ai",
        "genai",
    ],
    "Data Science": [
        "data science",
        "data scientist",
    ],
    "Data Analytics": [
        "data analytics",
        "data analysis",
        "data analyst",
    ],
    "Frontend Development": [
        "frontend",
        "front-end",
        "front end",
    ],
    "Backend Development": [
        "backend",
        "back-end",
        "back end",
    ],
    "Full Stack Development": [
        "full stack",
        "full-stack",
    ],
    "Software Development": [
        "software development",
        "software engineering",
        "software developer",
        "software engineer",
    ],
    "Web Development": [
        "web development",
        "web developer",
    ],
    "Mobile Application Development": [
        "mobile development",
        "mobile application",
        "android development",
        "ios development",
    ],
    "Cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
    ],
    "Cloud Computing": [
        "cloud computing",
        "cloud engineering",
    ],
    "DevOps": [
        "devops",
    ],
    "UI/UX Design": [
        "ui/ux",
        "ui design",
        "ux design",
    ],
    "Data Engineering": [
        "data engineering",
        "data engineer",
    ],
    "Software Testing": [
        "software testing",
        "quality assurance",
    ],
    "Computer Science": [
        "computer science",
    ],
    "Information Technology": [
        "information technology",
    ],
    "Robotics": [
        "robotics",
    ],
    "Embedded Systems": [
        "embedded systems",
    ],
}


def unique_values(values):
    """Remove duplicate strings while preserving order."""

    result = []
    seen = set()

    for value in values:
        if not isinstance(value, str):
            continue

        value = value.strip()
        key = value.casefold()

        if value and key not in seen:
            seen.add(key)
            result.append(value)

    return result


def identify_domains(text):
    """Identify career domains using predefined keywords."""

    import re

    if not isinstance(text, str):
        return []

    domains = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            pattern = (
                r"(?<!\w)"
                + re.escape(keyword)
                + r"(?!\w)"
            )

            if re.search(pattern, text, re.IGNORECASE):
                domains.append(domain)
                break

    return unique_values(domains)


def get_technical_skills(skills):
    """Keep recognized technical skills for retrieval."""

    recognized = []

    for skill in skills:
        if not isinstance(skill, str):
            continue

        recognized.extend(extract_skills(skill))

    return [
        skill
        for skill in unique_values(recognized)
        if skill.casefold() not in SOFT_SKILLS
    ]


def build_search_queries(profile):
    """Generate focused internship queries from a student profile."""

    if not isinstance(profile, dict):
        raise ValueError(
            "Student profile must be a dictionary."
        )

    queries = []

    def add_query(query_type, query):
        query = query.strip()

        if not query:
            return

        if any(
            item["query"].casefold() == query.casefold()
            for item in queries
        ):
            return

        queries.append({
            "query_type": query_type,
            "query": query,
        })

    # 1. Technical skills query
    technical_skills = get_technical_skills(
        profile.get("skills", [])
    )

    if technical_skills:
        add_query(
            "technical_skills",
            "Internships involving technical skills in "
            + ", ".join(technical_skills[:25])
            + "."
        )

    # 2. Project-based query
    project_domains = []
    project_skills = []

    for project in profile.get("projects", []):
        title = project.get("title") or ""
        category = project.get("category") or ""

        project_domains.extend(
            identify_domains(title + " " + category)
        )

        technologies = project.get("technologies") or []

        if isinstance(technologies, str):
            technologies = [technologies]

        project_skills.extend(
            get_technical_skills(technologies)
        )

    project_domains = unique_values(project_domains)
    project_skills = unique_values(project_skills)

    if project_domains or project_skills:
        query = "Internships related to practical projects"

        if project_domains:
            query += " in " + ", ".join(project_domains)

        if project_skills:
            query += (
                " involving "
                + ", ".join(project_skills[:15])
            )

        add_query("projects", query + ".")

    # 3. Experience-based query
    experience_domains = []
    experience_skills = []

    for experience in profile.get("experience", []):
        role = experience.get("role") or ""

        experience_domains.extend(
            identify_domains(role)
        )

        responsibilities = (
            experience.get("responsibilities") or []
        )

        if isinstance(responsibilities, str):
            responsibilities = [responsibilities]

        responsibility_text = " ".join(
            value
            for value in responsibilities
            if isinstance(value, str)
        )

        experience_skills.extend(
            get_technical_skills(
                extract_skills(
                    role + " " + responsibility_text
                )
            )
        )

    experience_domains = unique_values(experience_domains)
    experience_skills = unique_values(experience_skills)

    if experience_domains or experience_skills:
        query = "Internships suitable for students with experience"

        if experience_domains:
            query += (
                " in " + ", ".join(experience_domains)
            )

        if experience_skills:
            query += (
                " and knowledge of "
                + ", ".join(experience_skills[:15])
            )

        add_query("experience", query + ".")

    # 4. Education-based query
    education_domains = []

    for education in profile.get("education", []):
        qualification = (
            education.get("qualification") or ""
        )

        education_domains.extend(
            identify_domains(qualification)
        )

    education_domains = unique_values(education_domains)

    if education_domains:
        add_query(
            "education",
            "Internship opportunities for university "
            "students studying "
            + ", ".join(education_domains)
            + "."
        )

    # Avoid returning arbitrary jobs for an empty profile
    if not queries:
        raise ValueError(
            "Insufficient career-related information "
            "to generate internship search queries."
        )

    return queries