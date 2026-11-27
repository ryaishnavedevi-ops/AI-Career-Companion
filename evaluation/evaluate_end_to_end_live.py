import json
import math
import time

from itertools import combinations
from pathlib import Path
from statistics import mean, median

from app.job_retrieval_config import (
    DEFAULT_TOP_K_PER_QUERY,
    DEFAULT_MAX_CANDIDATES,
)

from app.job_ranking_engine import (
    InternshipRecommendationEngine,
    ranking_sort_key,
)

from app.job_query_builder import build_search_queries
from app.schemas import RecommendationResponse

from evaluation.evaluate_retrieval import (
    prepare_evaluation,
    sha256_file,
    save_json,
)


ROOT = Path(__file__).resolve().parents[1]

EVALUATION = ROOT / "evaluation"

CHECKPOINT = (
    EVALUATION / "end_to_end_live_checkpoint.json"
)

REPORT = (
    EVALUATION / "end_to_end_live_results.json"
)

OFFLINE_REPORT = (
    EVALUATION / "end_to_end_offline_results.json"
)

CUT_OFFS = [5, 10, 20, 40]

REFERENCE_YEAR = 2026


def load_json(path):

    return json.loads(
        path.read_text(encoding="utf-8-sig")
    )


def ratio(numerator, denominator):

    return (
        numerator / denominator
        if denominator
        else None
    )


def build_labels(ground_truth):

    return {
        (item["profile_id"], item["job_id"]): item
        for item in ground_truth["judgments"]
        if item["relevance_grade"] is not None
    }


def label_sets(labels):

    relevant = {
        key
        for key, label in labels.items()
        if label["relevance_grade"] >= 2
    }

    suitable = {
        key
        for key in relevant
        if labels[key]["suitability_grade"] is not None
        and labels[key]["suitability_grade"] >= 2
    }

    highly_suitable = {
        key
        for key in suitable
        if labels[key]["suitability_grade"] == 3
    }

    return relevant, suitable, highly_suitable


def validate_result(result, profile, expected_queries):

    response = RecommendationResponse(**result)

    assert response.candidate_id == profile["candidate_id"]
    assert response.resume_id == profile["resume_id"]

    assert result["queries"] == expected_queries

    items = result["recommendations"]

    ranking = result["ranking_statistics"]
    retrieval = result["retrieval_statistics"]

    assert items, "No recommendations returned"

    assert len(items) <= DEFAULT_MAX_CANDIDATES

    assert len(items) == ranking["total_ranked"]
    assert len(items) == ranking["total_candidates"]
    assert len(items) == ranking["returned_recommendations"]
    assert len(items) == retrieval["returned_candidates"]

    assert retrieval["top_k_per_query"] == (
        DEFAULT_TOP_K_PER_QUERY
    )

    assert retrieval["total_queries"] == len(expected_queries)

    assert (
        retrieval["total_retrieved"]
        - retrieval["unique_candidates"]
        == retrieval["duplicates_removed"]
    )

    assert ranking["requested_top_k"] == DEFAULT_MAX_CANDIDATES

    ids = [item["job_id"] for item in items]

    assert len(ids) == len(set(ids))

    assert [
        item["rank"] for item in items
    ] == list(range(1, len(items) + 1))

    assert items == sorted(
        items,
        key=ranking_sort_key,
    )

    assert ranking["eligibility_review_count"] == sum(
        item["eligibility_review_required"]
        for item in items
    )

    assert ranking["mandatory_eligibility_mismatch_count"] == sum(
        item["mandatory_eligibility_mismatch"]
        for item in items
    )

    for item in items:

        for field in [
            "compatibility_score",
            "ranking_score",
            "base_ranking_score",
        ]:

            value = item[field]

            if value is not None:

                assert math.isfinite(value)
                assert 0 <= value <= 100.000001

        coverage = item["evidence_coverage"]

        assert math.isfinite(coverage)
        assert 0 <= coverage <= 1

        semantic = item["semantic_score"]

        assert math.isfinite(semantic)
        assert -1 <= semantic <= 1

        assert isinstance(
            item["technical_assessment"],
            dict,
        )

        explanation = item["explanation"]

        assert isinstance(explanation, dict)

        assert explanation.get("summary")

        assert isinstance(
            explanation.get("score_explanation"),
            dict,
        )

        assert isinstance(
            explanation.get("eligibility_reviews"),
            list,
        )

        assert (
            explanation["mandatory_eligibility_mismatch"]
            == item["mandatory_eligibility_mismatch"]
        )

        assert (
            explanation["eligibility_review_required"]
            == item["eligibility_review_required"]
        )

        assert item["retrieval_evidence"]

    return items


