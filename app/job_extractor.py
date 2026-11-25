
import re
import unicodedata
from app.skill_vocabulary import extract_skills


SECTION_ALIASES = {
    "responsibilities": [
        "responsibilities",
        "key responsibilities",
        "duties and responsibilities",
        "job responsibilities",
        "what you'll do",
        "what you will do",
        "your responsibilities",
        "responsibilities include"
    ],

    "required_qualifications": [
        "qualifications",
        "required qualifications",
        "basic qualifications",
        "minimum qualifications",
        "basic required qualifications",
        "requirements",
        "position requirements",
        "required skills",
        "what you'll need",
        "what we're looking for",
        "knowledge, skills, and abilities"
    ],

    "preferred_qualifications": [
        "preferred qualifications",
        "additional preferred qualifications",
        "preferred skills",
        "desired qualifications",
        "nice to have",
        "bonus points"
    ],

    "education": [
        "education",
        "education requirements",
        "educational requirements"
    ],

    "experience": [
        "experience",
        "experience requirements",
        "required experience",
        "education and experience"
    ],

    "other": [
        "about the company",
        "about the organization",
        "company description",
        "about us",
        "benefits",
        "compensation",
        "additional information",
        "equal opportunity employer",
        "physical requirements"
    ]
}


def clean_job_description(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\u00a0", " ")
    text = text.replace("\u2019", "'")
    text = text.replace("\u2018", "'")

    text = re.sub(r"\r\n?", "\n", text)
    # Preserve potential qualification statement boundaries
    text = re.sub(r"(?<=[a-z0-9.)])[ \t]{2,}(?=[A-Z])", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Separate section headings merged with numbered lists
    text = re.sub(
        r"(?im)^([ \t]*(?:Responsibilities|Qualifications|Requirements|Key Responsibilities|Required Qualifications|Preferred Qualifications))(?=\d+[.)])",
        r"\1\n",
        text
    )
    
        # Separate merged section headings from their content
    text = re.sub(
        r"(?m)^(Company Description|Role Description|Job Description|Qualifications|Responsibilities|Required Qualifications|Preferred Qualifications)(?=[A-Z])",
        r"\1\n",
        text
    )
    
        # Restore missing spaces between concatenated sentences
    text = re.sub(
        r"(?<=[a-z])\.(?=[A-Z][a-z])",
        ". ",
        text
    )
    
 
    # Separate known concatenated qualification boundaries
    text = re.sub(
        r"(?<=[a-z])(?=(?:Experience|Knowledge|Excellent|Strong|Currently|Databases|Cascading|Bonus|Comfortable|Undergraduate|Must|Ability|Proficiency|Programming|Enrolled|Preferred|Required|Familiarity|Understanding)\b)",
        "\n",
        text
    )

    # Handle merged statements following uppercase skill names
    text = re.sub(
        r"(?<=[A-Z])(?=(?:Experience|Knowledge|Bonus|Proficiency|Ability|Enrolled|Strong|Must)\b)",
        "\n",
        text
    )
  

    text = re.sub(
        r"(?<=skills)(?=[A-Z])",
        "\n",
        text
    )

    text = re.sub(
        r"(?<=abilities)(?=[A-Z])",
        "\n",
        text
    )
    
    
    # Separate inline section headings from their content
    text = re.sub(
        r"(?im)^([^\n:?!*●]{2,100})([:?!*]+|(?=●))[ \t]*(?=\S)",
        lambda match: (
            match.group(1).strip() + "\n"
            if identify_section(match.group(1))
            else match.group(0)
        ),
        text
    )
    
    # Separate company introduction headings with repeated company names
    text = re.sub(
        r"(?m)^([ \t]*About[ \t]+([A-Z][A-Za-z0-9&-]*))(?=\2\b)",
        r"\1\n",
        text
        )
    
    # Separate known headings merged directly with content
    text = re.sub(
        r"(?m)^([ \t]*(?:Key Responsibilities|"
        r"Responsibilities|Computer Skills|Position Summary|"
        r"Learning Opportunities|Education and/or Experience|"
        r"Reasoning Ability|Certificates, Licenses, Registrations|"
        r"Working Model|Pay & Benefits))(?=[A-Z])",
    r"\1\n",
    text
)

    return text.strip()



def identify_section(line):
    normalized = line.strip().casefold()
    normalized = normalized.strip(" :?*!").strip()
    
    # Recognize company introduction headings
    if normalized != "about you" and re.fullmatch(
        r"about\s+[\w][\w\s&.,'’\-]{0,79}", normalized
        ):
        return "other"

    # Recognize employment metadata
    if normalized.startswith(("job types:", "job type:")):
        return "other"

    additional_aliases = {
        
                "working model": "other",
        "pay & benefits": "other",
        "reasoning ability": "required_qualifications",
        "certificates, licenses, registrations": "required_qualifications",
        
    # Final critical record heading corrections

    # Responsibilities
    "responsibilities and impact": "responsibilities",
    "as a software development intern, you will": "responsibilities",
    "as part of the project, you will": "responsibilities",
    "responsibilities for it support technician": "responsibilities",
    "you will": "responsibilities",
    "responsibilities include and are not limited to": "responsibilities",
    "core responsibilities": "responsibilities",
    "a day in the life of our research intern - computer vision and medical imaging": "responsibilities",
    "in your role, you will": "responsibilities",
    "what you'll be doing": "responsibilities",

    # Required qualifications
    "core experience & requirements": "required_qualifications",
    "computer skills": "required_qualifications",
    "our ideal intern can": "required_qualifications",
    "you have": "required_qualifications",
    "qualifications for this position include": "required_qualifications",
    "qualifications for technical support": "required_qualifications",
    "your areas of knowledge and expertise": "required_qualifications",
    "you might be a fit if you": "required_qualifications",
    "requirements for success": "required_qualifications",
    "software and technology": "required_qualifications",
    "about you": "required_qualifications",
    "as our ideal candidate": "required_qualifications",
    "you'll need to have": "required_qualifications",

    # Preferred qualifications
    "even better if you have one or more of the following": "preferred_qualifications",

    # Education
    "education and training": "education",

    # Non-matching sections
    "learning opportunities": "other",
    "compensation/benefits information": "other",
    "right to work requirements": "other",
    "where you'll be working": "other",
    "workplace type": "other",
    "values": "other",
    "faq": "other",
        
        # Additional responsibility headings
        "essential functions": "responsibilities",
        "in this role, you will": "responsibilities",
        "how you will contribute": "responsibilities",
        "internship responsibilities may include": "responsibilities",
        "general responsibilities": "responsibilities",
        "position responsibilities": "responsibilities",
        "key job responsibilities": "responsibilities",
        "things you'll do": "responsibilities",
        "what you'll get to do": "responsibilities",
        "what you will do": "responsibilities",
        "role responsibilities": "responsibilities",
        "essential responsibilities": "responsibilities",
        "representative duties and tasks": "responsibilities",
        "principal duties and responsibilities": "responsibilities",
        "essential duties and responsibilities": "responsibilities",

        # Additional qualification headings
        "what you'll bring": "required_qualifications",
        "skills required": "required_qualifications",
        "required qualifications & skills": "required_qualifications",
        "ideal qualifications & skills": "required_qualifications",
        "qualifications & skills": "required_qualifications",
        "additional skills & qualifications": "required_qualifications",
        "other requirements": "required_qualifications",
        "knowledge, skills and abilities (ksas)": "required_qualifications",
        "required knowledge, skills, and abilities": "required_qualifications",
        "minimum knowledge, skills and abilities required": "required_qualifications",
        "required minimum qualifications": "required_qualifications",
        "minimum requirements/educational requirements": "required_qualifications",
        "minimum qualifications and eligibility requirements": "required_qualifications",
        "what you will need": "required_qualifications",
        "you'll bring these qualifications": "required_qualifications",
        "what we're looking for on your resume": "required_qualifications",
        "knowledge and skills": "required_qualifications",
        "target skills": "required_qualifications",
        "job requirements": "required_qualifications",

        # Additional preferred qualification headings
        "preferred requirements": "preferred_qualifications",
        "intern preferred qualifications": "preferred_qualifications",
        "what would be nice to have": "preferred_qualifications",
        "these qualifications would be nice to have": "preferred_qualifications",
        "additional qualifications": "preferred_qualifications",

        # Additional education headings
        "education and/or experience": "experience",
        "experience and education requirements": "experience",
        "target majors": "education",

        # Additional non-requirement headings
        "company overview": "other",
        "office life & perks": "other",
        "compensation and benefits": "other",
        "expected compensation": "other",
        "salary range disclaimer": "other",
        "equal employment opportunity": "other",
        "benefits & perks": "other",
        "pay transparency": "other",
        "application": "other",

        # General information
        "position summary": "general",
        "position overview": "general",
        "job overview": "general",
        "overview": "general",
        "the opportunity": "general",
        "what this role is about": "general",

        # Responsibilities
        "role description": "responsibilities",
        "job description": "responsibilities",
        "expectations": "responsibilities",
        "a day in the life": "responsibilities",
        "job responsibilities and essential duties": "responsibilities",
        "primary responsibilities": "responsibilities",
        "what will you do": "responsibilities",
        "what you'll be tasked to do": "responsibilities",
        "how you'll make an impact": "responsibilities",
        "key responsibilities for this role include": "responsibilities",

        # Required qualifications
        "required skills and experiences": "required_qualifications",
        "required skills and experience": "required_qualifications",
        "minimum requirements": "required_qualifications",
        "intern requirements": "required_qualifications",
        "required knowledge, skills, and abilities": "required_qualifications",
        "who are we looking for": "required_qualifications",
        "what we're looking for in our ideal candidate": "required_qualifications",
        "what skills and knowledge should you bring": "required_qualifications",
        "what skills and knowledge you should bring": "required_qualifications",
        "what you need to succeed": "required_qualifications",
        "the minimum qualifications for this role are": "required_qualifications",

        # Preferred qualifications
        "bonus": "preferred_qualifications",
        "desired skills": "preferred_qualifications",

        # Unrelated information
        "compensation & benefits details": "other",
        "physical requirements (with or without accommodation)": "other",
        "what we offer": "other",
        "what you'll gain": "other",
        "what we can offer you": "other",
        "why us": "other",
        "why intern with us": "other",
        "how to apply": "other",
        "our company": "other",
        "global privacy notice": "other"
    }

    if normalized in additional_aliases:
        return additional_aliases[normalized]

    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    return None



def extract_job_sections(description):
    description = clean_job_description(description)

    sections = {
        "general": [],
        "responsibilities": [],
        "required_qualifications": [],
        "preferred_qualifications": [],
        "education": [],
        "experience": [],
        "other": []
    }

    current_section = "general"

    for line in description.splitlines():
        line = line.strip()

        if not line:
            continue

        detected_section = identify_section(line)

        if detected_section:
            current_section = detected_section
            continue

        sections[current_section].append(line)

    return sections
def split_job_statements(lines):
    statements = []

    for line in lines:
        parts = re.split(
            r"(?<=[.!?])\s+(?=[A-Z])|[•▪●;\n]+",
            line
        )

        for part in parts:
            part = part.strip()

            if part:
                statements.append(part)

    return statements


PREFERRED_QUALIFICATION_PATTERN = re.compile(
    r"\b("
    r"preferred|"
    r"is a plus|"
    r"is plus|"
    r"are a plus|"
    r"nice to have|"
    r"desirable|"
    r"desired|"
    r"highly desired|"
    r"advantageous|"
    r"bonus points|"
    r"not required|"
    r"an added advantage|"
    r"would be a plus|"
    r"beneficial|"
    r"an advantage|"
    r"optional"
    r")\b",
    re.IGNORECASE
)



def is_preferred_qualification(statement):
    return bool(
        PREFERRED_QUALIFICATION_PATTERN.search(statement)
    )
    
def extract_job_skills(sections):
    required_skills = []
    preferred_skills = []

    required_statements = split_job_statements(
        sections.get("required_qualifications", [])
    )

    preferred_statements = split_job_statements(
        sections.get("preferred_qualifications", [])
    )

    for statement in required_statements:
        skills = extract_skills(statement)

        if is_preferred_qualification(statement):
            preferred_skills.extend(skills)
        else:
            required_skills.extend(skills)

    for statement in preferred_statements:
        preferred_skills.extend(extract_skills(statement))

    # Remove duplicate skills
    required_skills = list(dict.fromkeys(required_skills))
    preferred_skills = list(dict.fromkeys(preferred_skills))

    # Required skills take priority over preferred skills
    preferred_skills = [
        skill for skill in preferred_skills
        if skill not in required_skills
    ]

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills
    }
    

EDUCATION_REQUIREMENT_PATTERN = re.compile(
    r"\b("
    r"bachelor|"
    r"master|"
    r"bachelor's|"
    r"master's|"
    r"associate's|"
    r"undergraduate|"
    r"postgraduate|"
    r"graduate degree|"
    r"degree|"
    r"currently enrolled|"
    r"currently pursuing|"
    r"college student|"
    r"university student|"
    r"high school diploma|"
    r"PhD|"
    r"doctorate|"
    r"GPA|"
    r"BSc|"
    r"MSc|"
    r"BTech|"
    r"MTech"
    r")\b",
    re.IGNORECASE
)


def extract_education_requirements(sections):
    education_requirements = []

    relevant_sections = [
        "education",
        "required_qualifications",
        "preferred_qualifications",
        "experience",
        "general",
        "responsibilities"
    ]

    for section in relevant_sections:
        statements = split_job_statements(
            sections.get(section, [])
        )

        for statement in statements:
            if EDUCATION_REQUIREMENT_PATTERN.search(statement):
                education_requirements.append(statement)

    return list(dict.fromkeys(education_requirements))


EXPERIENCE_REQUIREMENT_PATTERN = re.compile(
    r"\b("
    r"\d+\s*(?:[-–]\s*\d+)?\s*\+?\s*(?:years?|months?)|"
    r"prior experience|"
    r"previous experience|"
    r"professional experience|"
    r"professional work experience|"
    r"work experience|"
    r"internship experience|"
    r"previous internship|"
    r"prior internship|"
    r"relevant experience|"
    r"related experience|"
    r"no experience required|"
    r"no prior experience|"
    r"no professional experience|"
    r"academic projects|"
    r"equivalent experience"
    r")\b",
    re.IGNORECASE
)


def extract_experience_requirements(sections):
    experience_requirements = []

    relevant_sections = [
        "experience",
        "required_qualifications",
        "preferred_qualifications",
        "education",
        "general",
        "responsibilities"
    ]

    for section in relevant_sections:
        statements = split_job_statements(
            sections.get(section, [])
        )


        for statement in statements:
            if re.search(
                r"\b(pay range|salary|compensation|hourly rate|pay rate)\b",
                statement,
                re.IGNORECASE
            ):
                continue

            if EXPERIENCE_REQUIREMENT_PATTERN.search(statement):
                experience_requirements.append(statement)


    return list(dict.fromkeys(experience_requirements))
