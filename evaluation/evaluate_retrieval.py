"""Evaluate production RAG retrieval using partial relevance judgments."""

import argparse
import hashlib
import json
import math
import time

from pathlib import Path

from app.job_query_builder import build_search_queries

from evaluation.retrieval_metrics import (
    calculate_retrieval_metrics,
)


ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = ROOT / "data/internships.json"
PROFILES_PATH = ROOT / "evaluation/sample_profiles.json"
GROUND_TRUTH_PATH = ROOT / "evaluation/ground_truth.json"

CHECKPOINT_PATH = (
    ROOT / "evaluation/retrieval_evaluation_checkpoint.json"
)

REPORT_PATH = (
    ROOT / "evaluation/retrieval_evaluation_results.json"
)

TOP_K_PER_QUERY = 10
MAX_CANDIDATES = 40
CUTOFFS = [5, 10, 20, 40]


def load_json(path):

    return json.loads(
        path.read_text(encoding="utf-8-sig")
    )


def sha256_file(path):

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def save_json(path, data):

    temporary_path = path.with_suffix(".tmp")

    temporary_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def require(condition, message):

    if not condition:
        raise ValueError(message)


def prepare_evaluation():

    jobs = load_json(DATASET_PATH)
    profile_records = load_json(PROFILES_PATH)
    ground_truth = load_json(GROUND_TRUTH_PATH)

    job_ids = {
        job["job_id"]
        for job in jobs
    }

    profiles = {
        item["profile_id"]: item["profile"]
        for item in profile_records
    }

    require(
        len(job_ids) == len(jobs) == 150,
        "Dataset count or job ID uniqueness mismatch."
    )

    require(
        len(profiles) == len(profile_records) == 9,
        "Profile count or profile ID uniqueness mismatch."
    )

    require(
        sha256_file(DATASET_PATH)
        == ground_truth["dataset_sha256"],
        "Dataset fingerprint mismatch."
    )

    require(
        sha256_file(PROFILES_PATH)
        == ground_truth["profiles_sha256"],
        "Profile fingerprint mismatch."
    )

    require(
        set(ground_truth["job_ids"]) == job_ids,
        "Ground truth job IDs do not match dataset."
    )

    searchable = ground_truth["searchable_profiles"]
    rejected = ground_truth["expected_query_rejections"]

    require(
        len(searchable) == len(set(searchable)) == 7,
        "Expected seven unique searchable profiles."
    )

    require(
        len(rejected) == len(set(rejected)) == 2,
        "Expected two unique negative controls."
    )

    require(
        not set(searchable).intersection(rejected),
        "Searchable and rejected profiles overlap."
    )

    require(
        set(searchable + rejected) == set(profiles),
        "Ground truth profile coverage mismatch."
    )

    threshold = ground_truth["relevance_threshold"]

    require(
        type(threshold) is int and 1 <= threshold <= 3,
        "Invalid relevance threshold."
    )

    labels = {
        profile_id: {}
        for profile_id in searchable
    }

    seen_pairs = set()

    for judgment in ground_truth["judgments"]:

        profile_id = judgment["profile_id"]
        job_id = judgment["job_id"]
        grade = judgment.get("relevance_grade")

        require(
            profile_id in profiles and job_id in job_ids,
            "Unknown profile or job in ground truth."
        )

        pair = (profile_id, job_id)

        require(
            pair not in seen_pairs,
            "Duplicate ground truth judgment."
        )

        seen_pairs.add(pair)

        if grade is not None:

            require(
                profile_id in labels,
                "Unexpected relevance label for negative control."
            )

            require(
                type(grade) is int and 0 <= grade <= 3,
                "Invalid relevance grade."
            )

            labels[profile_id][job_id] = grade

    queries = {
        profile_id: build_search_queries(
            profiles[profile_id]
        )
        for profile_id in searchable
    }

    total_queries = sum(
        len(items)
        for items in queries.values()
    )

    negative_controls = []

    for profile_id in rejected:

        try:
            build_search_queries(profiles[profile_id])

        except ValueError as error:

            require(
                "Insufficient career-related information"
                in str(error),
                f"Unexpected rejection reason: {profile_id}"
            )

            negative_controls.append({
                "profile_id": profile_id,
                "passed": True,
                "reason": str(error),
            })

        else:

            raise ValueError(
                f"Negative control accepted: {profile_id}"
            )

    total_labels = sum(
        len(items)
        for items in labels.values()
    )

    known_relevant = sum(
        grade >= threshold
        for items in labels.values()
        for grade in items.values()
    )

    require(
        total_labels
        == ground_truth["coverage"]["judged_relevance_pairs"],
        "Relevance judgment count mismatch."
    )

    require(
        all(
            any(grade >= threshold for grade in items.values())
            for items in labels.values()
        ),
        "A searchable profile has no known relevant jobs."
    )

    fingerprint_paths = [
        DATASET_PATH,
        PROFILES_PATH,
        GROUND_TRUTH_PATH,
        ROOT / "data/job_chunks.json",
        ROOT / "data/job_embeddings.npy",
        ROOT / "data/job_index_metadata.json",
        ROOT / "app/job_query_builder.py",
        ROOT / "app/job_retriever.py",
        ROOT / "app/job_candidate_retriever.py",
        ROOT / "app/job_embedder.py",
        ROOT / "app/skill_vocabulary.py",
        ROOT / "evaluation/retrieval_metrics.py",
        Path(__file__).resolve(),
    ]

    configuration = {
        "fingerprints": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in fingerprint_paths
        },
        "top_k_per_query": TOP_K_PER_QUERY,
        "max_candidates": MAX_CANDIDATES,
        "cutoffs": CUTOFFS,
        "relevance_threshold": threshold,
        "annotation_status": ground_truth["annotation_status"],
        "reference_year": ground_truth["reference_year"],
        "searchable_profiles": searchable,
        "total_queries": total_queries,
        "total_jobs": len(jobs),
        "total_relevance_labels": total_labels,
        "known_relevant_pairs": known_relevant,
    }

    return {
        "configuration": configuration,
        "profiles": profiles,
        "labels": labels,
        "queries": queries,
        "job_ids": job_ids,
        "negative_controls": negative_controls,
    }


