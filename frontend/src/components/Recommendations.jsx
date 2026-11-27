import { useState, useEffect, useRef } from "react";

import {
  BriefcaseBusiness,
  Sparkles,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  MapPin,
  ChevronDown,
  Info,
  Target,
  TrendingUp,
  FileSearch,
} from "lucide-react";


function formatScore(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${value.toFixed(1)}%`
    : "Not evaluated";
}


function formatLabel(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


function ScoreDisplay({ label, value, color }) {
  const available =
    typeof value === "number" && Number.isFinite(value);

  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold text-slate-900">
        {formatScore(value)}
      </p>

      {available && (
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
          <div
            className={`h-full rounded-full ${color}`}
            style={{
              width: `${Math.max(0, Math.min(100, value))}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}


function SkillChips({ skills = [], variant = "matched" }) {
  const color =
    variant === "matched"
      ? "bg-emerald-50 text-emerald-700"
      : "bg-amber-50 text-amber-700";

  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((skill, index) => (
        <span
          key={`${skill}-${index}`}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${color}`}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}


function RecommendationCard({ item }) {
  const explanation = item.explanation ?? {};

  const strengths = explanation.strengths ?? [];
  const skillGaps = explanation.skill_gaps ?? [];
  const priorities = explanation.improvement_priorities ?? [];
  const warnings = explanation.warnings ?? [];
  const eligibilityReviews = explanation.eligibility_reviews ?? [];

  const requirementNotes = explanation.requirement_notes ?? [];
  const scoreExplanation = explanation.score_explanation ?? {};

  const requiredTechnical =
    scoreExplanation.required_technical_alignment;

  const preferredTechnical =
    scoreExplanation.preferred_technical_alignment;

  const technicalFactor =
    scoreExplanation.technical_evidence_factor;

  const mandatoryMismatch =
    item.mandatory_eligibility_mismatch === true ||
    explanation.mandatory_eligibility_mismatch === true;

  const [expanded, setExpanded] = useState(false);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:p-6">

      {/* Internship information */}

      <div className="flex items-start gap-4">

        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
          {item.company?.charAt(0) || "I"}
        </div>

        <div className="min-w-0 flex-1">

          <p className="text-xs font-semibold text-violet-600">
            Rank #{item.rank}
          </p>

          <h3 className="mt-1 text-lg font-bold text-slate-900">
            {item.job_title}
          </h3>

          <p className="mt-1 font-medium text-slate-600">
            {item.company}
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">

            {item.location && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={14} />
                {item.location}
              </span>
            )}

            {item.work_mode && (
              <span className="rounded-md bg-slate-100 px-2 py-1">
                {item.work_mode}
              </span>
            )}

            {item.domain && (
              <span className="rounded-md bg-violet-50 px-2 py-1 text-violet-700">
                {item.domain}
              </span>
            )}

          </div>
        </div>
      </div>


      {/* Matching scores */}

      <div className="mt-5 grid gap-3 sm:grid-cols-2">

        <ScoreDisplay
          label="Compatibility score"
          value={item.compatibility_score}
          color="bg-emerald-500"
        />

        <ScoreDisplay
          label="Ranking score"
          value={item.ranking_score}
          color="bg-violet-500"
        />

      </div>

      <p className="mt-3 text-xs text-slate-500">
        Evidence coverage:{" "}
        {formatScore(
          typeof item.evidence_coverage === "number"
            ? item.evidence_coverage * 100
            : null
        )}
      </p>


      {/* Matched required skills */}

      <div className="mt-5">

        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
          <CheckCircle2 size={17} className="text-emerald-600" />
          Matched required skills
        </h4>

        {item.matched_required_skills?.length > 0 ? (
          <SkillChips skills={item.matched_required_skills} />
        ) : (
          <p className="text-sm text-slate-500">
            No recognized required skill matches available.
          </p>
        )}

      </div>


      {/* Eligibility warning */}

      {mandatoryMismatch && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4">

          <AlertCircle
            size={19}
            className="mt-0.5 shrink-0 text-red-600"
          />

          <div>
            <p className="text-sm font-semibold text-red-800">
              Mandatory education mismatch
            </p>

            <p className="mt-1 text-xs leading-5 text-red-700">
              Recorded education does not meet the identified
              mandatory degree requirement. This internship is
              deprioritized regardless of its numeric ranking score.
              Verify the original posting before applying.
            </p>
          </div>

        </div>
      )}

      {item.eligibility_review_required && !mandatoryMismatch && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-100 bg-amber-50 p-4">

          <AlertCircle
            size={19}
            className="mt-0.5 shrink-0 text-amber-600"
          />

          <div>
            <p className="text-sm font-semibold text-amber-800">
              Eligibility verification required
            </p>

            <p className="mt-1 text-xs leading-5 text-amber-700">
              Some eligibility requirements remain unresolved.
              Review the original requirements before applying.
            </p>
          </div>

        </div>
      )}


      {/* Expandable explanation */}

      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
        className="mt-5 flex w-full items-center justify-between border-t border-slate-100 pt-4 text-left text-sm font-semibold text-violet-700"
      >
        {expanded
          ? "Hide recommendation details"
          : "View recommendation details"}

        <ChevronDown
          size={19}
          className={`transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>


      {expanded && (
        <div className="mt-5 space-y-5">

          {/* Summary */}

          <div className="rounded-xl bg-violet-50 p-4">

            <h4 className="flex items-center gap-2 text-sm font-bold text-violet-800">
              <Sparkles size={17} />
              Why this recommendation?
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-700">
              {explanation.summary || "No explanation available."}
            </p>

          </div>


          {/* Technical alignment */}

          {scoreExplanation.technical_alignment_status && (
            <div className="rounded-xl border border-slate-200 p-4">

              <h4 className="font-semibold text-slate-900">
                Technical alignment
              </h4>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                {scoreExplanation.technical_alignment_reason}
              </p>

              {typeof technicalFactor === "number" && (
                <div className="mt-3 rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">
                    Technical ranking factor
                  </p>

                  <p className="mt-1 text-xl font-bold text-violet-700">
                    {technicalFactor.toFixed(2)}x
                  </p>
                </div>
              )}

              <div className="mt-4 space-y-4">

                {[
                  {
                    label: "Required technical requirements",
                    data: requiredTechnical,
                  },
                  {
                    label: "Preferred technical requirements",
                    data: preferredTechnical,
                  },
                ].map(({ label, data }) => (

                  data && (
                    <div key={label}>

                      <h5 className="text-sm font-semibold text-slate-800">
                        {label}
                      </h5>

                      {data.total_requirements > 0 ? (
                        <>
                          <p className="mt-2 text-xs text-slate-600">
                            {data.matched_requirements} of{" "}
                            {data.total_requirements} requirements matched
                          </p>

                          <div className="mt-2">
                            <ScoreDisplay
                              label="Technical requirement match"
                              value={
                                typeof data.match_ratio === "number"
                                  ? data.match_ratio * 100
                                  : null
                              }
                              color="bg-violet-500"
                            />
                          </div>

                          {data.matched_skills?.length > 0 && (
                            <div className="mt-3">
                              <p className="mb-2 text-xs font-medium text-slate-600">
                                Matched technical skills
                              </p>

                              <SkillChips skills={data.matched_skills} />
                            </div>
                          )}

                          {data.missing_requirements?.length > 0 && (
                            <div className="mt-3">
                              <p className="mb-2 text-xs font-medium text-slate-600">
                                Unmatched technical requirements
                              </p>

                              <SkillChips
                                skills={data.missing_requirements}
                                variant="gap"
                              />
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="mt-2 text-xs text-slate-500">
                          No resolved technical requirements available
                          in this category.
                        </p>
                      )}

                    </div>
                  )
                ))}

              </div>

            </div>
          )}


          {/* Contextual requirement interpretation */}

          {requirementNotes.length > 0 && (
            <div>

              <h4 className="mb-3 font-semibold text-slate-900">
                Requirement interpretation
              </h4>

              <div className="space-y-3">

                {requirementNotes.map((note, index) => (
                  <div
                    key={index}
                    className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                  >

                    <p className="text-sm font-semibold text-slate-800">
                      {note.type === "future_certification"
                        ? "Future certification: " + note.skill
                        : note.type === "alternative_requirement"
                          ? (note.skills ?? []).join(" OR ")
                          : formatLabel(note.type)}
                    </p>

                    {note.category && (
                      <p className="mt-1 text-xs text-slate-500">
                        {formatLabel(note.category)}
                      </p>
                    )}

                    {note.type === "alternative_requirement" && (
                      <p className={`mt-1 text-xs font-medium ${
                        note.satisfied
                          ? "text-emerald-700"
                          : "text-amber-700"
                      }`}>
                        {note.satisfied
                          ? "Satisfied"
                          : "No matching option recorded"}
                      </p>
                    )}

                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {note.message}
                    </p>

                  </div>
                ))}

              </div>

            </div>
          )}


          {/* Strengths */}

          <div>

            <h4 className="mb-3 font-semibold text-slate-900">
              Matching strengths
            </h4>

            {strengths.length > 0 ? (
              <div className="space-y-2">

                {strengths.map((strength, index) => (
                  <div
                    key={index}
                    className="rounded-xl bg-emerald-50 p-3"
                  >

                    <p className="text-xs font-semibold text-emerald-700">
                      {formatLabel(strength.component)}
                    </p>

                    <p className="mt-1 text-sm leading-6 text-slate-700">
                      {strength.message}
                    </p>

                  </div>
                ))}

              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No structured strengths identified.
              </p>
            )}

          </div>


          {/* Skill gaps */}

          <div>

            <h4 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
              <Target size={18} className="text-amber-600" />
              Identified skill gaps
            </h4>

            {skillGaps.length > 0 ? (
              <div className="space-y-3">

                {skillGaps.map((gap, index) => (
                  <div
                    key={index}
                    className="rounded-xl border border-amber-100 bg-amber-50/40 p-4"
                  >

                    <p className="text-sm font-semibold text-slate-800">
                      {formatLabel(gap.category)}
                    </p>

                    <p className="mt-1 text-xs font-medium text-amber-700">
                      {formatLabel(gap.priority)} priority
                    </p>

                    <p className="my-3 text-sm text-slate-600">
                      {gap.message}
                    </p>

                    <SkillChips
                      skills={gap.skills ?? []}
                      variant="gap"
                    />

                  </div>
                ))}

              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No skill gaps identified from the available
                extracted requirements. This does not establish
                complete job suitability.
              </p>
            )}

          </div>


          {/* Improvement priorities */}

          <div>

            <h4 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
              <TrendingUp size={18} className="text-violet-600" />
              Improvement priorities
            </h4>

            {priorities.length > 0 ? (
              <div className="space-y-3">

                {priorities.map((priority, index) => (
                  <div
                    key={index}
                    className="rounded-xl bg-slate-50 p-4"
                  >

                    <p className="text-xs font-semibold text-violet-700">
                      {formatLabel(priority.priority)} priority
                    </p>

                    <p className="mt-2 text-sm text-slate-700">
                      {priority.action}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">

                      {[
                        ...(priority.skills ?? []),
                        ...(priority.activities ?? []),
                        ...(priority.constraints ?? []),
                      ].map((value, valueIndex) => (
                        <span
                          key={valueIndex}
                          className="rounded-lg bg-white px-3 py-1 text-xs text-slate-600 shadow-sm"
                        >
                          {formatLabel(value)}
                        </span>
                      ))}

                    </div>

                  </div>
                ))}

              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No additional improvement priorities identified.
              </p>
            )}

          </div>


          {/* Eligibility details */}

          {eligibilityReviews.length > 0 && (
            <div>

              <h4 className="mb-3 font-semibold text-slate-900">
                Eligibility details
              </h4>

              <div className="space-y-3">

                {eligibilityReviews.map((review, index) => (
                  <div
                    key={index}
                    className="rounded-xl bg-amber-50 p-4"
                  >

                    <p className="text-sm font-semibold text-amber-800">
                      {formatLabel(review.component)}
                    </p>

                    <p className="mt-2 text-sm text-slate-700">
                      {review.reason}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">

                      {(review.constraints ?? []).map(
                        (constraint, constraintIndex) => (
                          <span
                            key={constraintIndex}
                            className="rounded-lg bg-white px-3 py-1 text-xs text-amber-800"
                          >
                            {formatLabel(constraint)}
                          </span>
                        )
                      )}

                    </div>

                  </div>
                ))}

              </div>

            </div>
          )}


          {/* Evidence limitations */}

          {warnings.length > 0 && (
            <div>

              <h4 className="mb-3 font-semibold text-slate-900">
                Evidence limitations
              </h4>

              <div className="space-y-2">

                {warnings.map((warning, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 rounded-xl bg-slate-50 p-3"
                  >

                    <Info
                      size={16}
                      className="mt-0.5 shrink-0 text-slate-500"
                    />

                    <p className="text-sm leading-6 text-slate-600">
                      {warning.message}
                    </p>

                  </div>
                ))}

              </div>

            </div>
          )}

        </div>
      )}

    </article>
  );
}


export default function Recommendations() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [topK, setTopK] = useState(10);

  const controllerRef = useRef(null);

  const candidateId = localStorage.getItem("candidate_id");
  const resumeId = localStorage.getItem("resume_id");

  const canGenerate = Boolean(candidateId && resumeId);


  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);


  async function generateRecommendations() {

    if (loading || controllerRef.current) return;

    if (!canGenerate) {
      setError(
        "Create your student profile and upload a resume first."
      );
      return;
    }

    const controller = new AbortController();

    controllerRef.current = controller;

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const response = await fetch(
        "/api/recommendations/generate",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            candidate_id: candidateId,
            resume_id: resumeId,
            top_k: topK,
          }),

          signal: controller.signal,
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {

        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : `Recommendation request failed (${response.status}).`
        );

      }

      if (!Array.isArray(data?.recommendations)) {
        throw new Error(
          "The recommendation service returned an invalid response."
        );
      }

      if (!controller.signal.aborted) {
        setResult(data);
      }

    } catch (err) {

      if (!controller.signal.aborted) {
        setError(
          err.message || "Unable to generate recommendations."
        );
      }

    } finally {

      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }

      if (!controller.signal.aborted) {
        setLoading(false);
      }

    }

  }


  const recommendations = result?.recommendations ?? [];
  const statistics = result?.ranking_statistics ?? {};


  return (
    <section className="mx-auto max-w-5xl">

      {/* Page header */}

      <div className="mb-7">

        <div className="mb-4 inline-flex rounded-2xl bg-violet-100 p-4 text-violet-600">
          <BriefcaseBusiness size={30} />
        </div>

        <h2 className="text-3xl font-bold text-slate-900">
          Internship Recommendations
        </h2>

        <p className="mt-2 text-slate-500">
          Discover internship opportunities aligned with your
          resume, skills, education, experience and projects.
        </p>

      </div>


      {/* Historical dataset disclaimer */}

      <div className="mb-6 flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4">

        <Info
          size={20}
          className="mt-0.5 shrink-0 text-blue-600"
        />

        <div>

          <p className="text-sm font-semibold text-blue-800">
            Sample internship knowledge base
          </p>

          <p className="mt-1 text-sm leading-6 text-blue-700">
            Recommendations are generated from historical
            internship postings for matching and evaluation.
            These are not verified active vacancies.
          </p>

        </div>

      </div>


      {/* Generation controls */}

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <h3 className="text-lg font-bold text-slate-900">
          Find your internship matches
        </h3>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Our recommendation engine retrieves relevant roles,
          evaluates resume compatibility and identifies
          potential skill gaps.
        </p>

        <div className="mt-5 flex flex-wrap items-end gap-4">

          <div>

            <label
              htmlFor="recommendation-count"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Number of recommendations
            </label>

            <select
              id="recommendation-count"
              value={topK}
              disabled={loading}
              onChange={(event) =>
                setTopK(Number(event.target.value))
              }
              className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
            >

              <option value={5}>5 recommendations</option>
              <option value={10}>10 recommendations</option>
              <option value={15}>15 recommendations</option>
              <option value={20}>20 recommendations</option>

            </select>

          </div>

          <button
            type="button"
            onClick={generateRecommendations}
            disabled={loading || !canGenerate}
            className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >

            {loading ? (
              <LoaderCircle
                size={19}
                className="animate-spin"
              />
            ) : (
              <Sparkles size={19} />
            )}

            {loading
              ? "Generating..."
              : "Generate Recommendations"}

          </button>

        </div>

        {!canGenerate && (
          <p className="mt-4 text-sm text-amber-700">
            Complete your student profile and upload and analyze
            your resume before generating recommendations.
          </p>
        )}

      </div>


      {/* Loading state */}

      {loading && (
        <div
          role="status"
          className="rounded-2xl border border-violet-100 bg-white px-6 py-12 text-center"
        >

          <LoaderCircle
            size={38}
            className="mx-auto animate-spin text-violet-600"
          />

          <h3 className="mt-5 font-bold text-slate-900">
            Finding your internship matches
          </h3>

          <p className="mt-2 text-sm text-slate-500">
            Retrieving relevant internships, comparing resume
            evidence and generating explanations.
          </p>

          <p className="mt-2 text-xs text-slate-400">
            This may take several seconds or longer.
          </p>

        </div>
      )}


      {/* Error state */}

      {error && (
        <div
          role="alert"
          className="mb-6 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-5 text-red-700"
        >

          <AlertCircle size={20} className="shrink-0" />

          <div>

            <p className="font-semibold">
              Unable to generate recommendations
            </p>

            <p className="mt-2 text-sm">
              {error}
            </p>

          </div>

        </div>
      )}


      {/* Initial empty state */}

      {!loading && !result && !error && (
        <div className="rounded-3xl border border-slate-200 bg-white px-6 py-14 text-center shadow-sm">

          <FileSearch
            size={42}
            className="mx-auto text-violet-500"
          />

          <h3 className="mt-5 text-xl font-bold text-slate-900">
            Your internship matches will appear here
          </h3>

          <p className="mt-3 text-sm text-slate-500">
            Generate recommendations to explore personalized
            matches and resume improvement opportunities.
          </p>

        </div>
      )}


      {/* Recommendation results */}

      {result && !loading && (
        <div>

          {/* Statistics */}

          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            {[
              {
                label: "Internships evaluated",
                value: statistics.total_ranked ?? 0,
              },
              {
                label: "Recommendations returned",
                value: recommendations.length,
              },
              {
                label: "Internships needing eligibility review",
                value: statistics.eligibility_review_count ?? 0,
              },
              {
                label: "Mandatory eligibility mismatches",
                value: statistics.mandatory_eligibility_mismatch_count ?? 0,
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >

                <p className="text-sm text-slate-500">
                  {stat.label}
                </p>

                <p className="mt-2 text-3xl font-bold text-violet-600">
                  {stat.value}
                </p>

              </div>
            ))}

          </div>


          {/* Score interpretation */}

          <div className="mb-6 rounded-xl bg-slate-100 p-4 text-xs leading-6 text-slate-600">

            <p>
              <strong>Compatibility score:</strong>{" "}
              Alignment across evaluated matching evidence.
            </p>

            <p>
              <strong>Ranking score:</strong>{" "}
              Compatibility adjusted for evidence coverage
              and technical alignment. Mandatory eligibility
              mismatches are deprioritized before numeric
              ranking scores are compared.
            </p>

            <p>
              Scores are matching indicators, not probabilities
              of selection or guarantees of eligibility.
            </p>

          </div>


          {recommendations.length > 0 ? (
            <div className="space-y-5">

              {recommendations.map((item) => (
                <RecommendationCard
                  key={item.job_id}
                  item={item}
                />
              ))}

            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">

              <FileSearch
                size={36}
                className="mx-auto text-slate-400"
              />

              <h3 className="mt-4 font-bold text-slate-800">
                No recommendations found
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                Review your resume information and try again.
              </p>

            </div>
          )}

        </div>
      )}

    </section>
  );
}