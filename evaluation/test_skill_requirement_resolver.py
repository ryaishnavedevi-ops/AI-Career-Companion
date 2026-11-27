import json
from copy import deepcopy
from pathlib import Path

from app.job_skill_requirement_resolver import (
    resolve_skill_requirements
)


ROOT = Path(__file__).resolve().parents[1]

with open(
    ROOT / "data/internships.json",
    encoding="utf-8-sig"
) as f:
    jobs = json.load(f)

soc_job = next(
    job for job in jobs
    if job["job_title"] == "SOC Analyst Internship"
    and "360 SOC" in job["company"]
)

checks = []


def check(name, condition):
    checks.append(bool(condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


def resolve(required, qualifications, preferred=None, **extra):

    return resolve_skill_requirements({
        "required_skills": required,
        "preferred_skills": preferred or [],
        "qualifications": qualifications,
        **extra
    })


print("\n========== CERTIFICATION REGRESSION TESTS ==========")

result = resolve(
    ["Linux", "CCNA", "CompTIA Security+"],
    [
        "Willing to work towards industry certifications "
        "such as CCNA and Security+."
    ]
)

check(
    "Future CCNA removed",
    "CCNA" not in result["required_skills"]
)

check(
    "Future Security+ removed",
    "CompTIA Security+" not in result["required_skills"]
)

check(
    "Unrelated Linux requirement preserved",
    "Linux" in result["required_skills"]
)

result = resolve(
    ["CCNA"],
    ["Must have CCNA certification."]
)

check(
    "Mandatory certification preserved",
    "CCNA" in result["required_skills"]
)

result = resolve(
    ["CCNA"],
    [
        "Willing to work towards certifications such as CCNA.",
        "Current CCNA certification is required."
    ]
)

check(
    "Independent mandatory certification preserved",
    "CCNA" in result["required_skills"]
)

result = resolve(
    ["CCNA"],
    ["Willing to work towards certifications such as CCNA."],
    experience_requirements="Current CCNA certification required."
)

check(
    "Certification required in another field preserved",
    "CCNA" in result["required_skills"]
)

result = resolve(
    [],
    ["Willing to pursue certifications such as CCNA."],
    preferred=["CCNA"]
)

check(
    "Future preferred certification removed",
    "CCNA" not in result["preferred_skills"]
)

result = resolve(
    ["CCNA"],
    [
        "Willing to work towards certifications such as CCNA. "
        "Current CCNA certification is required."
    ]
)

check(
    "Previously failed mixed certification case fixed",
    "CCNA" in result["required_skills"]
)


print("\n========== PROGRAMMING REGRESSION TESTS ==========")

result = resolve(
    ["Linux", "Scripting"],
    ["Must have at least one programming or scripting language."]
)

check(
    "Programming alternative added",
    "Programming" in result["required_skills"]
)

check(
    "Scripting alternative preserved",
    "Scripting" in result["required_skills"]
)

check(
    "Correct any-of group generated",
    any(
        set(group["skills"]) == {"Programming", "Scripting"}
        for group in result["required_alternative_groups"]
    )
)

result = resolve(
    ["Scripting"],
    ["Scripting experience is required."]
)

check(
    "Independent scripting requirement unchanged",
    result["required_skills"] == ["Scripting"]
    and not result["required_alternative_groups"]
)

result = resolve(
    ["Scripting"],
    [
        "Must have at least one programming or scripting language.",
        "Scripting experience is independently required."
    ]
)

check(
    "Independent scripting requirement not weakened",
    not result["required_alternative_groups"]
)

result = resolve(
    ["Scripting"],
    [
        "Must have at least one programming or scripting language. "
        "Scripting experience is independently required."
    ]
)

check(
    "Previously failed same-line scripting case fixed",
    not result["required_alternative_groups"]
)


print("\n========== ADDITIONAL BOUNDARY TESTS ==========")

result = resolve(
    ["CCNA"],
    [
        "Willing to work towards certifications such as CCNA; "
        "current CCNA certification is required."
    ]
)

check(
    "Semicolon-separated mandatory certification preserved",
    "CCNA" in result["required_skills"]
)

result = resolve(
    ["CCNA"],
    [
        "Willing to work towards certifications such as CCNA "
        "but current CCNA certification is mandatory."
    ]
)

check(
    "Ambiguous mixed certification clause preserved",
    "CCNA" in result["required_skills"]
)

result = resolve(
    ["Scripting"],
    [
        "Must have at least one programming or scripting language; "
        "additional scripting experience is required."
    ]
)

check(
    "Semicolon-separated scripting requirement preserved",
    not result["required_alternative_groups"]
)

result = resolve(
    ["Scripting"],
    [
        "Must have at least one programming or scripting language "
        "and additional scripting experience is required."
    ]
)

check(
    "Same-clause independent scripting requirement preserved",
    not result["required_alternative_groups"]
)

result = resolve(
    ["CCNA", "Python"],
    []
)

check(
    "Missing qualifications preserve original requirements",
    result["required_skills"] == ["CCNA", "Python"]
    and not result["adjustments"]
)

result = resolve([], [])

check(
    "Empty requirements handled safely",
    not result["required_skills"]
    and not result["preferred_skills"]
    and not result["adjustments"]
)

result = resolve(
    ["Scripting"],
    ["Must have at least one programming or scripting language."],
    experience_requirements="Independent scripting experience required."
)

check(
    "Independent scripting in experience field preserved",
    not result["required_alternative_groups"]
)

result = resolve(
    ["Scripting"],
    [
        "At least one programming or scripting language "
        "is preferred but not required."
    ]
)

check(
    "Preferred-only language does not create mandatory alternative",
    not result["required_alternative_groups"]
)


print("\n========== ACTUAL SOC INTERNSHIP REGRESSION ==========")

original = deepcopy(soc_job)

result = resolve_skill_requirements(soc_job)

check(
    "Original job data unchanged",
    soc_job == original
)

check(
    "SOC future certifications excluded",
    "CCNA" not in result["required_skills"]
    and "CompTIA Security+" not in result["required_skills"]
)

check(
    "SOC programming alternative recovered",
    any(
        set(group["skills"]) == {"Programming", "Scripting"}
        for group in result["required_alternative_groups"]
    )
)

check(
    "SOC cybersecurity requirement preserved",
    "Cybersecurity" in result["required_skills"]
)

check(
    "SOC preferred skills unchanged",
    result["preferred_skills"] == soc_job["preferred_skills"]
)

print("\n========== SUMMARY ==========")
print(f"Passed: {sum(checks)}/{len(checks)}")
print(f"Failed: {len(checks) - sum(checks)}")

raise SystemExit(0 if all(checks) else 1)
