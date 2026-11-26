from app.job_query_builder import build_search_queries
from app.job_retriever import JobRetriever


class JobCandidateRetriever:
    """Retrieve and merge internship candidates for a student."""

    def __init__(self, retriever=None):
        self.retriever = (
            retriever if retriever is not None
            else JobRetriever()
        )

    def retrieve_candidates(
        self,
        profile,
        top_k_per_query=10,
        max_candidates=40,
    ):
        """Retrieve unique internships using multiple queries."""

        if (
            not isinstance(top_k_per_query, int)
            or top_k_per_query < 1
        ):
            raise ValueError(
                "top_k_per_query must be a positive integer."
            )

        if (
            not isinstance(max_candidates, int)
            or max_candidates < 1
        ):
            raise ValueError(
                "max_candidates must be a positive integer."
            )

        queries = build_search_queries(profile)

        candidates = {}
        query_statistics = []
        total_retrieved = 0

        for query_record in queries:

            query_type = query_record["query_type"]
            query = query_record["query"]

            results = self.retriever.search(
                query=query,
                top_k=top_k_per_query,
            )

            total_retrieved += len(results)

            query_statistics.append({
                "query_type": query_type,
                "query": query,
                "results_retrieved": len(results),
            })

            for rank, result in enumerate(results, start=1):

                job_id = result["job_id"]
                score = float(result["semantic_score"])

                retrieval_evidence = {
                    "query_type": query_type,
                    "query": query,
                    "rank": rank,
                    "semantic_score": score,
                    "best_matching_section": result[
                        "best_matching_section"
                    ],
                    "matched_chunks": result[
                        "matched_chunks"
                    ],
                }

                if job_id not in candidates:

                    candidates[job_id] = {
                        "job_id": job_id,
                        "job_title": result["job_title"],
                        "company": result["company"],
                        "location": result["location"],
                        "domain": result["domain"],
                        "work_mode": result["work_mode"],

                        "semantic_score": score,

                        "best_matching_section": result[
                            "best_matching_section"
                        ],

                        "matched_chunks": result[
                            "matched_chunks"
                        ],

                        "best_query_type": query_type,

                        "retrieval_evidence": [],

                        "job": result["job"],
                    }

                candidate = candidates[job_id]

                candidate["retrieval_evidence"].append(
                    retrieval_evidence
                )

                # Preserve the strongest semantic match
                if score > candidate["semantic_score"]:

                    candidate["semantic_score"] = score

                    candidate["best_matching_section"] = (
                        result["best_matching_section"]
                    )

                    candidate["matched_chunks"] = (
                        result["matched_chunks"]
                    )

                    candidate["best_query_type"] = (
                        query_type
                    )

        # Calculate retrieval coverage for each internship
        for candidate in candidates.values():

            candidate["query_count"] = len({
                evidence["query_type"]
                for evidence in candidate[
                    "retrieval_evidence"
                ]
            })

            candidate["matched_query_types"] = list(
                dict.fromkeys(
                    evidence["query_type"]
                    for evidence in candidate[
                        "retrieval_evidence"
                    ]
                )
            )

        # Rank candidates by semantic relevance
        ranked_candidates = sorted(
            candidates.values(),
            key=lambda item: (
                -item["semantic_score"],
                -item["query_count"],
                item["job_id"],
            ),
        )

        selected_candidates = ranked_candidates[
            :max_candidates
        ]

        return {
            "queries": queries,

            "retrieval_statistics": {
                "total_queries": len(queries),
                "total_retrieved": total_retrieved,
                "unique_candidates": len(candidates),
                "duplicates_removed": (
                    total_retrieved - len(candidates)
                ),
                "returned_candidates": len(
                    selected_candidates
                ),
                "top_k_per_query": top_k_per_query,
                "query_statistics": query_statistics,
            },

            "candidates": selected_candidates,
        }