import json
import time

from itertools import combinations
from pathlib import Path

from app.job_ranking_engine import rank_job_candidates


ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = (
    ROOT / "evaluation/end_to_end_offline_results.json"
)

DEPTHS = [10, 15, 20, 30, 40]

CUTOFFS = [5, 10, 20, 40]


def load(relative_path):

    return json.loads(
        (ROOT / relative_path).read_text(
            encoding="utf-8-sig"
        )
    )


def ratio(numerator, denominator):

    return (
        numerator / denominator
        if denominator
        else None
    )


def percentage(value):

    return (
        f"{value:.2%}"
        if value is not None
        else "Undefined"
    )


def main():

    experiment = load(
        "evaluation/retrieval_depth_experiment.json"
    )

    ground_truth = load(
        "evaluation/ground_truth.json"
    )

    jobs = {
        job["job_id"]: job
        for job in load("data/internships.json")
    }

    profiles = {
        item["profile_id"]: item["profile"]
        for item in load(
            "evaluation/sample_profiles.json"
        )
    }

    searchable = set(
        experiment["configuration"]["searchable_profiles"]
    )

    threshold = ground_truth["relevance_threshold"]

    labels = {
        (item["profile_id"], item["job_id"]): item
        for item in ground_truth["judgments"]
        if item["profile_id"] in searchable
        and item["relevance_grade"] is not None
    }

    relevant = {
        pair
        for pair, item in labels.items()
        if item["relevance_grade"] >= threshold
    }

    suitable = {
        pair
        for pair in relevant
        if labels[pair]["suitability_grade"] >= 2
    }

    highly_suitable = {
        pair
        for pair in relevant
        if labels[pair]["suitability_grade"] == 3
    }

    assert len(jobs) == 150
    assert len(searchable) == 7
    assert len(relevant) == 25
    assert len(suitable) == 17
    assert len(highly_suitable) == 8
    assert experiment["depths"] == DEPTHS

    summaries = {}
    profile_results = {}

    total_ranked = 0

    print("\n========== OFFLINE END-TO-END EVALUATION ==========")

    for depth in DEPTHS:

        print(f"\n========== DEPTH {depth} ==========")

        ranked_by_profile = {}

        correct_pairs = 0
        comparable_pairs = 0
        eligibility_violations = 0
        ranking_seconds = 0.0

        records = experiment["experiments"][str(depth)]

        assert {
            item["profile_id"]
            for item in records
        } == searchable

        for record in records:

            pid = record["profile_id"]

            cached = record["candidate_records"]

            candidates = [
                {
                    "job_id": item["job_id"],
                    "job": jobs[item["job_id"]],
                    "semantic_score": item["semantic_score"],
                    "best_matching_section": None,
                    "matched_chunks": [],
                    "retrieval_evidence": [],
                    "best_query_type": None,
                    "query_count": None,
                    "matched_query_types": [],
                }
                for item in cached
            ]

            ids = [
                item["job_id"]
                for item in candidates
            ]

            assert ids == record["candidate_job_ids"]
            assert len(ids) == len(set(ids))
            assert 0 < len(ids) <= 40

            started = time.perf_counter()

            result = rank_job_candidates(
                profiles[pid],
                candidates,
                top_k=len(candidates),
                reference_year=2026,
            )

            elapsed = time.perf_counter() - started

            ranking_seconds += elapsed

            ranked = result["recommendations"]

            assert len(ranked) == len(candidates)

            assert {
                item["job_id"]
                for item in ranked
            } == set(ids)

            assert [
                item["rank"]
                for item in ranked
            ] == list(range(1, len(ranked) + 1))

            total_ranked += len(ranked)

            compact = [
                {
                    "rank": item["rank"],
                    "job_id": item["job_id"],
                    "job_title": item["job_title"],
                    "company": item["company"],
                    "semantic_score": item["semantic_score"],
                    "compatibility_score": item["compatibility_score"],
                    "ranking_score": item["ranking_score"],
                    "evidence_coverage": item["evidence_coverage"],
                    "mandatory_eligibility_mismatch":
                        item["mandatory_eligibility_mismatch"],
                    "relevance_grade": labels.get(
                        (pid, item["job_id"]), {}
                    ).get("relevance_grade"),
                    "suitability_grade": labels.get(
                        (pid, item["job_id"]), {}
                    ).get("suitability_grade"),
                }
                for item in ranked
            ]

            ranked_by_profile[pid] = compact

            judged = [
                item
                for item in compact
                if item["suitability_grade"] is not None
            ]

            for first, second in combinations(judged, 2):

                a = first["suitability_grade"]
                b = second["suitability_grade"]

                if a == b:
                    continue

                comparable_pairs += 1

                if a > b:
                    correct_pairs += 1

            mismatch_seen = False

            for item in compact:

                if item["mandatory_eligibility_mismatch"]:
                    mismatch_seen = True

                elif mismatch_seen:
                    eligibility_violations += 1

            top5 = {
                (pid, item["job_id"])
                for item in compact[:5]
            }

            print(
                f"{pid} | "
                f"Ranked={len(compact):02d} | "
                f"Top-5 suitable={len(top5 & suitable)} | "
                f"Time={elapsed:.3f}s"
            )

        metrics = {}

        for k in CUTOFFS:

            returned = {
                (pid, item["job_id"])
                for pid, items in ranked_by_profile.items()
                for item in items[:k]
            }

            judged_count = len(returned & labels.keys())

            relevant_count = len(returned & relevant)

            suitable_count = len(returned & suitable)

            highly_count = len(returned & highly_suitable)

            metrics[str(k)] = {
                "returned_count": len(returned),
                "judged_count": judged_count,
                "relevant_count": relevant_count,
                "suitable_count": suitable_count,
                "highly_suitable_count": highly_count,
                "known_relevant_recall": ratio(
                    relevant_count, len(relevant)
                ),
                "known_suitable_recall": ratio(
                    suitable_count, len(suitable)
                ),
                "known_highly_suitable_recall": ratio(
                    highly_count, len(highly_suitable)
                ),
                "judgment_coverage": ratio(
                    judged_count, len(returned)
                ),
                "judged_precision": ratio(
                    relevant_count, judged_count
                ),
            }

        summaries[str(depth)] = {
            "metrics": metrics,
            "correct_pairs": correct_pairs,
            "comparable_pairs": comparable_pairs,
            "conditional_pairwise_accuracy": ratio(
                correct_pairs, comparable_pairs
            ),
            "eligibility_ordering_violations":
                eligibility_violations,
            "ranking_seconds": round(
                ranking_seconds, 4
            ),
        }

        profile_results[str(depth)] = ranked_by_profile

        for k in CUTOFFS:

            m = metrics[str(k)]

            print(
                f"Top-{k:02d} | "
                f"Relevant={m['relevant_count']}/25 | "
                f"Suitable={m['suitable_count']}/17 | "
                f"Highly suitable={m['highly_suitable_count']}/8 | "
                f"Coverage={percentage(m['judgment_coverage'])}"
            )

        print(
            f"Conditional pairwise ranking: "
            f"{correct_pairs}/{comparable_pairs} "
            f"({percentage(ratio(correct_pairs, comparable_pairs))})"
        )

        print(
            "Eligibility ordering violations:",
            eligibility_violations,
        )

        assert eligibility_violations == 0

        expected = experiment["aggregate_results"][
            str(depth)
        ]["40"]

        assert (
            metrics["40"]["relevant_count"]
            == expected["relevant"]
        )

        assert (
            metrics["40"]["returned_count"]
            == expected["returned"]
        )

    print("\n========== FINAL DEPTH COMPARISON ==========")

    for depth in DEPTHS:

        summary = summaries[str(depth)]

        m5 = summary["metrics"]["5"]
        m10 = summary["metrics"]["10"]
        m40 = summary["metrics"]["40"]

        print(
            f"Depth={depth:02d} | "
            f"Candidates={m40['returned_count']:03d} | "
            f"Top-5 suitable={m5['suitable_count']}/17 | "
            f"Top-10 suitable={m10['suitable_count']}/17 | "
            f"Pairwise={percentage(summary['conditional_pairwise_accuracy'])} | "
            f"Ranking time={summary['ranking_seconds']:.3f}s"
        )

    assert total_ranked == 1055

    report = {
        "evaluation_type": "cached_retrieval_production_ranking",
        "reference_year": 2026,
        "annotation_status": ground_truth["annotation_status"],
        "depths": DEPTHS,
        "cutoffs": CUTOFFS,
        "profiles_evaluated": len(searchable),
        "total_candidate_evaluations": total_ranked,
        "known_relevant_pairs": len(relevant),
        "known_suitable_pairs": len(suitable),
        "known_highly_suitable_pairs": len(highly_suitable),
        "aggregate_results": summaries,
        "profile_results": profile_results,
        "limitations": [
            "Partial assistant-draft judgments.",
            "Cached semantic retrieval results.",
            "Missing chunk-level retrieval evidence.",
            "Production ranking function evaluated directly.",
            "Explanation generation not evaluated.",
            "Pairwise comparisons conditional on retrieved judged jobs.",
            "Different depths may have different comparable pairs.",
            "Timing excludes embedding and retrieval.",
            "Not an independent held-out evaluation.",
        ],
    }

    temporary = REPORT_PATH.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    temporary.replace(REPORT_PATH)

    print("\n========== FINAL SUMMARY ==========")

    print("Profiles evaluated:", len(searchable))
    print("Configurations evaluated:", len(DEPTHS))
    print("Total candidate evaluations:", total_ranked)
    print("Gemini API requests: 0")
    print("Report saved:", REPORT_PATH)
    print("Offline end-to-end evaluation: COMPLETE")


if __name__ == "__main__":
    main()
