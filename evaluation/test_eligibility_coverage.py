import json

from copy import deepcopy
from pathlib import Path

from app.job_matching_refinement import (
    detect_additional_eligibility,
)

from app.job_ranking_engine import (
    rank_job_candidates,
)

from app.job_recommendation_explainer import (
    generate_recommendation_explanation,
)


ROOT = Path(__file__).resolve().parents[1]

checks = []


def check(name, condition):

    checks.append(bool(condition))

    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
    )


def load(path):

    return json.loads(
        (ROOT / path).read_text(
            encoding="utf-8-sig"
        )
    )


def constraints(reviews):

    return {
        constraint
        for review in reviews
        for constraint in review["constraints"]
    }


def main():

    print(
        "\n========== ELIGIBILITY COVERAGE REGRESSION =========="
    )

    print("\n========== RESPONSIBILITIES DETECTION ==========")

    reviews = detect_additional_eligibility({
        "responsibilities": [
            "RequirementsUS Work Authorization"
        ]
    })

    check(
        "Merged work authorization requirement detected",
        "work_authorization_mention"
        in constraints(reviews),
    )

    check(
        "Eligibility remains unknown pending verification",
        bool(reviews)
        and all(
            item["status"] == "unknown"
            for item in reviews
        ),
    )

    check(
        "Original matched evidence preserved",
        any(
            "Work Authorization" in item["evidence"]
            for item in reviews
        ),
    )

    reviews = detect_additional_eligibility({
        "responsibilities":
            "Candidates must be authorized to work."
    })

    check(
        "String responsibilities supported",
        "work_authorization_mention"
        in constraints(reviews),
    )

    print("\n========== EXISTING DETECTION ==========")

    existing_cases = [
        (
            "qualifications",
            "Must be a US citizen",
            "citizenship_requirement",
        ),
        (
            "education_requirements",
            "US citizenship is required",
            "citizenship_requirement",
        ),
        (
            "experience_requirements",
            "Active security clearance required",
            "security_clearance_mention",
        ),
        (
            "job_description",
            "Visa sponsorship is unavailable",
            "work_authorization_mention",
        ),
        (
            "responsibilities",
            "Security clearance required",
            "security_clearance_mention",
        ),
        (
            "responsibilities",
            "US citizenship is required",
            "citizenship_requirement",
        ),
    ]

    for field, text, expected in existing_cases:

        reviews = detect_additional_eligibility({
            field: text
        })

        check(
            f"{field}: {expected}",
            expected in constraints(reviews),
        )

    print("\n========== DUPLICATE EVIDENCE ==========")

    reviews = detect_additional_eligibility({
        "qualifications": [
            "Work Authorization"
        ],
        "responsibilities": [
            "Work Authorization",
            "Work Authorization",
        ],
        "job_description":
            "Work Authorization",
    })

    check(
        "One review per constraint",
        len(reviews) == 1,
    )

    check(
        "Duplicate evidence removed",
        len(reviews) == 1
        and len(reviews[0]["evidence"]) == 1,
    )

    print("\n========== NEGATIVE CONTROLS ==========")

    negative_cases = [
        {},
        {"responsibilities": None},
        {"responsibilities": []},
        {"responsibilities": ""},
        {
            "responsibilities": [
                "Develop Python applications",
                "Collaborate with team members",
            ]
        },
        {
            "responsibilities": [
                None,
                123,
                {},
                "Build software applications",
            ]
        },
    ]

    for index, job in enumerate(
        negative_cases, 1
    ):

        check(
            f"Negative control {index}",
            detect_additional_eligibility(job) == [],
        )

    print("\n========== REAL DATASET INTEGRATION ==========")

    diagnostic = load(
        "evaluation/end_to_end_component_diagnostic.json"
    )

    selected = [
        record
        for record in diagnostic["records"]
        if record["job_id"] == "3902351469"
        and record["profile_id"] in {"P02", "P07"}
    ]

    check(
        "Both TuneTunnel diagnostic cases available",
        len(selected) == 2
        and {
            record["profile_id"]
            for record in selected
        } == {"P02", "P07"},
    )

    for record in selected:

        pid = record["profile_id"]

        print(f"\n========== {pid} | TUNETUNNEL ==========")

        profile = record["profile"]
        job = record["job"]

        original_profile = deepcopy(profile)
        original_job = deepcopy(job)

        old = record["ranking_result"]

        candidate = {
            "job_id": record["job_id"],
            "job": job,
            "semantic_score": old["semantic_score"],
            "best_matching_section": None,
            "matched_chunks": [],
            "best_query_type": None,
            "retrieval_evidence": [],
            "query_count": None,
            "matched_query_types": [],
        }

        result = rank_job_candidates(
            profile,
            [candidate],
            top_k=1,
            reference_year=2026,
        )

        item = result["recommendations"][0]

        check(
            f"{pid}: Previously missed review confirmed",
            old["eligibility_review_required"] is False,
        )

        check(
            f"{pid}: Eligibility review now required",
            item["eligibility_review_required"] is True,
        )

        check(
            f"{pid}: Work authorization constraint present",
            "work_authorization_mention"
            in constraints(item["eligibility_review"]),
        )

        check(
            f"{pid}: No automatic mandatory mismatch",
            item["mandatory_eligibility_mismatch"] is False,
        )

        for field in [
            "compatibility_score",
            "base_ranking_score",
            "ranking_score",
            "evidence_coverage",
        ]:

            check(
                f"{pid}: {field} unchanged",
                item[field] == old[field],
            )

        explanation = (
            generate_recommendation_explanation(item)
        )

        check(
            f"{pid}: Explanation requires eligibility review",
            explanation["eligibility_review_required"]
            is True,
        )

        check(
            f"{pid}: Explanation contains authorization constraint",
            "work_authorization_mention"
            in constraints(
                explanation["eligibility_reviews"]
            ),
        )

        check(
            f"{pid}: Student profile unchanged",
            profile == original_profile,
        )

        check(
            f"{pid}: Job data unchanged",
            job == original_job,
        )

        print(
            "Previous eligibility review:",
            old["eligibility_review_required"],
        )

        print(
            "Updated eligibility review:",
            item["eligibility_review_required"],
        )

        print(
            "Ranking score:",
            item["ranking_score"],
        )

    print("\n========== FULL DATASET SMOKE TEST ==========")

    jobs = load("data/internships.json")

    processed = 0
    flagged = 0
    errors = []

    for job in jobs:

        try:

            reviews = detect_additional_eligibility(job)

            if reviews:
                flagged += 1

            processed += 1

        except Exception as exc:

            errors.append({
                "job_id": job.get("job_id"),
                "error": str(exc),
            })

    check(
        "All 150 internships processed",
        processed == len(jobs) == 150,
    )

    check(
        "No eligibility detection errors",
        not errors,
    )

    print("Internships processed:", processed)
    print("Internships requiring additional review:", flagged)
    print("Detection errors:", len(errors))

    print("\n========== FINAL SUMMARY ==========")

    passed = sum(checks)

    print(f"Checks passed: {passed}/{len(checks)}")
    print("Dataset size:", len(jobs))
    print("Gemini API requests: 0")

    assert all(checks), "Eligibility regression failed"

    print("Eligibility coverage regression: COMPLETE")


if __name__ == "__main__":
    main()
