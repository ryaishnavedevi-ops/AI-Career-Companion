import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent / "sample_profiles.json"


def make_education(qualification):
    return {
        "qualification": qualification,
        "dates": "August 2023 - May 2027",
        "institution": "Synthetic Evaluation University",
        "result": "",
    }


def make_project(title, category, technologies, description):
    return {
        "title": title,
        "category": category,
        "technologies": technologies,
        "description": description,
        "link": "",
    }


def make_experience(role, responsibilities):
    return {
        "company": "Synthetic Evaluation Organization",
        "details": "June 2026 - August 2026",
        "role": role,
        "duration": "2 Months",
        "responsibilities": responsibilities,
    }


def make_profile(
    profile_id,
    name,
    level,
    skills,
    expected_domains,
    education=None,
    projects=None,
    experience=None,
    notes="",
):
    education = education or []
    projects = projects or []
    experience = experience or []

    skills = list(dict.fromkeys(skills))

    skill_records = [
        {
            "category": "Evaluation Skills",
            "skills": skills.copy(),
        }
    ] if skills else []

    skill_evidence = []

    for skill in skills:
        sources = [
            {
                "source": "explicit_skill",
                "detail": "Evaluation Skills",
            }
        ]

        for project in projects:
            technologies = project.get("technologies", [])

            if skill.casefold() in {
                technology.casefold()
                for technology in technologies
            }:
                sources.append({
                    "source": "project_technology",
                    "detail": project["title"],
                })

        skill_evidence.append({
            "skill": skill,
            "sources": sources,
        })

    return {
        "profile_id": profile_id,
        "profile_name": name,
        "competency_level": level,
        "expected_domains": expected_domains,
        "evaluation_notes": notes,
        "profile": {
            "candidate_id": f"evaluation-candidate-{profile_id}",
            "resume_id": f"evaluation-resume-{profile_id}",
            "professional_summary": name,
            "location": None,
            "skills": skills.copy(),
            "explicit_skills": skills.copy(),
            "inferred_skills": [],
            "skill_records": skill_records,
            "skill_evidence": skill_evidence,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": [],
            "awards": [],
            "languages": [],
            "profile_statistics": {
                "total_skills": len(skills),
                "explicit_skills": len(skills),
                "inferred_skills": 0,
                "education_records": len(education),
                "experience_records": len(experience),
                "projects": len(projects),
                "certifications": 0,
                "awards": 0,
            },
        },
    }


