import json
from copy import deepcopy
from pathlib import Path

from app.job_resume_matcher import match_job_skills

from app.job_matching_refinement import (
    assess_technical_alignment,
    enrich_student_profile,
    refine_job_scoring,
)

from app.student_job_comparator import (
    compare_student_job,
)

from app.job_ranking_engine import (
    rank_job_candidates,
)


ROOT = Path(__file__).resolve().parents[1]

checks = []


def check(name, condition):

    checks.append(bool(condition))

    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
    )


def assess(
    student_skills,
    required=None,
    preferred=None,
    qualifications=None,
):

    profile = {
        "skills": student_skills
    }

    job = {
        "required_skills": required or [],
        "preferred_skills": preferred or [],
        "qualifications": qualifications or [],
    }

    result = match_job_skills(profile, job)

    comparison = {
        "components": {
            "required_skills": result["required_skills"],
            "preferred_skills": result["preferred_skills"],
        }
    }

    return assess_technical_alignment(comparison)


print("\n========== REQUIRED TECHNICAL ALIGNMENT ==========")

result = assess(
    ["Python"],
    required=["Python", "SQL"]
)

check(
    "Required technical match receives full factor",
    result["ranking_factor"] == 1.0
)

check(
    "Partial technical match ratio calculated correctly",
    result["required_technical_alignment"]["match_ratio"]
    == 0.5
)

result = assess(
    ["Communication"],
    required=["Python", "Communication"]
)

check(
    "Soft skill does not satisfy technical requirement",
    result["required_technical_alignment"][
        "matched_requirements"
    ] == 0
)

check(
    "Zero required technical matches reduce ranking factor",
    result["ranking_factor"] == 0.5
)

check(
    "Missing technical evidence explicitly identified",
    result["alignment_status"]
    == "no_required_technical_match"
)

result = assess(
    ["Python", "SQL"],
    required=["Python", "SQL"]
)

check(
    "Complete technical alignment calculated correctly",
    result["required_technical_alignment"]["match_ratio"]
    == 1.0
)


print("\n========== PREFERRED TECHNICAL ALIGNMENT ==========")

result = assess(
    ["Python"],
    required=["Communication"],
    preferred=["Python"]
)

check(
    "Preferred technical match receives 0.75 factor",
    result["ranking_factor"] == 0.75
)

check(
    "Preferred technical alignment status correct",
    result["alignment_status"]
    == "preferred_technical_evidence_available"
)

result = assess(
    ["Communication"],
    preferred=["Python"]
)

check(
    "Unmatched preferred technical skill receives 0.5 factor",
    result["ranking_factor"] == 0.5
)

check(
    "Unmatched preferred technical status correct",
    result["alignment_status"]
    == "no_preferred_technical_match"
)

result = assess(
    ["Python"],
    required=["Java"],
    preferred=["Python"]
)

check(
    "Preferred match does not override missing required match",
    result["ranking_factor"] == 0.5
)


print("\n========== MISSING REQUIREMENT INFORMATION ==========")

result = assess(
    ["Communication"],
    required=["Communication"]
)

check(
    "Soft-only requirements identified as insufficient",
    result["alignment_status"]
    == "technical_requirements_unavailable"
)

check(
    "Unavailable technical requirements have no match ratio",
    result["required_technical_alignment"]["match_ratio"]
    is None
)

result = assess([])

check(
    "Empty requirements handled safely",
    result["ranking_factor"] == 0.5
    and result["required_technical_alignment"][
        "total_requirements"
    ] == 0
)


print("\n========== TECHNICAL ALTERNATIVE REQUIREMENTS ==========")

for skills, expected, name in [
    (["Linux"], 1, "Linux alone satisfies alternative"),
    (["Microsoft Windows"], 1, "Windows alone satisfies alternative"),
    (["Linux", "Microsoft Windows"], 1, "Both options counted once"),
    (["Communication"], 0, "Unrelated skill cannot satisfy alternative"),
]:

    result = assess(
        skills,
        required=["Linux", "Microsoft Windows"],
        qualifications=[
            "Must be experienced with Linux or Windows operating systems."
        ]
    )

    alignment = result["required_technical_alignment"]

    check(
        name,
        alignment["total_requirements"] == 1
        and alignment["matched_requirements"] == expected
    )


print("\n========== CONTEXTUAL REQUIREMENT INTEGRATION ==========")

result = assess(
    ["Linux"],
    required=["Linux", "CCNA"],
    qualifications=[
        "Willing to work towards industry certifications such as CCNA."
    ]
)

check(
    "Future certification excluded from technical assessment",
    "CCNA" not in result["technical_required_skills"]
)

check(
    "Remaining technical requirement correctly evaluated",
    result["required_technical_alignment"]["match_ratio"]
    == 1.0
)

result = assess(
    ["Programming"],
    required=["Scripting"],
    qualifications=[
        "Must have at least one programming or scripting language."
    ]
)

check(
    "Contextual programming alternative counted once",
    result["required_technical_alignment"][
        "total_requirements"
    ] == 1
)

check(
    "Contextual programming alternative satisfied",
    result["required_technical_alignment"][
        "matched_requirements"
    ] == 1
)


