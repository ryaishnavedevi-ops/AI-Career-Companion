"""Regression tests for partial-judgment retrieval metrics."""

from copy import deepcopy

from evaluation.retrieval_metrics import (
    calculate_retrieval_metrics,
)

checks = []


def check(name, condition):

    checks.append(bool(condition))

    print(
        f"[{'PASS' if condition else 'FAIL'}] {name}"
    )


def expect_error(name, function):

    try:
        function()
    except ValueError:
        check(name, True)
    else:
        check(name, False)


print("\n========== FULLY JUDGED RESULTS ==========")

metrics = calculate_retrieval_metrics(
    ["A", "B", "C"],
    {"A": 3, "B": 0, "C": 2, "D": 3},
    k=3,
)

check(
    "Complete judgment coverage",
    metrics["judgment_coverage"] == 1.0
)

check(
    "Judged precision correct",
    metrics["judged_precision"] == 2 / 3
)

check(
    "Precision bounds collapse when fully judged",
    metrics["precision_lower_bound"]
    == metrics["precision_upper_bound"]
    == 2 / 3
)

check(
    "Known-relevant recall correct",
    metrics["known_relevant_recall"] == 2 / 3
)

check(
    "Missed relevant job identified",
    metrics["missed_known_relevant_job_ids"] == ["D"]
)


print("\n========== ENTIRELY UNJUDGED RESULTS ==========")

metrics = calculate_retrieval_metrics(
    ["A", "B", "C"],
    {"D": 3},
    k=3,
)

check(
    "All results remain unjudged",
    metrics["unjudged_count"] == 3
)

check(
    "Judged precision undefined",
    metrics["judged_precision"] is None
)

check(
    "Judgment coverage zero",
    metrics["judgment_coverage"] == 0.0
)

check(
    "Precision uncertainty preserved",
    metrics["precision_lower_bound"] == 0.0
    and metrics["precision_upper_bound"] == 1.0
)

check(
    "Known-relevant recall zero",
    metrics["known_relevant_recall"] == 0.0
)

check(
    "Reciprocal rank uncertainty preserved",
    metrics["reciprocal_rank_lower_bound"] == 0.0
    and metrics["reciprocal_rank_upper_bound"] == 1.0
)


print("\n========== NULL AND BELOW-THRESHOLD LABELS ==========")

metrics = calculate_retrieval_metrics(
    ["A", "B", "C", "D"],
    {"A": None, "B": 1, "C": 2, "D": 0},
    k=4,
)

check(
    "Null relevance remains unjudged",
    metrics["unjudged_job_ids"] == ["A"]
)

check(
    "Grade one is below relevance threshold",
    "B" in metrics["irrelevant_job_ids"]
)

check(
    "Grade zero is irrelevant",
    "D" in metrics["irrelevant_job_ids"]
)

check(
    "Grade two is relevant",
    metrics["relevant_job_ids"] == ["C"]
)

check(
    "First known relevant rank correct",
    metrics["first_known_relevant_rank"] == 3
)

check(
    "Reciprocal rank bounds correct",
    metrics["reciprocal_rank_lower_bound"] == 1 / 3
    and metrics["reciprocal_rank_upper_bound"] == 1.0
)


print("\n========== EMPTY RETRIEVAL RESULTS ==========")

metrics = calculate_retrieval_metrics(
    [],
    {"A": 3},
    k=5,
)

check(
    "Requested K preserved",
    metrics["requested_k"] == 5
)

check(
    "Returned count zero",
    metrics["returned_count"] == 0
)

check(
    "Empty-result precision undefined",
    metrics["judged_precision"] is None
    and metrics["precision_lower_bound"] is None
    and metrics["precision_upper_bound"] is None
)

check(
    "Empty-result coverage undefined",
    metrics["judgment_coverage"] is None
)

check(
    "Known relevant job not retrieved",
    metrics["known_relevant_recall"] == 0.0
)

