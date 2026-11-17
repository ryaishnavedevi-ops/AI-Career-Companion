import { useEffect, useState } from "react";

import {
  BrainCircuit,
  GraduationCap,
  BriefcaseBusiness,
  FolderKanban,
  Award,
  Trophy,
  Languages,
  FileSearch,
} from "lucide-react";

const sections = [
  { key: "skills", title: "Skills", icon: BrainCircuit },
  { key: "education", title: "Education", icon: GraduationCap },
  { key: "experience", title: "Experience", icon: BriefcaseBusiness },
  { key: "projects", title: "Projects", icon: FolderKanban },
  { key: "certifications", title: "Certifications", icon: Award },
  { key: "awards", title: "Awards & Achievements", icon: Trophy },
  { key: "languages", title: "Languages", icon: Languages },
];

export default function Skills() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const resumeId = localStorage.getItem("resume_id");

    if (!resumeId) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadExtraction() {
      try {
        const response = await fetch(`/api/resumes/extracted/${resumeId}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Unable to retrieve your resume analysis.");
        }

        const result = await response.json();

        setData({
          ...result.extracted_data,
          project_records: result.project_records ?? [],
          experience_records: result.experience_records ?? [],
          education_records: result.education_records ?? [],
          award_records: result.award_records ?? [],
        });
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Failed to load analysis.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadExtraction();

    return () => controller.abort();
  }, []);

  if (loading) {
    return (
      <div role="status" className="p-8 text-slate-500">
        Loading your resume analysis...
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="rounded-xl bg-red-50 p-6 text-red-700">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl rounded-3xl border border-slate-200 bg-white px-6 py-16 text-center shadow-sm">
        <FileSearch size={42} className="mx-auto mb-5 text-violet-500" />
        <h2 className="text-2xl font-bold text-slate-900">
          No resume analysis yet
        </h2>
        <p className="mt-3 text-slate-500">
          Upload and analyze your resume first to explore your skills and
          experience.
        </p>
      </div>
    );
  }

  const totalItems = sections.reduce(
    (total, section) =>
      total + (Array.isArray(data[section.key]) ? data[section.key].length : 0),
    0,
  );

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-8">
        <div className="mb-4 inline-flex rounded-2xl bg-violet-100 p-4 text-violet-600">
          <BrainCircuit size={30} />
        </div>

        <h2 className="text-3xl font-bold text-slate-900">
          Your career profile
        </h2>

        <p className="mt-2 text-slate-500">
          Explore the information extracted from your resume.
        </p>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Extracted items</p>
          <p className="mt-2 text-3xl font-bold text-violet-600">
            {totalItems}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Skills entries</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {Array.isArray(data.skills) ? data.skills.length : 0}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Projects identified</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {Array.isArray(data.project_records) &&
            data.project_records.length > 0
              ? data.project_records.length
              : "—"}
          </p>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {sections.map((section) => {
          const Icon = section.icon;
          const items = Array.isArray(data[section.key])
            ? data[section.key]
            : [];

          return (
            <div
              key={section.key}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="mb-5 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-violet-50 p-3 text-violet-600">
                    <Icon size={22} />
                  </div>

                  <h3 className="font-bold text-slate-900">{section.title}</h3>
                </div>

                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  {section.key === "awards" && data.award_records?.length > 0
                    ? data.award_records.length
                    : section.key === "education" &&
                        data.education_records?.length > 0
                      ? data.education_records.length
                      : section.key === "experience" &&
                          data.experience_records?.length > 0
                        ? data.experience_records.length
                        : section.key === "projects" &&
                            data.project_records?.length > 0
                          ? data.project_records.length
                          : items.length}
                </span>
              </div>

              {section.key === "awards" &&
              Array.isArray(data.award_records) &&
              data.award_records.length > 0 ? (
                <div className="space-y-3">
                  {data.award_records.map((award, index) => (
                    <div
                      key={index}
                      className="rounded-xl border border-violet-100 bg-violet-50/40 p-4"
                    >
                      <p className="text-sm leading-6 text-slate-700">
                        {award.description}
                      </p>
                    </div>
                  ))}
                </div>
              ) : null}

              {section.key === "education" &&
              Array.isArray(data.education_records) &&
              data.education_records.length > 0 ? (
                <div className="space-y-4">
                  {data.education_records.map((education, index) => (
                    <div
                      key={`${education.institution}-${index}`}
                      className="rounded-2xl border border-violet-100 bg-violet-50/40 p-5"
                    >
                      <h4 className="text-lg font-bold text-slate-900">
                        {education.qualification}
                      </h4>

                      <p className="mt-2 font-medium text-violet-600">
                        {education.institution}
                      </p>

                      <p className="mt-3 text-sm text-slate-500">
                        {education.dates}
                      </p>

                      <p className="mt-2 text-sm font-semibold text-slate-700">
                        {education.result}
                      </p>
                    </div>
                  ))}
                </div>
              ) : null}

              {section.key === "awards" &&
              Array.isArray(data.award_records) &&
              data.award_records.length > 0 ? null : section.key ===
                  "education" &&
                Array.isArray(data.education_records) &&
                data.education_records.length > 0 ? null : section.key ===
                  "experience" &&
                Array.isArray(data.experience_records) &&
                data.experience_records.length > 0 ? (
                <div className="space-y-4">
                  {data.experience_records.map((experience, index) => (
                    <div
                      key={`${experience.company}-${index}`}
                      className="rounded-2xl border border-violet-100 bg-violet-50/40 p-5"
                    >
                      <h4 className="text-lg font-bold text-slate-900">
                        {experience.role}
                      </h4>

                      <p className="mt-1 font-medium text-violet-600">
                        {experience.company}
                      </p>

                      <div className="mt-3 space-y-1 text-sm text-slate-500">
                        <p>{experience.details}</p>
                        <p>{experience.duration}</p>
                      </div>

                      <ul className="mt-4 list-disc space-y-2 pl-5">
                        {(experience.responsibilities ?? []).map(
                          (responsibility, responsibilityIndex) => (
                            <li
                              key={responsibilityIndex}
                              className="text-sm leading-6 text-slate-600"
                            >
                              {responsibility}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : section.key === "projects" &&
                Array.isArray(data.project_records) &&
                data.project_records.length > 0 ? (
                <div className="space-y-4">
                  {data.project_records.map((project, index) => (
                    <div
                      key={`${project.title}-${index}`}
                      className="rounded-2xl border border-violet-100 bg-violet-50/40 p-5"
                    >
                      <h4 className="text-lg font-bold text-slate-900">
                        {project.title}
                      </h4>

                      <p className="mt-1 text-sm font-medium text-violet-600">
                        {project.category}
                      </p>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {(project.technologies ?? []).map((tech, techIndex) => (
                          <span
                            key={techIndex}
                            className="rounded-lg bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-sm"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>

                      <ul className="mt-4 space-y-2">
                        {(project.description ?? []).map(
                          (description, descIndex) => (
                            <li
                              key={descIndex}
                              className="text-sm leading-6 text-slate-600"
                            >
                              {description}
                            </li>
                          ),
                        )}
                      </ul>

                      {project.link && (
                        <p className="mt-4 text-xs text-slate-500">
                          Project reference: {project.link}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : items.length === 0 ? (
                <p className="text-sm text-slate-400">
                  No information found in this section.
                </p>
              ) : (
                <ul className="space-y-3">
                  {items.map((item, index) => (
                    <li
                      key={index}
                      className="rounded-xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700"
                    >
                      {typeof item === "string" ? item : JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>

      <p className="mt-6 text-sm text-slate-400">
        Extracted information may require review. Check it against your original
        resume before using it in applications.
      </p>
    </div>
  );
}
