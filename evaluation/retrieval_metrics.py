"""Retrieval evaluation metrics for partially judged datasets."""


def safe_ratio(numerator, denominator):
    """Return None when a metric cannot be established."""

    if denominator == 0:
        return None

    return numerator / denominator


def calculate_retrieval_metrics(
    retrieved_job_ids,
    relevance_labels,
    k,
    relevance_threshold=2,
):
    """Evaluate ranked retrieval results using partial relevance labels."""

    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer.")

    if not isinstance(retrieved_job_ids, list):
        raise ValueError(
            "Retrieved job IDs must be a list."
        )

    if not isinstance(relevance_labels, dict):
        raise ValueError(
            "Relevance labels must be a dictionary."
        )

    if type(relevance_threshold) is not int or not (
        1 <= relevance_threshold <= 3
    ):
        raise ValueError(
            "Relevance threshold must be between 1 and 3."
        )

    if any(
        not isinstance(job_id, str) or not job_id.strip()
        for job_id in retrieved_job_ids
    ):
        raise ValueError(
            "Retrieved job IDs must be nonempty strings."
        )

    if len(retrieved_job_ids) != len(set(retrieved_job_ids)):
        raise ValueError(
            "Retrieved job IDs must be unique."
        )

    for job_id, grade in relevance_labels.items():

        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("Invalid labeled job ID.")

        if grade is not None and (
            type(grade) is not int
            or not 0 <= grade <= 3
        ):
            raise ValueError(
                f"Invalid relevance grade for job {job_id}."
            )

    selected = retrieved_job_ids[:k]

    known_relevant_ids = {
        job_id
        for job_id, grade in relevance_labels.items()
        if grade is not None
        and grade >= relevance_threshold
    }

    relevant_ids = []
    irrelevant_ids = []
    unjudged_ids = []

    ranked_results = []

    for rank, job_id in enumerate(selected, start=1):

        grade = relevance_labels.get(job_id)

        if grade is None:

            status = "unjudged"
            unjudged_ids.append(job_id)

        elif grade >= relevance_threshold:

            status = "relevant"
            relevant_ids.append(job_id)

        else:

            status = "irrelevant"
            irrelevant_ids.append(job_id)

        ranked_results.append({
            "rank": rank,
            "job_id": job_id,
            "relevance_grade": grade,
            "relevance_status": status,
        })

    returned_count = len(selected)

    relevant_count = len(relevant_ids)
    irrelevant_count = len(irrelevant_ids)
    unjudged_count = len(unjudged_ids)

    judged_count = relevant_count + irrelevant_count

    known_relevant_count = len(known_relevant_ids)

    first_relevant_rank = next(
        (
            item["rank"]
            for item in ranked_results
            if item["relevance_status"] == "relevant"
        ),
        None,
    )

    first_possible_relevant_rank = next(
        (
            item["rank"]
            for item in ranked_results
            if item["relevance_status"] != "irrelevant"
        ),
        None,
    )

    return {
        "requested_k": k,
        "returned_count": returned_count,

        "relevant_count": relevant_count,
        "irrelevant_count": irrelevant_count,
        "unjudged_count": unjudged_count,
        "judged_count": judged_count,

        "known_relevant_count": known_relevant_count,

        "judgment_coverage": safe_ratio(
            judged_count,
            returned_count,
        ),

        "judged_precision": safe_ratio(
            relevant_count,
            judged_count,
        ),

        "precision_lower_bound": safe_ratio(
            relevant_count,
            returned_count,
        ),

        "precision_upper_bound": safe_ratio(
            relevant_count + unjudged_count,
            returned_count,
        ),

        "known_relevant_recall": safe_ratio(
            relevant_count,
            known_relevant_count,
        ),

        "first_known_relevant_rank": first_relevant_rank,

        "reciprocal_rank_lower_bound": (
            1 / first_relevant_rank
            if first_relevant_rank is not None
            else 0.0
        ),

        "reciprocal_rank_upper_bound": (
            1 / first_possible_relevant_rank
            if first_possible_relevant_rank is not None
            else 0.0
        ),

        "relevant_job_ids": relevant_ids,
        "irrelevant_job_ids": irrelevant_ids,
        "unjudged_job_ids": unjudged_ids,

        "missed_known_relevant_job_ids": sorted(
            known_relevant_ids - set(relevant_ids)
        ),

        "ranked_results": ranked_results,
    }