print("\n========== SCORING PRESERVATION ==========")

scoring = {
    "compatibility_score": 80.0,
    "ranking_score": 60.0,
    "eligibility_review": [],
}

original_scoring = deepcopy(scoring)

job = {
    "required_skills": ["Python", "Communication"],
    "preferred_skills": [],
}

skill_result = match_job_skills(
    {"skills": ["Communication"]},
    job
)

comparison = {
    "components": {
        "required_skills": skill_result["required_skills"],
        "preferred_skills": skill_result["preferred_skills"],
    }
}

refined = refine_job_scoring(
    scoring,
    job,
    comparison=comparison
)

check(
    "Original scoring object unchanged",
    scoring == original_scoring
)

check(
    "Compatibility score preserved",
    refined["compatibility_score"] == 80.0
)

check(
    "Base ranking score preserved",
    refined["base_ranking_score"] == 60.0
)

check(
    "Technical factor correctly applied",
    refined["ranking_score"] == 30.0
)


print("\n========== ACTUAL INTERNSHIP REGRESSION ==========")

with open(
    ROOT / "data/internships.json",
    encoding="utf-8-sig"
) as f:
    jobs = json.load(f)

with open(
    ROOT / "evaluation/sample_profiles.json",
    encoding="utf-8-sig"
) as f:
    profiles = json.load(f)


def get_profile(profile_id):

    return next(
        item["profile"]
        for item in profiles
        if item["profile_id"] == profile_id
    )


def get_job(title, company):

    return next(
        job for job in jobs
        if title.lower() in job["job_title"].lower()
        and company.lower() in job["company"].lower()
    )


targets = [
    (
        "P01",
        "Intern, Computer Architecture Engineer",
        "Sunlune",
        0.5,
        "technical_requirements_unavailable"
    ),
    (
        "P08",
        "Intern, Computer Architecture Engineer",
        "Sunlune",
        0.5,
        "technical_requirements_unavailable"
    ),
    (
        "P04",
        "UI/UX Designer",
        "Aayats",
        0.5,
        "no_required_technical_match"
    ),
    (
        "P04",
        "Full Stack Software Engineer Intern",
        "ByteDance",
        0.5,
        "no_required_technical_match"
    ),
    (
        "P05",
        "SOC Analyst Internship",
        "360 SOC",
        1.0,
        "required_technical_evidence_available"
    ),
]

for (
    profile_id,
    title,
    company,
    expected_factor,
    expected_status,
) in targets:

    profile = get_profile(profile_id)
    job = get_job(title, company)

    original_profile = deepcopy(profile)
    original_job = deepcopy(job)

    candidate = {
        "job_id": job["job_id"],
        "job": job,
        "semantic_score": None,
        "best_matching_section": None,
        "matched_chunks": [],
        "best_query_type": None,
        "retrieval_evidence": [],
        "query_count": 0,
        "matched_query_types": [],
    }

    ranking = rank_job_candidates(
        profile,
        [candidate],
        top_k=1,
        reference_year=2026
    )

    item = ranking["recommendations"][0]

    technical = item["technical_assessment"]

    print(
        f"\n{profile_id} | {company}"
        f"\nBase score: {item['base_ranking_score']:.2f}"
        f"\nRanking score: {item['ranking_score']:.2f}"
        f"\nFactor: {technical['ranking_factor']}"
        f"\nStatus: {technical['alignment_status']}"
    )

    check(
        f"{profile_id} {company}: expected technical factor",
        technical["ranking_factor"] == expected_factor
    )

    check(
        f"{profile_id} {company}: expected alignment status",
        technical["alignment_status"] == expected_status
    )

    check(
        f"{profile_id} {company}: original inputs unchanged",
        profile == original_profile
        and job == original_job
    )


print("\n========== SOC EVIDENCE PROPAGATION ==========")

soc_profile = enrich_student_profile(
    get_profile("P05")
)

soc_job = get_job(
    "SOC Analyst Internship",
    "360 SOC"
)

comparison = compare_student_job(
    soc_profile,
    soc_job,
    reference_year=2026
)

check(
    "Contextual adjustments preserved in comparison",
    len(comparison["requirement_adjustments"]) == 3
)

technical = assess_technical_alignment(comparison)

check(
    "Future CCNA excluded from effective technical skills",
    "CCNA" not in technical["technical_required_skills"]
)

check(
    "Future Security+ excluded from effective technical skills",
    "CompTIA Security+"
    not in technical["technical_required_skills"]
)

check(
    "Programming evidence preserved in technical alignment",
    "Programming"
    in technical["required_technical_alignment"]["matched_skills"]
)

check(
    "SOC technical requirement count correct",
    technical["required_technical_alignment"][
        "total_requirements"
    ] == 9
)

check(
    "SOC matched technical requirement count correct",
    technical["required_technical_alignment"][
        "matched_requirements"
    ] == 3
)


print("\n========== FINAL SUMMARY ==========")

print(f"Passed: {sum(checks)}/{len(checks)}")
print(f"Failed: {len(checks) - sum(checks)}")

raise SystemExit(0 if all(checks) else 1)