def evaluate_profile(context, profile_id, retriever):

    started = time.perf_counter()

    result = retriever.retrieve_candidates(
        context["profiles"][profile_id],
        top_k_per_query=TOP_K_PER_QUERY,
        max_candidates=MAX_CANDIDATES,
    )

    elapsed = time.perf_counter() - started

    candidates = result["candidates"]
    statistics = result["retrieval_statistics"]

    ids = [
        candidate["job_id"]
        for candidate in candidates
    ]

    require(
        result["queries"] == context["queries"][profile_id],
        "Generated queries changed during evaluation."
    )

    require(
        len(ids) == len(set(ids)),
        "Duplicate retrieved internship IDs."
    )

    require(
        set(ids).issubset(context["job_ids"]),
        "Retrieved unknown internship IDs."
    )

    require(
        len(ids) <= MAX_CANDIDATES,
        "Maximum candidate limit exceeded."
    )

    require(
        statistics["returned_candidates"] == len(ids),
        "Returned candidate count mismatch."
    )

    require(
        statistics["total_queries"]
        == len(context["queries"][profile_id]),
        "Query count mismatch."
    )

    require(
        statistics["duplicates_removed"]
        == statistics["total_retrieved"]
        - statistics["unique_candidates"],
        "Deduplication statistics mismatch."
    )

    require(
        all(
            math.isfinite(item["semantic_score"])
            and -1 <= item["semantic_score"] <= 1
            for item in candidates
        ),
        "Invalid semantic similarity score."
    )

    require(
        all(
            candidates[i]["semantic_score"]
            >= candidates[i + 1]["semantic_score"]
            for i in range(len(candidates) - 1)
        ),
        "Semantic retrieval order is invalid."
    )

    metrics = {
        str(k): calculate_retrieval_metrics(
            ids,
            context["labels"][profile_id],
            k=k,
            relevance_threshold=context[
                "configuration"
            ]["relevance_threshold"],
        )
        for k in CUTOFFS
    }

    candidate_records = [
        {
            "rank": rank,
            "job_id": candidate["job_id"],
            "job_title": candidate["job_title"],
            "company": candidate["company"],
            "domain": candidate["domain"],
            "semantic_score": candidate["semantic_score"],
            "best_query_type": candidate["best_query_type"],
            "best_matching_section": candidate[
                "best_matching_section"
            ],
            "query_count": candidate["query_count"],
            "matched_query_types": candidate[
                "matched_query_types"
            ],
        }
        for rank, candidate in enumerate(
            candidates, start=1
        )
    ]

    return {
        "profile_id": profile_id,
        "retrieval_seconds": round(elapsed, 4),
        "queries": result["queries"],
        "retrieval_statistics": statistics,
        "candidates": candidate_records,
        "metrics": metrics,
    }


