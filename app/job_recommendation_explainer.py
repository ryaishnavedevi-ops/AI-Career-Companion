from copy import deepcopy


def generate_recommendation_explanation(item):
    """Generate evidence-backed internship explanations."""

    if not isinstance(item, dict):
        raise ValueError(
            "Ranked recommendation must be a dictionary."
        )

    components = item["comparison"]["components"]

    required = components["required_skills"]
    preferred = components["preferred_skills"]
    education = components["education"]
    experience = components["experience"]
    projects = components["projects"]

    technical = item["technical_assessment"]

    strengths = []
    skill_gaps = []
    improvement_priorities = []
    warnings = []

    # Required skill evidence

    matched_required = required.get(
        "matched_skills", []
    )

    missing_required = required.get(
        "missing_skills", []
    )

    if matched_required:

        strengths.append({
            "component": "required_skills",
            "message": (
                "Resume evidence matches extracted "
                "required skills: "
                + ", ".join(matched_required)
                + "."
            ),
            "evidence": deepcopy(
                required.get("matched_evidence", [])
            )
        })

    if missing_required:

        skill_gaps.append({
            "priority": "high",
            "category": "required_skills",
            "skills": missing_required.copy(),
            "message": (
                "The resume does not currently "
                "provide recognized evidence for "
                "these extracted required skills."
            )
        })

        improvement_priorities.append({
            "priority": "high",
            "action": (
                "Develop or document evidence for "
                "the unmatched required skills."
            ),
            "skills": missing_required.copy()
        })

    # Preferred skill evidence

    matched_preferred = preferred.get(
        "matched_skills", []
    )

    missing_preferred = preferred.get(
        "missing_skills", []
    )

    if matched_preferred:

        strengths.append({
            "component": "preferred_skills",
            "message": (
                "Resume evidence also matches "
                "preferred skills: "
                + ", ".join(matched_preferred)
                + "."
            ),
            "evidence": deepcopy(
                preferred.get("matched_evidence", [])
            )
        })

    if missing_preferred:

        skill_gaps.append({
            "priority": "medium",
            "category": "preferred_skills",
            "skills": missing_preferred.copy(),
            "message": (
                "These preferred skills could "
                "strengthen the application."
            )
        })

        improvement_priorities.append({
            "priority": "medium",
            "action": (
                "Consider developing relevant "
                "preferred skills."
            ),
            "skills": missing_preferred.copy()
        })

    # Education and experience evidence

    for name, component in [
        ("education", education),
        ("experience", experience)
    ]:

        evidence = component.get(
            "matched_evidence", []
        )

        if evidence:

            status = component.get("status")

            if status == "matched":

                message = (
                    f"Recognized {name} evidence "
                    "aligns with the extracted requirement."
                )

            else:

                message = (
                    f"Relevant {name} evidence was found, "
                    "but full alignment remains unverified."
                )

            strengths.append({
                "component": name,
                "message": message,
                "evidence": deepcopy(evidence)
            })

    # Practical project evidence

    matched_activities = projects.get(
        "matched_activities", []
    )

    unmatched_activities = projects.get(
        "unmatched_activities", []
    )

    if matched_activities:

        strengths.append({
            "component": "projects",
            "message": (
                "Project descriptions support "
                "recognized job activities: "
                + ", ".join(matched_activities)
                + "."
            ),
            "evidence": deepcopy(
                projects.get("matched_evidence", [])
            )
        })

    if unmatched_activities:

        improvement_priorities.append({
            "priority": "medium",
            "action": (
                "Build or document practical "
                "project evidence for these activities."
            ),
            "activities": unmatched_activities.copy()
        })

    # Technical information limitations

    if technical["status"] == (
        "insufficient_technical_requirements"
    ):

        warnings.append({
            "type": "insufficient_technical_information",
            "message": (
                "No extracted technical required or "
                "preferred skills are available. "
                "Technical compatibility cannot be "
                "established confidently."
            )
        })

    elif technical["status"] == (
        "technical_preferred_only"
    ):

        warnings.append({
            "type": "limited_required_technical_information",
            "message": (
                "Technical skills are available only "
                "as preferred requirements. "
                "Mandatory technical alignment "
                "remains uncertain."
            )
        })

    # Unresolved comparison components

    for name, component in components.items():

        if (
            component.get("match_ratio") is None
            and component.get("status")
            != "not_specified"
        ):

            warnings.append({
                "type": "unresolved_component",
                "component": name,
                "message": (
                    component.get("reason")
                    or f"{name} alignment remains uncertain."
                )
            })

    # Eligibility verification

    eligibility_reviews = deepcopy(
        item.get("eligibility_review", [])
    )

    if eligibility_reviews:

        improvement_priorities.insert(0, {
            "priority": "verification",
            "action": (
                "Verify unresolved eligibility "
                "requirements before applying."
            ),
            "constraints": list(dict.fromkeys(
                constraint
                for review in eligibility_reviews
                for constraint in review.get(
                    "constraints", []
                )
            ))
        })

    # Summary reasoning

    if strengths:

        summary = (
            "The internship was retrieved as a "
            "potentially relevant opportunity and "
            "ranked using available resume-job "
            "matching evidence."
        )

    else:

        summary = (
            "The internship was retrieved as a "
            "potentially relevant opportunity, "
            "but supporting structured matching "
            "evidence is limited."
        )

    if technical["ranking_factor"] < 1.0:

        summary += (
            " Its ranking was adjusted because "
            "technical requirement information "
            "is limited."
        )

    if eligibility_reviews:

        summary += (
            " Eligibility requires further "
            "verification."
        )

    return {
        "job_id": item["job_id"],
        "rank": item["rank"],
        "summary": summary,
        "strengths": strengths,
        "skill_gaps": skill_gaps,
        "improvement_priorities":
            improvement_priorities,
        "warnings": warnings,
        "eligibility_review_required":
            bool(eligibility_reviews),
        "eligibility_reviews":
            eligibility_reviews,
        "score_explanation": {
            "compatibility_score":
                item["compatibility_score"],
            "base_ranking_score":
                item["base_ranking_score"],
            "ranking_score":
                item["ranking_score"],
            "evidence_coverage":
                item["evidence_coverage"],
            "technical_evidence_factor":
                technical["ranking_factor"],
            "technical_requirement_status":
                technical["status"],
            "semantic_score":
                item["semantic_score"],
            "score_breakdown": deepcopy(
                item["score_breakdown"]
            )
        }
    }


def attach_recommendation_explanations(result):
    """Attach explanations without modifying the input."""

    explained_result = deepcopy(result)

    for item in explained_result["recommendations"]:

        item["explanation"] = (
            generate_recommendation_explanation(item)
        )

    return explained_result