def compact_record(profile_id, item, labels):

    label = labels.get(
        (profile_id, item["job_id"]),
        {},
    )

    return {
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
        "eligibility_review_required":
            item["eligibility_review_required"],
        "eligibility_review":
            item["eligibility_review"],
        "relevance_grade":
            label.get("relevance_grade"),
        "suitability_grade":
            label.get("suitability_grade"),
        "technical_assessment":
            item["technical_assessment"],
        "explanation":
            item["explanation"],
    }


def compare_baseline(records, baseline):

    current_ids = [
        item["job_id"] for item in records
    ]

    baseline_ids = [
        item["job_id"] for item in baseline
    ]

    current_set = set(current_ids)
    baseline_set = set(baseline_ids)

    shared = current_set.intersection(baseline_set)

    old_ranks = {
        item["job_id"]: item["rank"]
        for item in baseline
    }

    new_ranks = {
        item["job_id"]: item["rank"]
        for item in records
    }

    return {
        "identical_candidate_set":
            current_set == baseline_set,
        "identical_ranking_order":
            current_ids == baseline_ids,
        "shared_candidates": len(shared),
        "candidate_jaccard_similarity": ratio(
            len(shared),
            len(current_set.union(baseline_set)),
        ),
        "added_candidates":
            sorted(current_set - baseline_set),
        "removed_candidates":
            sorted(baseline_set - current_set),
        "mean_absolute_rank_change": (
            mean(
                abs(new_ranks[job_id] - old_ranks[job_id])
                for job_id in shared
            )
            if shared
            else None
        ),
    }


def pairwise_metrics(records):

    comparable = 0
    correct = 0

    judged = [
        item
        for item in records
        if item["suitability_grade"] is not None
    ]

    for first, second in combinations(judged, 2):

        first_grade = first["suitability_grade"]
        second_grade = second["suitability_grade"]

        if first_grade == second_grade:
            continue

        comparable += 1

        if first_grade > second_grade:
            correct += 1

    return correct, comparable


def aggregate(profile_results, labels):

    relevant, suitable, highly_suitable = label_sets(
        labels
    )

    metrics = {}

    for k in CUT_OFFS:

        selected = [
            (pid, item["job_id"])
            for pid, record in profile_results.items()
            for item in record["recommendations"][:k]
        ]

        returned = len(selected)

        judged = sum(
            key in labels for key in selected
        )

        relevant_count = sum(
            key in relevant for key in selected
        )

        suitable_count = sum(
            key in suitable for key in selected
        )

        highly_suitable_count = sum(
            key in highly_suitable for key in selected
        )

        metrics[str(k)] = {
            "returned_count": returned,
            "judged_count": judged,
            "unjudged_count": returned - judged,
            "relevant_count": relevant_count,
            "suitable_count": suitable_count,
            "highly_suitable_count":
                highly_suitable_count,
            "known_relevant_recall": ratio(
                relevant_count, len(relevant)
            ),
            "known_suitable_recall": ratio(
                suitable_count, len(suitable)
            ),
            "known_highly_suitable_recall": ratio(
                highly_suitable_count,
                len(highly_suitable),
            ),
            "judgment_coverage": ratio(
                judged, returned
            ),
            "judged_precision": ratio(
                relevant_count, judged
            ),
        }

    correct_pairs = 0
    comparable_pairs = 0
    ordering_violations = 0

    for record in profile_results.values():

        items = record["recommendations"]

        correct, comparable = pairwise_metrics(items)

        correct_pairs += correct
        comparable_pairs += comparable

        mismatch_seen = False

        for item in items:

            if item["mandatory_eligibility_mismatch"]:

                mismatch_seen = True

            elif mismatch_seen:

                ordering_violations += 1

    timings = [
        record["execution_seconds"]
        for record in profile_results.values()
    ]

    return {
        "metrics": metrics,
        "correct_pairs": correct_pairs,
        "comparable_pairs": comparable_pairs,
        "conditional_pairwise_accuracy": ratio(
            correct_pairs, comparable_pairs
        ),
        "eligibility_ordering_violations":
            ordering_violations,
        "total_execution_seconds": sum(timings),
        "mean_profile_seconds": mean(timings),
        "median_profile_seconds": median(timings),
        "total_candidates": sum(
            len(record["recommendations"])
            for record in profile_results.values()
        ),
        "total_logical_queries": sum(
            len(record["queries"])
            for record in profile_results.values()
        ),
    }


