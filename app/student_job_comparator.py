from app.job_resume_matcher import match_job_skills
from app.job_education_matcher import match_job_education
from app.job_experience_matcher import match_job_experience
from app.job_project_matcher import match_job_projects


def compare_student_job(
    profile,
    job,
    reference_year=None,
):
    """Combine all student-job matching components."""

    if not isinstance(profile, dict):
        raise ValueError(
            "Student profile must be a dictionary."
        )

    if not isinstance(job, dict):
        raise ValueError(
            "Job posting must be a dictionary."
        )

    skill_result = match_job_skills(
        profile,
        job
    )

    education_result = match_job_education(
        profile,
        job,
        reference_year=reference_year
    )

    experience_result = match_job_experience(
        profile,
        job
    )

    project_result = match_job_projects(
        profile,
        job
    )

    components = {
        "required_skills":
            skill_result["required_skills"],

        "preferred_skills":
            skill_result["preferred_skills"],

        "education":
            education_result,

        "experience":
            experience_result,

        "projects":
            project_result,
    }

    component_ratios = {
        name: result.get("match_ratio")
        for name, result in components.items()
    }

    component_statuses = {
        name: result.get("status")
        for name, result in components.items()
    }

    evaluated_components = [
        name
        for name, ratio in component_ratios.items()
        if ratio is not None
    ]

    unspecified_components = [
        name
        for name, status in component_statuses.items()
        if status == "not_specified"
    ]

    unresolved_components = [
        name
        for name, ratio in component_ratios.items()
        if ratio is None
        and name not in unspecified_components
    ]

    comparison_summary = {
        "total_components": len(components),

        "evaluated_count":
            len(evaluated_components),

        "unspecified_count":
            len(unspecified_components),

        "unresolved_count":
            len(unresolved_components),

        "evaluated_components":
            evaluated_components,

        "unspecified_components":
            unspecified_components,

        "unresolved_components":
            unresolved_components,

        "component_ratios":
            component_ratios,

        "component_statuses":
            component_statuses,

        "evaluation_coverage": (
            len(evaluated_components)
            / len(components)
        ),
    }

    return {
        "candidate_id": profile.get("candidate_id"),
        "resume_id": profile.get("resume_id"),

        "job_id": job.get("job_id"),
        "job_title": job.get("job_title"),
        "company": job.get("company"),
        "domain": job.get("domain"),
        "location": job.get("location"),
        "work_mode": job.get("work_mode"),

        "components": components,

        "comparison_summary": comparison_summary,
    }