import json

from copy import deepcopy
from pathlib import Path

from app.job_ranking_engine import rank_job_candidates

from app.job_recommendation_explainer import (
    generate_recommendation_explanation,
    attach_recommendation_explanations,
)


ROOT = Path(__file__).resolve().parents[1]

checks = []


def check(name, condition):

    checks.append(bool(condition))

    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
    )


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


def get_ranked_item(profile_id, title, company):

    profile = get_profile(profile_id)
    job = get_job(title, company)

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

    result = rank_job_candidates(
        profile,
        [candidate],
        top_k=1,
        reference_year=2026
    )

    return result["recommendations"][0]


def warning_types(explanation):

    return {
        warning["type"]
        for warning in explanation["warnings"]
    }


print("\n========== SOC CONTEXTUAL EXPLANATIONS ==========")

soc = get_ranked_item(
    "P05",
    "SOC Analyst Internship",
    "360 SOC"
)

original_soc = deepcopy(soc)

explanation = generate_recommendation_explanation(soc)

notes = explanation["requirement_notes"]

certification_notes = {
    note["skill"]
    for note in notes
    if note["type"] == "future_certification"
}

alternative_notes = [
    note for note in notes
    if note["type"] == "alternative_requirement"
]

check(
    "Original recommendation unchanged",
    soc == original_soc
)

check(
    "Future CCNA explained",
    "CCNA" in certification_notes
)

check(
    "Future Security+ explained",
    "CompTIA Security+" in certification_notes
)

check(
    "Linux or Windows alternative explained",
    any(
        {"Linux", "Microsoft Windows"}
        == set(note["skills"])
        and note["satisfied"]
        and "Linux" in note["matched_options"]
        for note in alternative_notes
    )
)

check(
    "Programming or Scripting alternative explained",
    any(
        {"Programming", "Scripting"}
        == set(note["skills"])
        and note["satisfied"]
        and "Programming" in note["matched_options"]
        for note in alternative_notes
    )
)

check(
    "All contextual adjustments preserved",
    len(explanation["requirement_adjustments"]) == 3
)

check(
    "SOC does not receive zero technical match warning",
    "no_required_technical_match"
    not in warning_types(explanation)
)

check(
    "SOC technical alignment status correct",
    explanation["score_explanation"][
        "technical_alignment_status"
    ] == "required_technical_evidence_available"
)

check(
    "SOC technical evidence factor correct",
    explanation["score_explanation"][
        "technical_evidence_factor"
    ] == 1.0
)

check(
    "SOC technical requirement counts preserved",
    explanation["score_explanation"][
        "required_technical_alignment"
    ]["matched_requirements"] == 3
    and explanation["score_explanation"][
        "required_technical_alignment"
    ]["total_requirements"] == 9
)

missing_skills = [
    skill
    for gap in explanation["skill_gaps"]
    for skill in gap.get("skills", [])
]

check(
    "Future certifications absent from skill gaps",
    "CCNA" not in missing_skills
    and "CompTIA Security+" not in missing_skills
)

print("\nSOC requirement notes:")

for note in notes:
    print("-", note["message"])


print("\n========== ZERO TECHNICAL MATCH EXPLANATIONS ==========")

aayats = get_ranked_item(
    "P04",
    "UI/UX Designer",
    "Aayats"
)

explanation = generate_recommendation_explanation(aayats)

check(
    "Missing technical evidence warning present",
    "no_required_technical_match"
    in warning_types(explanation)
)

check(
    "Missing evidence distinguished from missing requirements",
    "insufficient_technical_information"
    not in warning_types(explanation)
)

check(
    "Unmatched design tool alternative explained",
    any(
        note["type"] == "alternative_requirement"
        and {"Adobe XD", "Figma"}.issubset(
            set(note["skills"])
        )
        and not note["satisfied"]
        for note in explanation["requirement_notes"]
    )
)

check(
    "Technical ranking factor is 0.5",
    explanation["score_explanation"][
        "technical_evidence_factor"
    ] == 0.5
)

check(
    "Summary contains actual ranking adjustment reason",
    aayats["technical_assessment"]["reason"]
    in explanation["summary"]
)

check(
    "Old misleading adjustment reason absent",
    "technical requirement information is limited"
    not in explanation["summary"]
)

print("\nAayats summary:")
print(explanation["summary"])


print("\n========== UNAVAILABLE TECHNICAL REQUIREMENTS ==========")