def aggregate_metrics(profile_results):

    metric_names = [
        "judgment_coverage",
        "judged_precision",
        "precision_lower_bound",
        "precision_upper_bound",
        "known_relevant_recall",
        "reciprocal_rank_lower_bound",
        "reciprocal_rank_upper_bound",
    ]

    aggregates = {}

    for k in CUTOFFS:

        records = [
            item["metrics"][str(k)]
            for item in profile_results
        ]

        summary = {}

        for name in metric_names:

            values = [
                record[name]
                for record in records
                if record[name] is not None
            ]

            summary[name] = {
                "macro_average": (
                    sum(values) / len(values)
                    if values else None
                ),
                "defined_profiles": len(values),
                "total_profiles": len(records),
            }

        relevant = sum(
            record["relevant_count"]
            for record in records
        )

        judged = sum(
            record["judged_count"]
            for record in records
        )

        returned = sum(
            record["returned_count"]
            for record in records
        )

        unjudged = sum(
            record["unjudged_count"]
            for record in records
        )

        known_relevant = sum(
            record["known_relevant_count"]
            for record in records
        )

        summary["micro_counts"] = {
            "returned": returned,
            "judged": judged,
            "relevant": relevant,
            "unjudged": unjudged,
            "known_relevant": known_relevant,
        }

        summary["micro_metrics"] = {
            "judgment_coverage": (
                judged / returned if returned else None
            ),
            "judged_precision": (
                relevant / judged if judged else None
            ),
            "precision_lower_bound": (
                relevant / returned if returned else None
            ),
            "precision_upper_bound": (
                (relevant + unjudged) / returned
                if returned else None
            ),
            "known_relevant_recall": (
                relevant / known_relevant
                if known_relevant else None
            ),
        }

        aggregates[str(k)] = summary

    return aggregates


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate evaluation inputs without API requests."
    )

    args = parser.parse_args()

    context = prepare_evaluation()

    config = context["configuration"]

    print("\n========== EVALUATION CONFIGURATION ==========")

    for key, value in config.items():

        if key != "fingerprints":
            print(f"{key}: {value}")

    print("\n========== PROFILE QUERIES ==========")

    for profile_id, queries in context["queries"].items():

        print(f"\n{profile_id}: {len(queries)} queries")

        for query in queries:
            print(
                f"  [{query['query_type']}] "
                f"{query['query']}"
            )

    print("\n========== NEGATIVE CONTROLS ==========")

    for control in context["negative_controls"]:
        print(f"[PASS] {control['profile_id']}")

    print("\nInput validation: PASS")

    if args.dry_run:

        print("Dry run completed successfully.")
        print("Gemini API requests: 0")

        return

    from app.job_candidate_retriever import (
        JobCandidateRetriever,
    )

    if CHECKPOINT_PATH.exists():

        checkpoint = load_json(CHECKPOINT_PATH)

        require(
            checkpoint["configuration"] == config,
            "Checkpoint configuration mismatch. "
            "Archive the old checkpoint before restarting."
        )

    else:

        checkpoint = {
            "configuration": config,
            "profile_results": {},
        }

    completed = checkpoint["profile_results"]

    require(
        set(completed).issubset(
            config["searchable_profiles"]
        ),
        "Checkpoint contains unknown profiles."
    )

    pending = [
        profile_id
        for profile_id in config["searchable_profiles"]
        if profile_id not in completed
    ]

    retriever = (
        JobCandidateRetriever()
        if pending else None
    )

    print("\n========== LIVE RETRIEVAL EVALUATION ==========")

    for profile_id in config["searchable_profiles"]:

        if profile_id in completed:

            print(f"[RESUME] {profile_id}: already completed")
            continue

        print(f"\nEvaluating {profile_id}...", flush=True)

        record = evaluate_profile(
            context,
            profile_id,
            retriever,
        )

        completed[profile_id] = record

        save_json(CHECKPOINT_PATH, checkpoint)

        print(
            f"[PASS] {profile_id}: "
            f"{len(record['candidates'])} candidates, "
            f"{record['retrieval_seconds']:.2f} seconds"
        )

        for k in CUTOFFS:

            metrics = record["metrics"][str(k)]

            print(
                f"  Top-{k}: "
                f"relevant={metrics['relevant_count']}, "
                f"judged={metrics['judged_count']}, "
                f"unjudged={metrics['unjudged_count']}, "
                f"known-relevant recall="
                f"{metrics['known_relevant_recall']:.2%}"
            )

    profile_results = [
        completed[profile_id]
        for profile_id in config["searchable_profiles"]
    ]

    aggregates = aggregate_metrics(profile_results)

    report = {
        "evaluation_type": "production_rag_retrieval",
        "configuration": config,
        "evaluation_complete": True,
        "completed_profiles": len(profile_results),
        "negative_controls": context["negative_controls"],
        "metric_limitations": [
            "Ground truth is partial and not human verified.",
            "Unjudged results are not treated as irrelevant.",
            "Precision bounds use actual returned counts.",
            "Known-relevant recall is not full corpus recall.",
            "Macro averages exclude undefined ratios.",
            "Cutoffs use merged semantic candidate ordering.",
            "Recorded latency includes API retries when applicable.",
        ],
        "aggregate_metrics": aggregates,
        "profile_results": profile_results,
    }

    save_json(REPORT_PATH, report)

    print("\n========== AGGREGATE RESULTS ==========")

    for k, summary in aggregates.items():

        print(f"\nTop-{k}")

        for name, value in summary["micro_metrics"].items():

            display = (
                f"{value:.2%}"
                if value is not None else "Undefined"
            )

            print(f"  {name}: {display}")

    print("\nRetrieval evaluation: COMPLETE")
    print(f"Profiles completed: {len(profile_results)}/7")
    print(f"Report saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