def main():

    print("\n========== FINAL LIVE EVALUATION ==========")

    assert DEFAULT_TOP_K_PER_QUERY == 15
    assert DEFAULT_MAX_CANDIDATES == 40

    context = prepare_evaluation()

    ground_truth = load_json(
        EVALUATION / "ground_truth.json"
    )

    labels = build_labels(ground_truth)

    relevant, suitable, highly_suitable = label_sets(
        labels
    )

    assert len(relevant) == 25
    assert len(suitable) == 17
    assert len(highly_suitable) == 8

    profiles = context["profiles"]

    expected_profiles = [
        f"P{i:02d}" for i in range(1, 8)
    ]

    offline = load_json(OFFLINE_REPORT)

    baseline = offline["profile_results"]["15"]

    assert set(baseline) == set(expected_profiles)

    fingerprints = dict(
        context["configuration"]["fingerprints"]
    )

    additional_paths = [
        Path(__file__),
        OFFLINE_REPORT,
        ROOT / "app/schemas.py",
        ROOT / "app/job_retrieval_config.py",
        ROOT / "app/student_profile_builder.py",
        ROOT / "app/job_ranking_engine.py",
        ROOT / "app/student_job_comparator.py",
        ROOT / "app/job_resume_matcher.py",
        ROOT / "app/job_requirement_parser.py",
        ROOT / "app/job_skill_requirement_resolver.py",
        ROOT / "app/job_education_matcher.py",
        ROOT / "app/job_education_requirement_resolver.py",
        ROOT / "app/job_experience_matcher.py",
        ROOT / "app/job_project_matcher.py",
        ROOT / "app/job_compatibility_scorer.py",
        ROOT / "app/job_matching_refinement.py",
        ROOT / "app/job_recommendation_explainer.py",
    ]

    for path in additional_paths:

        fingerprints[str(path.relative_to(ROOT))] = (
            sha256_file(path)
        )

    configuration = {
        "reference_year": REFERENCE_YEAR,
        "top_k_per_query": DEFAULT_TOP_K_PER_QUERY,
        "max_candidates": DEFAULT_MAX_CANDIDATES,
        "cutoffs": CUT_OFFS,
        "profiles": expected_profiles,
        "fingerprints": fingerprints,
    }

    print("\n========== NEGATIVE CONTROLS ==========")

    negative_controls = {}

    for pid in ["P08", "P09"]:

        try:

            build_search_queries(profiles[pid])

        except ValueError as exc:

            assert (
                "Insufficient career-related information"
                in str(exc)
            )

            negative_controls[pid] = {
                "status": "passed",
                "message": str(exc),
            }

            print(f"[PASS] {pid}: {exc}")

        else:

            raise AssertionError(
                f"{pid} should reject query generation"
            )

    if CHECKPOINT.exists():

        checkpoint = load_json(CHECKPOINT)

        assert checkpoint["configuration"] == configuration, (
            "Checkpoint configuration changed. "
            "Preserve the old checkpoint before restarting."
        )

        profile_results = checkpoint["profile_results"]

    else:

        profile_results = {}

    assert set(profile_results).issubset(
        expected_profiles
    )

    pending = [
        pid
        for pid in expected_profiles
        if pid not in profile_results
    ]

    print("\nCompleted profiles:", len(profile_results))
    print("Pending profiles:", len(pending))

    if pending:

        engine = InternshipRecommendationEngine()

    for pid in pending:

        print(f"\n========== PROFILE {pid} ==========")

        profile = profiles[pid]

        expected_queries = build_search_queries(profile)

        started = time.perf_counter()

        result = engine.recommend(
            profile,
            top_k=DEFAULT_MAX_CANDIDATES,
            reference_year=REFERENCE_YEAR,
        )

        elapsed = time.perf_counter() - started

        items = validate_result(
            result,
            profile,
            expected_queries,
        )

        assert all(
            item["job_id"] in context["job_ids"]
            for item in items
        )

        records = [
            compact_record(pid, item, labels)
            for item in items
        ]

        comparison = compare_baseline(
            records,
            baseline[pid],
        )

        profile_results[pid] = {
            "profile_id": pid,
            "execution_seconds": elapsed,
            "queries": result["queries"],
            "retrieval_statistics":
                result["retrieval_statistics"],
            "ranking_statistics":
                result["ranking_statistics"],
            "baseline_comparison": comparison,
            "recommendations": records,
        }

        save_json(
            CHECKPOINT,
            {
                "configuration": configuration,
                "profile_results": profile_results,
            },
        )

        print("Candidates:", len(records))
        print("Logical queries:", len(expected_queries))
        print(f"Execution seconds: {elapsed:.4f}")

        print(
            "Identical candidate set:",
            comparison["identical_candidate_set"],
        )

        print(
            "Identical ranking order:",
            comparison["identical_ranking_order"],
        )

        for item in records[:5]:

            print(
                f"#{item['rank']} | "
                f"{item['job_title']} | "
                f"{item['company']} | "
                f"ranking={item['ranking_score']} | "
                f"review={item['eligibility_review_required']}"
            )

        print("[PASS] Response validation")
        print("[PASS] Profile checkpoint saved")

    assert len(profile_results) == 7

    summary = aggregate(profile_results, labels)

    assert summary["total_logical_queries"] == 20

    assert summary["eligibility_ordering_violations"] == 0

    report = {
        "evaluation_type":
            "live_production_end_to_end",
        "configuration": configuration,
        "annotation_status":
            ground_truth["annotation_status"],
        "evaluation_complete": True,
        "profiles_evaluated": len(profile_results),
        "negative_controls": negative_controls,
        "known_relevant_pairs": len(relevant),
        "known_suitable_pairs": len(suitable),
        "known_highly_suitable_pairs":
            len(highly_suitable),
        "aggregate_results": summary,
        "profile_results": profile_results,
        "limitations": [
            "Ground truth is partial and not human verified.",
            "Unjudged recommendations are not assumed irrelevant.",
            "Known recall is not exhaustive corpus recall.",
            "Pairwise accuracy is conditional on retrieved judged jobs.",
            "Logical queries do not count API retries.",
            "Latency excludes engine initialization.",
            "Checkpointed profiles may come from different runs.",
            "Internal Top-40 evaluation is not the public API limit.",
            "Specialized skill extraction remains incomplete.",
        ],
    }

    save_json(REPORT, report)

    print("\n========== AGGREGATE RESULTS ==========")

    print(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n========== FINAL SUMMARY ==========")

    print("Profiles evaluated:", len(profile_results))
    print("Negative controls passed:", len(negative_controls))
    print("Total candidates:", summary["total_candidates"])
    print("Logical queries:", summary["total_logical_queries"])
    print(
        "Eligibility ordering violations:",
        summary["eligibility_ordering_violations"],
    )
    print("Report saved:", REPORT)
    print("Live end-to-end evaluation: COMPLETE")


if __name__ == "__main__":
    main()
