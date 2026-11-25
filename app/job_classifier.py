
import re


DOMAIN_PATTERNS = {
    "Artificial Intelligence and Machine Learning": (
        r"\b(machine learning|artificial intelligence|"
        r"AI|ML|NLP|deep learning|computer vision|"
        r"computational imaging)\b"
    ),

    "Data Science": (
        r"\b(data science|data scientist)\b"
    ),

    "Data Engineering": (
        r"\b(data engineer|data engineering|database)\b"
    ),

    "Data Analytics": (
        r"\b(data analyst|data analytics|analytics|"
        r"data analysis|business intelligence|"
        r"data quality|data intern)\b"
    ),

    "Cybersecurity": (
        r"\b(cybersecurity|cyber security|"
        r"information security|SOC analyst|"
        r"digital forensics|DFIR|FedRAMP|IT security)\b"
    ),

    "Cloud Computing and DevOps": (
        r"\b(cloud|devops)\b"
    ),

    "Full Stack Development": (
        r"\b(full stack|full-stack)\b"
    ),

    "Frontend Development": (
        r"\b(frontend|front end|front-end)\b"
    ),

    "Backend Development": (
        r"\b(backend|back end|back-end)\b"
    ),

    "Mobile Application Development": (
        r"\b(mobile app|mobile application|"
        r"android|iOS|flutter)\b"
    ),

    "UI/UX Design": (
        r"\b(ui/ux|ux design|ui design|"
        r"user experience|web design|"
        r"UX games|mobile product design)\b"
    ),

    "Software Testing and Quality Assurance": (
        r"\b(software testing|quality assurance|"
        r"QA|test engineer|software quality engineer|"
r"global quality IT)\b"
    ),

    "Web Development": (
        r"\b(web development|web developer|"
        r"wordpress)\b"
    ),

    "Robotics and Automation": (
        r"\b(robotics|automation)\b"
    ),

    "Hardware and Embedded Systems": (
        r"\b(hardware engineering|hardware engineer|"
        r"embedded systems|firmware)\b"
    ),

    "Networking and IT Infrastructure": (
        r"\b(network engineer|network engineering|"
        r"systems engineer|systems administrator|"
        r"technical support|PC technician|"
r"IT support|IT end user services)\b"
    ),

    "Technical Product Management": (
        r"\b(product management|product manager)\b"
    ),

    "IT Business Analysis": (
        r"\b(business analyst|business analysis)\b"
    ),

    "Geographic Information Systems": (
        r"\b(geographic information systems|GIS)\b"
    ),

    "Software Development": (
        r"\b(software|developer|programming|"
        r"application development|SDE|SWE)\b"
    ),

    "Information Technology": (
        r"\b(information technology|IT|"
        r"digital technology|computer science|"
        r"seasonal technology|informatics)\b"
    )
}


def classify_job_domain(title, description=""):
    title = title.strip()
    description = description.strip()
        # Handle specialized roles with generic job titles
    if re.search(r"\bapplication developer\b", title, re.IGNORECASE):
        if re.search(
            r"\b(flutter|react native|mobile app development)\b",
            description,
            re.IGNORECASE
        ):
            return "Mobile Application Development"

    # Software asset management is not software development
    if re.search(r"\bsoftware librarian\b", title, re.IGNORECASE):
        return "Information Technology"

    # First priority: job title
    for domain, pattern in DOMAIN_PATTERNS.items():
        if re.search(pattern, title, re.IGNORECASE):
            return domain

    # Second priority: job description
    for domain, pattern in DOMAIN_PATTERNS.items():
        if re.search(pattern, description, re.IGNORECASE):
            return domain

    return "Other Technology"
