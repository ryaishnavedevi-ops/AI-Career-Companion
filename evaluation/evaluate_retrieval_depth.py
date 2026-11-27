"""Compare retrieval depths using shared query search results."""

import json
import time

from copy import deepcopy
from pathlib import Path

from app.job_retriever import JobRetriever
from app.job_candidate_retriever import JobCandidateRetriever

from evaluation.evaluate_retrieval import (
    prepare_evaluation,
    save_json,
)

from evaluation.retrieval_metrics import (
    calculate_retrieval_metrics,
)


ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = (
    ROOT / "evaluation/retrieval_depth_experiment.json"
)

DEPTHS = [10, 15, 20, 30, 40]

MAX_CANDIDATES = 40


class CachedRetriever:
    """Retrieve once per query and reuse ranked prefixes."""

    def __init__(self, retriever):

        self.retriever = retriever
        self.cache = {}
        self.search_calls = 0

    def search(self, query, top_k=5):

        if top_k > max(DEPTHS):
            raise ValueError(
                "Requested depth exceeds cached depth."
            )

        if query not in self.cache:

            self.cache[query] = self.retriever.search(
                query=query,
                top_k=max(DEPTHS),
            )

            self.search_calls += 1

        return deepcopy(
            self.cache[query][:top_k]
        )


def main():

    context = prepare_evaluation()

    config = context["configuration"]

    threshold = config["relevance_threshold"]

    cached = CachedRetriever(JobRetriever())

    retriever = JobCandidateRetriever(
        retriever=cached
    )

    experiments = {
        str(depth): []
        for depth in DEPTHS
    }

    started = time.perf_counter()

    print("\n========== RETRIEVAL DEPTH EXPERIMENT ==========")

    print("Depths:", DEPTHS)
    print("Maximum candidates:", MAX_CANDIDATES)

    for pid in config["searchable_profiles"]:

        print(f"\nEvaluating {pid}...", flush=True)

        previous_ids = set()

        for depth in DEPTHS:

            result = retriever.retrieve_candidates(
                context["profiles"][pid],
                top_k_per_query=depth,
                max_candidates=MAX_CANDIDATES,
            )

            candidates = result["candidates"]

            ids = [
                item["job_id"]
                for item in candidates
            ]

            assert len(ids) == len(set(ids))
            assert len(ids) <= MAX_CANDIDATES
            assert set(ids).issubset(context["job_ids"])

            metrics = {
                str(k): calculate_retrieval_metrics(
                    ids,
                    context["labels"][pid],
                    k=k,
                    relevance_threshold=threshold,
                )
                for k in [5, 10, 20, 40]
            }

            record = {
                "profile_id": pid,
                "top_k_per_query": depth,
                "retrieval_statistics": result[
                    "retrieval_statistics"
                ],
                "candidate_job_ids": ids,
                "candidate_records": [
                    {
                        "job_id": item["job_id"],
                        "job_title": item["job_title"],
                        "company": item["company"],
                        "semantic_score": item["semantic_score"],
                    }
                    for item in candidates
                ],
                "metrics": metrics,
                "added_candidates": sorted(
                    set(ids) - previous_ids
                ),
                "removed_candidates": sorted(
                    previous_ids - set(ids)
                ),
            }

            experiments[str(depth)].append(record)

            previous_ids = set(ids)

            full = metrics["40"]

            print(
                f"  Depth={depth:02d} | "
                f"Candidates={len(ids):02d} | "
                f"Relevant={full['relevant_count']}/"
                f"{full['known_relevant_count']} | "
                f"Recall={full['known_relevant_recall']:.2%}",
                flush=True,
            )

    elapsed = time.perf_counter() - started

    print("\n========== AGGREGATE COMPARISON ==========")

    summaries = {}

    for depth in DEPTHS:

        records = experiments[str(depth)]

        summary = {}

        for k in [5, 10, 20, 40]:

            metrics = [
                item["metrics"][str(k)]
                for item in records
            ]

            relevant = sum(
                item["relevant_count"]
                for item in metrics
            )

            known = sum(
                item["known_relevant_count"]
                for item in metrics
            )

            returned = sum(
                item["returned_count"]
                for item in metrics
            )

            judged = sum(
                item["judged_count"]
                for item in metrics
            )

            unjudged = sum(
                item["unjudged_count"]
                for item in metrics
            )

            summary[str(k)] = {
                "returned": returned,
                "relevant": relevant,
                "known_relevant": known,
                "judged": judged,
                "unjudged": unjudged,
                "known_relevant_recall": (
                    relevant / known if known else None
                ),
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
            }

        summaries[str(depth)] = summary

        full = summary["40"]

        print(
            f"Depth={depth:02d} | "
            f"Candidates={full['returned']:03d} | "
            f"Relevant={full['relevant']}/"
            f"{full['known_relevant']} | "
            f"Recall={full['known_relevant_recall']:.2%}"
        )

    print("\n========== BASELINE COMPARISON ==========")

    baseline = json.loads(
        (
            ROOT
            / "evaluation/retrieval_evaluation_baseline.json"
        ).read_text(encoding="utf-8-sig")
    )

    baseline_lookup = {
        item["profile_id"]: item
        for item in baseline["profile_results"]
    }

    baseline_comparison = []

    for item in experiments["10"]:

        pid = item["profile_id"]

        old_ids = [
            candidate["job_id"]
            for candidate in baseline_lookup[pid]["candidates"]
        ]

        new_ids = item["candidate_job_ids"]

        comparison = {
            "profile_id": pid,
            "identical_candidate_order": old_ids == new_ids,
            "identical_candidate_set": (
                set(old_ids) == set(new_ids)
            ),
            "old_relevant_count": baseline_lookup[pid][
                "metrics"
            ]["40"]["relevant_count"],
            "new_relevant_count": item[
                "metrics"
            ]["40"]["relevant_count"],
        }

        baseline_comparison.append(comparison)

        print(json.dumps(comparison))

    unique_queries = {
        item["query"]
        for queries in context["queries"].values()
        for item in queries
    }

    assert cached.search_calls == len(unique_queries)

    report = {
        "evaluation_type": "retrieval_depth_sensitivity",
        "configuration": config,
        "depths": DEPTHS,
        "max_candidates": MAX_CANDIDATES,
        "unique_query_search_calls": cached.search_calls,
        "experiment_seconds": round(elapsed, 4),
        "baseline_comparison": baseline_comparison,
        "aggregate_results": summaries,
        "experiments": experiments,
        "limitations": [
            "Partial assistant-draft relevance judgments.",
            "All depths reuse the same fresh query results.",
            "Original baseline used a separate embedding run.",
            "Search call count excludes API retries.",
            "Timing is not independent per-depth latency.",
            "No production retrieval settings were modified.",
        ],
    }

    save_json(REPORT_PATH, report)

    print("\n========== FINAL SUMMARY ==========")

    print("Profiles evaluated:", len(config["searchable_profiles"]))
    print("Configurations evaluated:", len(DEPTHS))
    print("Unique query search calls:", cached.search_calls)
    print("Total experiment seconds:", round(elapsed, 2))
    print("Report saved:", REPORT_PATH)
    print("Retrieval depth experiment: COMPLETE")


if __name__ == "__main__":
    main()
