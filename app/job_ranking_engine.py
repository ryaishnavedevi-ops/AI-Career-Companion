from app.job_retrieval_config import (
    DEFAULT_TOP_K_PER_QUERY,
    DEFAULT_MAX_CANDIDATES,
)

from app.student_job_comparator import compare_student_job
from app.job_compatibility_scorer import calculate_compatibility

from app.job_matching_refinement import (
    enrich_student_profile,
    refine_job_scoring
)

from app.job_recommendation_explainer import (
    attach_recommendation_explanations
)


def sortable_value(value):
    """Place unavailable numeric values below valid values."""

    return value if value is not None else float("-inf")


def ranking_sort_key(item):
    """Provide deterministic internship ranking."""

    return (
        bool(item.get(
            "mandatory_eligibility_mismatch", False
        )),

        -sortable_value(item["ranking_score"]),

        -sortable_value(item["evidence_coverage"]),

        -sortable_value(
            item["required_skill_match_ratio"]
        ),

        -sortable_value(item["compatibility_score"]),

        -sortable_value(item["semantic_score"]),

        str(item["job_id"]),
    )


def rank_job_candidates(
    profile,
    candidates,
    top_k=10,
    reference_year=None,
):
    """Compare, score and rank retrieved internship candidates."""

    if not isinstance(profile, dict):
        raise ValueError(
            "Student profile must be a dictionary."
        )

    if not isinstance(candidates, list):
        raise ValueError(
            "Candidates must be a list."
        )

    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or top_k <= 0
    ):
        raise ValueError(
            "top_k must be a positive integer."
        )

    profile = enrich_student_profile(profile)

    ranked_jobs = []
    seen_job_ids = set()

    for candidate in candidates:

        job = candidate["job"]
        job_id = job.get("job_id")

        if not job_id:
            raise ValueError(
                "Candidate job ID is missing."
            )

        if job_id in seen_job_ids:
            raise ValueError(
                f"Duplicate candidate job ID: {job_id}"
            )

        seen_job_ids.add(job_id)

        semantic_score = candidate.get(
            "semantic_score"
        )

        comparison = compare_student_job(
            profile,
            job,
            reference_year=reference_year
        )

        scoring = calculate_compatibility(
            comparison,
            semantic_score=semantic_score
        )

        scoring = refine_job_scoring(
            scoring,
            job,
            comparison=comparison
        )

        required_skills = comparison[
            "components"
        ]["required_skills"]

        ranked_jobs.append({
            "job_id": job_id,

            "job_title": job.get("job_title"),

            "company": job.get("company"),

            "location": job.get("location"),

            "domain": job.get("domain"),

            "work_mode": job.get("work_mode"),

            "compatibility_score":
                scoring["compatibility_score"],

            "ranking_score":
                scoring["ranking_score"],

            "base_ranking_score":
                scoring["base_ranking_score"],

            "technical_assessment":
                scoring["technical_assessment"],

            "evidence_coverage":
                scoring["evidence_coverage"],

            "semantic_score":
                scoring["semantic_score"],

            "required_skill_match_ratio":
                required_skills["match_ratio"],

            "matched_required_skills":
                required_skills["matched_skills"],

            "missing_required_skills":
                required_skills["missing_skills"],

            "mandatory_eligibility_mismatch":
                scoring["mandatory_eligibility_mismatch"],

            "eligibility_review_required":
                scoring["eligibility_review_required"],

            "eligibility_review":
                scoring["eligibility_review"],

            "score_breakdown":
                scoring["score_breakdown"],

            "weight_summary":
                scoring["weight_summary"],

            "comparison":
                comparison,

            "retrieval_evidence":
                candidate.get("retrieval_evidence", []),

            "best_matching_section":
                candidate.get("best_matching_section"),

            "matched_chunks":
                candidate.get("matched_chunks", []),

            "query_count":
                candidate.get("query_count"),

            "job": job,
        })

    ranked_jobs.sort(
        key=ranking_sort_key
    )

    for rank, item in enumerate(
        ranked_jobs,
        start=1
    ):
        item["rank"] = rank

    recommendations = ranked_jobs[:top_k]

    return {
        "candidate_id": profile.get("candidate_id"),

        "resume_id": profile.get("resume_id"),

        "ranking_statistics": {
            "total_candidates": len(candidates),

            "total_ranked": len(ranked_jobs),

            "scored_candidates": sum(
                item["ranking_score"] is not None
                for item in ranked_jobs
            ),

            "unscored_candidates": sum(
                item["ranking_score"] is None
                for item in ranked_jobs
            ),

            "mandatory_eligibility_mismatch_count": sum(
                item["mandatory_eligibility_mismatch"]
                for item in ranked_jobs
            ),

            "eligibility_review_count": sum(
                item["eligibility_review_required"]
                for item in ranked_jobs
            ),

            "returned_recommendations":
                len(recommendations),

            "requested_top_k": top_k,
        },

        "recommendations": recommendations,
    }


class InternshipRecommendationEngine:

    def __init__(self, candidate_retriever=None):

        if candidate_retriever is None:

            from app.job_candidate_retriever import (
                JobCandidateRetriever
            )

            candidate_retriever = JobCandidateRetriever()

        self.candidate_retriever = candidate_retriever

    def recommend(
        self,
        profile,
        top_k=10,
        top_k_per_query=DEFAULT_TOP_K_PER_QUERY,
        max_candidates=DEFAULT_MAX_CANDIDATES,
        reference_year=None,
    ):
        """Retrieve relevant internships and rank compatibility."""

        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k <= 0
        ):
            raise ValueError(
                "top_k must be a positive integer."
            )

        retrieval = self.candidate_retriever.retrieve_candidates(
            profile,
            top_k_per_query=top_k_per_query,
            max_candidates=max_candidates
        )

        ranking = rank_job_candidates(
            profile,
            retrieval["candidates"],
            top_k=top_k,
            reference_year=reference_year
        )

        result = {
            **ranking,
            "queries": retrieval["queries"],
            "retrieval_statistics":
            retrieval["retrieval_statistics"]
            }
        return attach_recommendation_explanations(
            result
        )