def create_profiles():
    return [
        make_profile(
            "P01",
            "AI and Machine Learning Student",
            "strong",
            [
                "Python", "Machine Learning",
                "Artificial Intelligence", "TensorFlow",
                "Scikit-learn", "Pandas", "NumPy",
                "Statistics", "Data Analysis",
                "Communication", "Problem-Solving",
            ],
            [
                "Artificial Intelligence and Machine Learning",
                "Data Science",
            ],
            education=[
                make_education(
                    "Bachelor of Science in Computer Science "
                    "(Artificial Intelligence and Machine Learning)"
                )
            ],
            projects=[
                make_project(
                    "Machine Learning Classification System",
                    "Academic Project",
                    ["Python", "Scikit-learn", "Pandas", "NumPy"],
                    [
                        "Performed data preprocessing.",
                        "Trained classification models.",
                        "Evaluated machine learning models.",
                        "Analyzed prediction performance.",
                    ],
                ),
                make_project(
                    "Image Classification Application",
                    "Academic Project",
                    ["Python", "TensorFlow"],
                    [
                        "Trained image classification models.",
                        "Evaluated model performance.",
                        "Developed a classification application.",
                    ],
                ),
            ],
            notes="Specialized hardware or advanced research requirements may remain unmatched.",
        ),

        make_profile(
            "P02",
            "Frontend Development Student",
            "strong",
            [
                "HTML", "CSS", "JavaScript", "React",
                "Git", "REST APIs", "Communication",
                "Problem-Solving",
            ],
            [
                "Frontend Development",
                "Web Development",
                "Full Stack Development",
                "Software Development",
            ],
            education=[
                make_education(
                    "Bachelor of Science in Computer Science"
                )
            ],
            projects=[
                make_project(
                    "React Web Dashboard",
                    "Frontend Development",
                    ["HTML", "CSS", "JavaScript", "React", "REST APIs"],
                    [
                        "Developed a responsive web application.",
                        "Implemented user interface components.",
                        "Integrated REST APIs.",
                        "Performed software testing and debugging.",
                    ],
                )
            ],
            experience=[
                make_experience(
                    "Frontend Developer Intern",
                    [
                        "Developed React user interfaces.",
                        "Implemented responsive web pages.",
                        "Integrated REST APIs.",
                    ],
                )
            ],
            notes="Relevant frontend roles may appear under broader software development domains.",
        ),

        make_profile(
            "P03",
            "Data Analytics Student",
            "strong",
            [
                "Python", "SQL", "Microsoft Excel",
                "Power BI", "Pandas", "Data Analysis",
                "Data Visualization", "Statistics",
                "Analytical Skills", "Communication",
            ],
            [
                "Data Analytics",
                "Data Science",
                "IT Business Analysis",
            ],
            education=[
                make_education(
                    "Bachelor of Science in Data Analytics"
                )
            ],
            projects=[
                make_project(
                    "Sales Analytics Dashboard",
                    "Data Analytics",
                    ["Python", "SQL", "Pandas", "Microsoft Excel", "Power BI"],
                    [
                        "Performed data cleaning and preprocessing.",
                        "Conducted exploratory data analysis.",
                        "Created data visualizations.",
                        "Developed business analytics dashboards.",
                    ],
                )
            ],
            notes="Expected analytics relevance, but not advanced machine learning suitability.",
        ),

        make_profile(
            "P04",
            "Software Engineering Student",
            "intermediate",
            [
                "Java", "Python", "Programming",
                "Object-Oriented Programming",
                "Data Structures", "Algorithms",
                "Git", "REST APIs", "Problem-Solving",
                "Teamwork",
            ],
            [
                "Software Development",
                "Full Stack Development",
            ],
            education=[
                make_education(
                    "Bachelor of Engineering in Software Engineering"
                )
            ],
            projects=[
                make_project(
                    "Library Management Application",
                    "Software Development",
                    ["Java", "Git", "REST APIs"],
                    [
                        "Developed a software application.",
                        "Implemented backend application logic.",
                        "Integrated REST APIs.",
                        "Performed software testing and debugging.",
                    ],
                )
            ],
            notes="Expected general software development matches. No professional experience is claimed.",
        ),

        make_profile(
            "P05",
            "Cybersecurity Student",
            "intermediate",
            [
                "Cybersecurity", "Linux", "Networking",
                "Python", "Wireshark", "Incident Response",
                "Problem-Solving", "Attention to Detail",
            ],
            [
                "Cybersecurity",
                "Networking and IT Infrastructure",
                "Information Technology",
            ],
            education=[
                make_education(
                    "Bachelor of Science in Cybersecurity"
                )
            ],
            projects=[
                make_project(
                    "Network Security Monitoring Lab",
                    "Cybersecurity",
                    ["Linux", "Wireshark", "Python"],
                    [
                        "Performed network security monitoring.",
                        "Analyzed network traffic.",
                        "Conducted vulnerability assessments.",
                        "Practiced incident response procedures.",
                    ],
                )
            ],
            notes="Security clearance and citizenship are unknown.",
        ),

        make_profile(
            "P06",
            "UI UX Design Student",
            "strong",
            [
                "Figma", "Prototyping", "Wireframing",
                "User Research", "UI Design", "UX Design",
                "Communication", "Collaboration",
            ],
            ["UI/UX Design"],
            education=[
                make_education(
                    "Bachelor of Design in Interaction Design"
                )
            ],
            projects=[
                make_project(
                    "Mobile User Experience Design",
                    "UI/UX Design",
                    ["Figma", "Prototyping", "Wireframing"],
                    [
                        "Conducted user research.",
                        "Created interface wireframes.",
                        "Developed interactive prototypes.",
                        "Designed user interfaces.",
                    ],
                )
            ],
            notes="Expected UI/UX matches rather than programming-intensive development roles.",
        ),

        make_profile(
            "P07",
            "Beginner Programming Student",
            "beginner",
            [
                "Python", "HTML", "CSS",
                "Communication", "Willingness to Learn",
            ],
            [
                "Software Development",
                "Web Development",
                "Information Technology",
            ],
            education=[
                make_education(
                    "Bachelor of Science in Computer Science"
                )
            ],
            notes="Limited skills and no project or experience evidence. Strong compatibility is not assumed.",
        ),

        make_profile(
            "P08",
            "Unrelated Skills Student",
            "negative_control",
            [
                "Communication", "Teamwork",
                "Microsoft Word", "Customer Service",
                "Event Planning",
            ],
            [],
            education=[
                make_education(
                    "Bachelor of Arts in English Literature"
                )
            ],
            notes="Tests soft-skill dominance and misleading technical recommendations. Suitable individual roles require manual review.",
        ),

        make_profile(
            "P09",
            "Empty Evaluation Profile",
            "boundary_test",
            [],
            [],
            notes="Expected query generation to reject insufficient career-related information.",
        ),
    ]


def validate_profiles(profiles):
    assert len(profiles) == 9

    ids = [item["profile_id"] for item in profiles]
    assert len(ids) == len(set(ids))

    candidate_ids = set()
    resume_ids = set()

    for item in profiles:
        profile = item["profile"]
        skills = profile["skills"]

        assert profile["candidate_id"] not in candidate_ids
        assert profile["resume_id"] not in resume_ids

        candidate_ids.add(profile["candidate_id"])
        resume_ids.add(profile["resume_id"])

        assert len(skills) == len({
            skill.casefold() for skill in skills
        })

        assert profile["explicit_skills"] == skills
        assert profile["inferred_skills"] == []

        evidence_skills = [
            record["skill"]
            for record in profile["skill_evidence"]
        ]

        assert evidence_skills == skills

        for record in profile["skill_evidence"]:
            assert record["sources"]

        stats = profile["profile_statistics"]

        assert stats["total_skills"] == len(skills)
        assert stats["explicit_skills"] == len(skills)
        assert stats["inferred_skills"] == 0
        assert stats["projects"] == len(profile["projects"])
        assert stats["education_records"] == len(profile["education"])
        assert stats["experience_records"] == len(profile["experience"])

        print(
            f"{item['profile_id']} | "
            f"{item['profile_name']} | "
            f"Skills: {len(skills)} | "
            f"Projects: {len(profile['projects'])} | "
            f"Experience: {len(profile['experience'])} | PASS"
        )

    print("\nAll 9 profile structures validated.")


def main():
    profiles = create_profiles()

    print("========== PROFILE VALIDATION ==========")
    validate_profiles(profiles)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=4, ensure_ascii=False)

    print("\n========== OUTPUT ==========")
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Total profiles: {len(profiles)}")
    print("Substantive profiles: 8")
    print("Boundary profiles: 1")
    print("Synthetic profile generation completed.")


if __name__ == "__main__":
    main()