check(
    "Empty reciprocal rank bounds zero",
    metrics["reciprocal_rank_lower_bound"] == 0.0
    and metrics["reciprocal_rank_upper_bound"] == 0.0
)


print("\n========== NO KNOWN RELEVANT JOBS ==========")

metrics = calculate_retrieval_metrics(
    ["A", "B"],
    {"A": 0, "B": 1},
    k=2,
)

check(
    "Known-relevant recall undefined",
    metrics["known_relevant_recall"] is None
)

check(
    "Fully judged irrelevant results have zero precision",
    metrics["judged_precision"] == 0.0
)

check(
    "No known relevant rank",
    metrics["first_known_relevant_rank"] is None
)

check(
    "No possible relevant result",
    metrics["reciprocal_rank_upper_bound"] == 0.0
)


print("\n========== TOP-K AND SHORT RESULTS ==========")

results = ["A", "B", "C", "D"]
labels = {"A": 3, "B": 0, "C": 2, "D": 3}

original_results = deepcopy(results)
original_labels = deepcopy(labels)

top2 = calculate_retrieval_metrics(
    results, labels, k=2
)

top4 = calculate_retrieval_metrics(
    results, labels, k=4
)

top10 = calculate_retrieval_metrics(
    results, labels, k=10
)

check(
    "Top-K truncation correct",
    top2["returned_count"] == 2
)

check(
    "Top-K order preserved",
    [
        item["job_id"]
        for item in top2["ranked_results"]
    ] == ["A", "B"]
)

check(
    "Known-relevant recall increases with K",
    top2["known_relevant_recall"]
    <= top4["known_relevant_recall"]
)

check(
    "Short result count preserved",
    top10["requested_k"] == 10
    and top10["returned_count"] == 4
)

check(
    "Short-result precision uses actual count",
    top10["precision_lower_bound"] == 0.75
)

check(
    "Input result list unchanged",
    results == original_results
)

check(
    "Input relevance labels unchanged",
    labels == original_labels
)


print("\n========== CUSTOM RELEVANCE THRESHOLD ==========")

metrics = calculate_retrieval_metrics(
    ["A", "B", "C"],
    {"A": 1, "B": 2, "C": 3},
    k=3,
    relevance_threshold=3,
)

check(
    "Custom threshold applied",
    metrics["relevant_job_ids"] == ["C"]
)

check(
    "Lower grades classified consistently",
    metrics["irrelevant_job_ids"] == ["A", "B"]
)

check(
    "Known relevant denominator updated",
    metrics["known_relevant_count"] == 1
)


print("\n========== INVALID INPUT VALIDATION ==========")

expect_error(
    "Duplicate job IDs rejected",
    lambda: calculate_retrieval_metrics(
        ["A", "A"], {"A": 3}, k=2
    )
)

expect_error(
    "Zero K rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": 3}, k=0
    )
)

expect_error(
    "Negative K rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": 3}, k=-1
    )
)

expect_error(
    "Boolean K rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": 3}, k=True
    )
)

expect_error(
    "Non-list results rejected",
    lambda: calculate_retrieval_metrics(
        "A", {"A": 3}, k=1
    )
)

expect_error(
    "Non-dictionary labels rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], [3], k=1
    )
)

expect_error(
    "Invalid relevance grade rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": 4}, k=1
    )
)

expect_error(
    "Boolean relevance grade rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": True}, k=1
    )
)

expect_error(
    "Empty job ID rejected",
    lambda: calculate_retrieval_metrics(
        [""], {}, k=1
    )
)

expect_error(
    "Invalid relevance threshold rejected",
    lambda: calculate_retrieval_metrics(
        ["A"], {"A": 3}, k=1,
        relevance_threshold=4
    )
)


print("\n========== FINAL SUMMARY ==========")

print(f"Passed: {sum(checks)}/{len(checks)}")
print(f"Failed: {len(checks) - sum(checks)}")

raise SystemExit(0 if all(checks) else 1)