sunlune = get_ranked_item(
    "P08",
    "Intern, Computer Architecture Engineer",
    "Sunlune"
)

explanation = generate_recommendation_explanation(sunlune)

check(
    "Unavailable technical requirements warning present",
    "insufficient_technical_information"
    in warning_types(explanation)
)

check(
    "Unavailable requirements not confused with failed match",
    "no_required_technical_match"
    not in warning_types(explanation)
)

check(
    "Unavailable alignment status preserved",
    explanation["score_explanation"][
        "technical_alignment_status"
    ] == "technical_requirements_unavailable"
)

check(
    "Unavailable technical match ratio remains unknown",
    explanation["score_explanation"][
        "required_technical_alignment"
    ]["match_ratio"] is None
)

check(
    "Summary explains unavailable technical evidence",
    sunlune["technical_assessment"]["reason"]
    in explanation["summary"]
)

print("\nSunlune summary:")
print(explanation["summary"])


print("\n========== MANDATORY EDUCATION MISMATCH ==========")

instacart = get_ranked_item(
    "P01",
    "Machine Learning Engineer, PhD Intern",
    "Instacart"
)

explanation = generate_recommendation_explanation(instacart)

check(
    "Mandatory mismatch flag preserved",
    explanation["mandatory_eligibility_mismatch"] is True
)

check(
    "Explicit mandatory education warning present",
    "mandatory_eligibility_mismatch"
    in warning_types(explanation)
)

check(
    "Mismatched education not presented as strength",
    not any(
        strength["component"] == "education"
        for strength in explanation["strengths"]
    )
)

check(
    "Mandatory degree verification prioritized",
    "mandatory degree requirement"
    in explanation["improvement_priorities"][0]["action"]
)

check(
    "Eligibility-based deprioritization explained",
    "deprioritized" in explanation["summary"]
)

check(
    "Mandatory mismatch preserved in score explanation",
    explanation["score_explanation"][
        "mandatory_eligibility_mismatch"
    ] is True
)

check(
    "Eligibility ranking policy exposed",
    "deprioritized" in explanation[
        "score_explanation"
    ]["ranking_policy"]
)

print("\nInstacart summary:")
print(explanation["summary"])


print("\n========== SCORE AND RESPONSE CONSISTENCY ==========")

for name, item in [
    ("SOC", soc),
    ("Aayats", aayats),
    ("Sunlune", sunlune),
    ("Instacart", instacart),
]:

    explanation = generate_recommendation_explanation(item)

    score = explanation["score_explanation"]

    check(
        f"{name}: all numeric scores preserved",
        all(
            score[key] == item[key]
            for key in [
                "compatibility_score",
                "base_ranking_score",
                "ranking_score",
                "evidence_coverage",
                "semantic_score",
            ]
        )
    )

    check(
        f"{name}: existing explanation fields preserved",
        {
            "job_id",
            "rank",
            "summary",
            "strengths",
            "skill_gaps",
            "improvement_priorities",
            "warnings",
            "eligibility_review_required",
            "eligibility_reviews",
            "score_explanation",
        }.issubset(explanation)
    )

    check(
        f"{name}: score breakdown preserved",
        score["score_breakdown"]
        == item["score_breakdown"]
    )

    check(
        f"{name}: explanation JSON serializable",
        bool(json.dumps(explanation))
    )


print("\n========== EXPLANATION ATTACHMENT INTEGRATION ==========")

result = {
    "recommendations": [
        soc,
        aayats,
        sunlune,
        instacart,
    ]
}

original_result = deepcopy(result)

explained = attach_recommendation_explanations(result)

check(
    "Original ranking result unchanged",
    result == original_result
)

check(
    "Explanation attached to every recommendation",
    all(
        "explanation" in item
        for item in explained["recommendations"]
    )
)

check(
    "Recommendation order preserved",
    [
        item["job_id"]
        for item in explained["recommendations"]
    ] == [
        item["job_id"]
        for item in result["recommendations"]
    ]
)

check(
    "Original ranking fields preserved",
    all(
        {
            key: value
            for key, value in updated.items()
            if key != "explanation"
        } == original
        for updated, original in zip(
            explained["recommendations"],
            result["recommendations"]
        )
    )
)


print("\n========== FINAL SUMMARY ==========")

print(f"Passed: {sum(checks)}/{len(checks)}")
print(f"Failed: {len(checks) - sum(checks)}")

raise SystemExit(0 if all(checks) else 1)
