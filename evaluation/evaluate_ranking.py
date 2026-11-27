import json
from pathlib import Path
from itertools import combinations

from app.job_ranking_engine import rank_job_candidates


ROOT = Path(__file__).resolve().parents[1]
BASELINE_CORRECT = 38
BASELINE_PAIRS = 52


def load_json(path):
    with open(ROOT / path, encoding="utf-8-sig") as f:
        return json.load(f)


def main():

    jobs = {
        str(j["job_id"]): j
        for j in load_json("data/internships.json")
    }

    profiles = {
        p["profile_id"]: p["profile"]
        for p in load_json("evaluation/sample_profiles.json")
    }

    ground_truth = load_json(
        "evaluation/ground_truth.json"
    )

    judgments = ground_truth["judgments"]

    total_correct = 0
    total_incorrect = 0
    total_pairs = 0
    total_processed = 0
    total_mismatches = 0

    profile_results = []
    ranking_records = []
    ranking_errors = []

    print("\n========== REFINED RANKING EVALUATION ==========")

    for profile_id, profile in profiles.items():

        selected = [
            j for j in judgments
            if j["profile_id"] == profile_id
        ]

        if not selected:
            continue

        candidates = [
            {
                "job": jobs[str(j["job_id"])],
                "semantic_score": None,
                "best_matching_section": None,
                "matched_chunks": [],
                "best_query_type": None,
                "retrieval_evidence": [],
                "query_count": 0,
                "matched_query_types": []
            }
            for j in selected
        ]

        result = rank_job_candidates(
            profile,
            candidates,
            top_k=len(candidates),
            reference_year=ground_truth["reference_year"]
        )

        recommendations = result["recommendations"]

        lookup = {
            str(item["job_id"]): item
            for item in recommendations
        }

        expected_ids = {
            str(j["job_id"]) for j in selected
        }

        assert set(lookup) == expected_ids
        assert len(recommendations) == len(selected)

        total_processed += len(recommendations)

        correct = 0
        incorrect = 0

        print(f"\n========== PROFILE {profile_id} ==========")

        grades = {
            str(j["job_id"]): j["suitability_grade"]
            for j in selected
        }

        for item in recommendations:

            job_id = str(item["job_id"])
            grade = grades[job_id]

            mismatch = item[
                "mandatory_eligibility_mismatch"
            ]

            total_mismatches += int(mismatch)

            score = item["ranking_score"]

            score_text = (
                f"{score:.2f}"
                if score is not None
                else "N/A"
            )

            print(
                f"Rank {item['rank']} | "
                f"Grade {grade} | "
                f"Score {score_text} | "
                f"Mismatch {mismatch} | "
                f"{item['job_title']}"
            )

            ranking_records.append({
                "profile_id": profile_id,
                "job_id": job_id,
                "job_title": item["job_title"],
                "suitability_grade": grade,
                "rank": item["rank"],
                "ranking_score": score,
                "compatibility_score":
                    item["compatibility_score"],
                "mandatory_eligibility_mismatch":
                    mismatch
            })

        for first, second in combinations(selected, 2):

            first_grade = first["suitability_grade"]
            second_grade = second["suitability_grade"]

            if first_grade == second_grade:
                continue

            higher, lower = (
                (first, second)
                if first_grade > second_grade
                else (second, first)
            )

            higher_item = lookup[str(higher["job_id"])]
            lower_item = lookup[str(lower["job_id"])]

            if higher_item["rank"] < lower_item["rank"]:

                correct += 1

            else:

                incorrect += 1

                ranking_errors.append({
                    "profile_id": profile_id,
                    "expected_higher_job":
                        higher_item["job_title"],
                    "expected_higher_grade":
                        higher["suitability_grade"],
                    "actual_higher_job":
                        lower_item["job_title"],
                    "actual_higher_grade":
                        lower["suitability_grade"]
                })

        pairs = correct + incorrect

        accuracy = (
            correct / pairs * 100
            if pairs
            else None
        )

        total_correct += correct
        total_incorrect += incorrect
        total_pairs += pairs

        profile_results.append({
            "profile_id": profile_id,
            "processed_jobs": len(recommendations),
            "correct_pairs": correct,
            "incorrect_pairs": incorrect,
            "comparable_pairs": pairs,
            "pairwise_accuracy": accuracy
        })

        print(f"Correct pairs: {correct}/{pairs}")

        if accuracy is not None:
            print(f"Pairwise accuracy: {accuracy:.2f}%")
        else:
            print("Pairwise accuracy: N/A")

    assert total_processed == len(judgments)
    assert total_pairs == BASELINE_PAIRS

    baseline_accuracy = (
        BASELINE_CORRECT / BASELINE_PAIRS * 100
    )

    refined_accuracy = (
        total_correct / total_pairs * 100
    )

    improvement = (
        refined_accuracy - baseline_accuracy
    )

    print("\n========== REMAINING RANKING ERRORS ==========")

    for error in ranking_errors:

        print(
            f"{error['profile_id']} | "
            f"Expected higher: "
            f"{error['expected_higher_job']} "
            f"(grade {error['expected_higher_grade']}) | "
            f"Actually higher: "
            f"{error['actual_higher_job']} "
            f"(grade {error['actual_higher_grade']})"
        )

    print("\n========== FINAL EVALUATION SUMMARY ==========")

    print("Processed judgments:", total_processed)
    print("Comparable pairs:", total_pairs)
    print("Correct pairs:", total_correct)
    print("Incorrect pairs:", total_incorrect)
    print("Mandatory mismatches:", total_mismatches)

    print(f"Baseline accuracy: {baseline_accuracy:.2f}%")
    print(f"Refined accuracy: {refined_accuracy:.2f}%")
    print(f"Improvement: {improvement:+.2f} percentage points")

    report = {
        "evaluation_type":
            "matching_only_pairwise_ranking",
        "reference_year": ground_truth["reference_year"],
        "semantic_retrieval_used": False,
        "annotation_status":
            ground_truth["annotation_status"],
        "evaluation_scope":
            "Partial in-sample suitability judgments",
        "processed_judgments": total_processed,
        "comparable_pairs": total_pairs,
        "correct_pairs": total_correct,
        "incorrect_pairs": total_incorrect,
        "mandatory_mismatches": total_mismatches,
        "baseline_accuracy": baseline_accuracy,
        "refined_accuracy": refined_accuracy,
        "improvement_percentage_points": improvement,
        "profile_results": profile_results,
        "ranking_records": ranking_records,
        "ranking_errors": ranking_errors
    }

    output = ROOT / "evaluation/ranking_evaluation_results.json"

    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nResults saved:", output)
    print("Evaluation: COMPLETE")


if __name__ == "__main__":
    main()
