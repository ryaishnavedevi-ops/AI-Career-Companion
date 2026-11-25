import re

SKILL_ALIASES = {
    
    # Cloud and distributed computing
    "Cloud Computing": ["cloud computing"],
    "Distributed Systems": ["distributed systems", "distributed system"],
    "Distributed Computing": ["distributed computing"],

    # Office productivity
    "Microsoft Office": [
        "microsoft office suite",
        "microsoft office",
        "ms office",
        "ms office suite"
    ],

    # Cybersecurity and networking
    "Data Encryption": ["data encryption"],
    "Multi-Factor Authentication": [
        "multi-factor authentication",
        "multifactor authentication",
        "multi factor authentication",
        "MFA"
    ],
    "LDAP": ["LDAP", "lightweight directory access protocol"],
    "Network Traffic Analysis": ["network traffic analysis"],
    "Packet Analysis": ["packet analysis"],
    "Malware Analysis": ["malware analysis"],

    # Audio and data processing
    "Audio Processing": ["audio processing", "audio signal processing"],
    "Data Cleaning": ["data cleaning", "data cleansing"],

    # Programming
    "Scripting": ["scripting", "scripting languages"],

    # Professional certifications
    "CCNA": ["CCNA"],
    "CompTIA Security+": ["CompTIA Security+", "Security+", "Security +"],
    "CompTIA Network+": ["CompTIA Network+", "Network+", "Network +"],


    # Programming Languages
    "Python": ["Python"],
    "Java": ["Java"],
    "JavaScript": ["JavaScript", "JS"],
    "TypeScript": ["TypeScript"],
    "C++": ["C++"],
    "C#": ["C#"],
    "C": ["C programming", "C language"],
    "R": ["R programming", "R language"],
    "Go": ["Golang", "Go programming"],
    "PHP": ["PHP"],
    "SQL": ["SQL"],
    "MATLAB": ["MATLAB"],
    "Kotlin": ["Kotlin"],
    "Swift": ["Swift"],

    # Web Development
    "HTML": ["HTML", "HTML5"],
    "CSS": ["CSS", "CSS3", "Cascading Style Sheets"],
    "React": ["React", "React.js", "ReactJS"],
    "Angular": ["Angular", "AngularJS"],
    "Vue.js": ["Vue.js", "VueJS"],
    "Node.js": ["Node.js", "NodeJS"],
    "Express.js": ["Express.js", "ExpressJS"],
    "FastAPI": ["FastAPI"],
    "Django": ["Django"],
    "Flask": ["Flask"],
    "Spring Boot": ["Spring Boot"],
    "REST APIs": ["REST API", "REST APIs", "RESTful APIs"],
    ".NET": [".NET", "ASP.NET"],
    "WordPress": ["WordPress"],

    # Artificial Intelligence and Machine Learning
    "Machine Learning": ["Machine Learning", "ML"],
    "Artificial Intelligence": ["Artificial Intelligence", "AI"],
    "Deep Learning": ["Deep Learning"],
    "Natural Language Processing": [
        "Natural Language Processing", "NLP"
    ],
    "Computer Vision": ["Computer Vision"],
    "Generative AI": ["Generative AI", "GenAI"],
    "Large Language Models": [
        "Large Language Models", "LLM", "LLMs"
    ],
    "TensorFlow": ["TensorFlow"],
    "PyTorch": ["PyTorch"],
    "Scikit-learn": ["Scikit-learn", "sklearn"],
    "Keras": ["Keras"],
    "OpenCV": ["OpenCV"],

    # Data Science and Analytics
    "Pandas": ["Pandas"],
    "NumPy": ["NumPy"],
    "Matplotlib": ["Matplotlib"],
    "Seaborn": ["Seaborn"],
    "Data Analysis": ["Data Analysis", "Data Analytics"],
    "Data Visualization": ["Data Visualization"],
    "Statistics": ["Statistics", "Statistical Analysis"],
    "Microsoft Excel": ["Microsoft Excel", "MS Excel", "Excel"],
    "Power BI": ["Power BI", "PowerBI"],
    "Tableau": ["Tableau"],
    "Apache Spark": ["Apache Spark", "PySpark"],
    "Hadoop": ["Hadoop"],
    "ETL": ["ETL", "Extract Transform Load"],

    # Databases
    "MySQL": ["MySQL"],
    "PostgreSQL": ["PostgreSQL", "Postgres"],
    "MongoDB": ["MongoDB"],
    "SQLite": ["SQLite"],
    "Redis": ["Redis"],
    "SQL Server": ["SQL Server", "MSSQL"],
    "Database Management": ["Database Management"],

    # Cloud and DevOps
    "AWS": ["AWS", "Amazon Web Services"],
    "Microsoft Azure": ["Microsoft Azure", "Azure"],
    "Google Cloud": ["Google Cloud", "GCP"],
    "Docker": ["Docker"],
    "Kubernetes": ["Kubernetes", "K8s"],
    "Jenkins": ["Jenkins"],
    "Terraform": ["Terraform"],
    "CI/CD": ["CI/CD", "Continuous Integration"],
    "Linux": ["Linux"],
    "Git": ["Git"],
    "GitHub": ["GitHub"],
    "GitLab": ["GitLab"],

    # Mobile Development
    "Flutter": ["Flutter"],
    "Dart": ["Dart"],
    "React Native": ["React Native"],
    "Android": ["Android"],
    "iOS": ["iOS"],

    # Cybersecurity and IT Infrastructure
    "Cybersecurity": ["Cybersecurity", "Cyber Security"],
    "Network Security": ["Network Security"],
    "Information Security": ["Information Security"],
    "Vulnerability Assessment": [
        "Vulnerability Assessment", "Vulnerability Management"
    ],
    "Penetration Testing": ["Penetration Testing"],
    "Digital Forensics": ["Digital Forensics"],
    "SIEM": ["SIEM"],
    "Wireshark": ["Wireshark"],
    "TCP/IP": ["TCP/IP"],
    "Active Directory": ["Active Directory"],
    "Microsoft 365": ["Microsoft 365", "Office 365"],
    "Microsoft Exchange": ["Microsoft Exchange"],
    "Microsoft Windows": ["Microsoft Windows", "Windows"],
    "PC Hardware": ["PC Hardware"],
    "Technical Support": ["Technical Support"],
    "Troubleshooting": ["Troubleshooting", "Troubleshoot"],
    "SharePoint": ["SharePoint"],

    # UI/UX Design
    "Figma": ["Figma"],
    "Adobe XD": ["Adobe XD"],
    "Photoshop": ["Photoshop"],
    "UI Design": ["UI Design", "User Interface Design"],
    "UX Design": ["UX Design", "User Experience Design"],
    "Wireframing": ["Wireframing", "Wireframes"],
    "Prototyping": ["Prototyping"],
    "User Research": ["User Research"],
    "Usability Testing": ["Usability Testing"],

    # Software Testing
    "Software Testing": ["Software Testing"],
    "Quality Assurance": ["Quality Assurance", "QA"],
    "Selenium": ["Selenium"],
    "Pytest": ["Pytest"],
    "JUnit": ["JUnit"],
    "Unit Testing": ["Unit Testing"],
    "Integration Testing": ["Integration Testing"],
    "Regression Testing": ["Regression Testing"],
    "Test Automation": ["Test Automation", "Automated Testing"],
    "Manual Testing": ["Manual Testing"],
    "Postman": ["Postman"],

    # Hardware, Embedded Systems and Robotics
    "Embedded Systems": ["Embedded Systems", "Embedded System"],
    "Firmware Development": ["Firmware Development"],
    "Arduino": ["Arduino"],
    "Raspberry Pi": ["Raspberry Pi"],
    "Robotics": ["Robotics"],
    "Circuit Design": ["Circuit Design"],
    "PCB Design": ["PCB Design"],
    "Servo Control": ["Servo Control", "Servo Feedback Control"],

    # Geographic Information Systems
    "GIS": ["GIS", "Geographic Information Systems"],
    "ArcGIS": ["ArcGIS"],
    "QGIS": ["QGIS"],

    # Product Management and Business Analysis
    "Agile": ["Agile"],
    "Scrum": ["Scrum"],
    "SAFe": ["SAFe"],
    "Jira": ["Jira"],
    "Product Management": ["Product Management"],
    "Business Analysis": ["Business Analysis"],
    "Requirements Gathering": ["Requirements Gathering"],

    # General Technical Skills
    "Programming": ["Programming"],
    "Software Development": ["Software Development"],
    "Data Structures": ["Data Structures"],
    "Algorithms": ["Algorithms"],
    "Object-Oriented Programming": [
        "Object-Oriented Programming", "OOP"
    ],

    # Soft Skills
    "Communication": ["Communication", "Communication Skills"],
    "Teamwork": ["Teamwork", "Team Environment"],
    "Collaboration": ["Collaboration", "Collaboratively"],
    "Problem-Solving": ["Problem-Solving", "Problem Solving"],
    "Analytical Skills": ["Analytical Skills"],
    "Time Management": ["Time Management"],
    "Adaptability": ["Adaptability"],
    "Leadership": ["Leadership"],
    "Attention to Detail": ["Attention to Detail"],
    "Customer Service": ["Customer Service"],
    "Willingness to Learn": [
        "Willingness to Learn", "Fast Learning", "Eager to Learn"
    ]
}
def extract_skills(text):
    if not text:
        return []

    matches = []
    occupied_spans = []

    aliases = [
        (skill, alias)
        for skill, skill_aliases in SKILL_ALIASES.items()
        for alias in skill_aliases
    ]

    # Match longer aliases first to prevent overlapping matches
    aliases.sort(key=lambda item: len(item[1]), reverse=True)

    for skill, alias in aliases:
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"

        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.span()

            overlaps = any(
                start < existing_end and end > existing_start
                for existing_start, existing_end in occupied_spans
            )

            if overlaps:
                continue

            occupied_spans.append((start, end))
            matches.append((start, skill))

    # Preserve the order in which skills appear in the text
    matches.sort(key=lambda item: item[0])

    # Remove duplicate standardized skills
    return list(dict.fromkeys(skill for _, skill in matches))