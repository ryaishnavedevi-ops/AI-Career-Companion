import math


COMPONENT_WEIGHTS = {
    "required_skills": 40,
    "preferred_skills": 10,
    "education": 15,
    "experience": 15,
    "projects": 10,
    "semantic_relevance": 10,
}


def validate_ratio(ratio):
    """Validate a numeric matching ratio."""

    if ratio is None:
        return

    if (
        isinstance(ratio, bool)
        or not isinstance(ratio, (int, float))
        or not math.isfinite(ratio)
        or not 0.0 <= ratio <= 1.0
    ):
        raise ValueError(
            f"Invalid matching ratio: {ratio}"
        )


def calculate_compatibility(
    comparison,
    semantic_score=None,
):
    """Calculate compatibility and evidence-aware ranking."""

    if not isinstance(comparison, dict):
        raise ValueError(
            "Comparison must be a dictionary."
        )

    components = comparison["components"]

    if semantic_score is not None:

        if (
            isinstance(semantic_score, bool)
            or not isinstance(
                semantic_score, (int, float)
            )
            or not math.isfinite(semantic_score)
            or not -1.0 <= semantic_score <= 1.0
        ):
            raise ValueError(
                "Invalid semantic similarity score."
            )

        semantic_ratio = max(
            0.0, semantic_score
        )

    else:
        semantic_ratio = None

    scoring_components = {
        **components,

        "semantic_relevance": {
            "status": (
                "evaluated"
                if semantic_ratio is not None
                else "not_specified"
            ),
            "match_ratio": semantic_ratio,
        },
    }

    earned_weight = 0.0
    evaluated_weight = 0.0
    applicable_weight = 0.0
    unspecified_weight = 0.0
    unresolved_weight = 0.0

    breakdown = {}

    for name, weight in COMPONENT_WEIGHTS.items():

        component = scoring_components[name]

        ratio = component.get("match_ratio")
        status = component.get("status")

        validate_ratio(ratio)

        if status == "not_specified" and ratio is not None:

            raise ValueError(
                f"Unspecified component has a ratio: {name}"
            )

        contribution = None

        if status == "not_specified":

            scoring_status = "not_specified"
            unspecified_weight += weight

        elif ratio is None:

            scoring_status = "unresolved"

            applicable_weight += weight
            unresolved_weight += weight

        else:

            scoring_status = "evaluated"

            applicable_weight += weight
            evaluated_weight += weight

            contribution = weight * ratio

            earned_weight += contribution

        breakdown[name] = {
            "weight": weight,
            "original_status": status,
            "scoring_status": scoring_status,
            "match_ratio": ratio,
            "weighted_contribution": contribution,
        }

    compatibility_score = (
        earned_weight / evaluated_weight * 100
        if evaluated_weight > 0
        else None
    )

    evidence_coverage = (
        evaluated_weight / applicable_weight
        if applicable_weight > 0
        else None
    )

    ranking_score = (
        earned_weight / applicable_weight * 100
        if applicable_weight > 0
        and evaluated_weight > 0
        else None
    )

    eligibility_review = []

    mandatory_eligibility_mismatch = (
        components["education"].get(
            "mandatory_requirement"
        ) is True
        and components["education"].get(
            "confirmed_degree_mismatch"
        ) is True
        and components["education"].get(
            "status"
        ) == "mismatch"
    )

    for name in ["education", "experience"]:

        status = breakdown[name]["scoring_status"]

        if (
            status == "unresolved"
            or components[name].get("status") == "mismatch"
        ):

            eligibility_review.append({
                "component": name,
                "status": components[name]["status"],
                "constraints": components[name].get(
                    "unresolved_constraints", []
                ),
                "reason": components[name].get(
                    "reason"
                ),
            })

    return {
        "job_id": comparison.get("job_id"),
        "job_title": comparison.get("job_title"),
        "company": comparison.get("company"),

        "compatibility_score": compatibility_score,

        "ranking_score": ranking_score,

        "evidence_coverage": evidence_coverage,

        "semantic_score": semantic_score,

        "mandatory_eligibility_mismatch":
            mandatory_eligibility_mismatch,

        "eligibility_review_required": bool(
            eligibility_review
        ),

        "eligibility_review": eligibility_review,

        "weight_summary": {
            "total_weight": sum(
                COMPONENT_WEIGHTS.values()
            ),

            "earned_weight": earned_weight,

            "evaluated_weight": evaluated_weight,

            "applicable_weight": applicable_weight,

            "unspecified_weight": unspecified_weight,

            "unresolved_weight": unresolved_weight,
        },

        "score_breakdown": breakdown,
    }