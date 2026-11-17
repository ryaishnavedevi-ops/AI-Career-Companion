import { useState } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  LoaderCircle,
  Sparkles,
} from "lucide-react";

export default function ResumeUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [resumeId, setResumeId] = useState("");

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState("");

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0];

    setMessage("");
    setResumeId("");
    setFile(null);

    if (!selectedFile) return;

    const extension = selectedFile.name.split(".").pop()?.toLowerCase();

    if (!["pdf", "docx"].includes(extension)) {
      setMessage("Please select a PDF or DOCX file.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setMessage("File size must not exceed 5 MB.");
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
  }

  async function handleUpload() {
    if (!file || uploading) return;

    const candidateId = localStorage.getItem("candidate_id");

    if (!candidateId) {
      setMessage("Create your student profile before uploading a resume.");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`/api/resumes/upload/${candidateId}`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Resume upload failed.",
        );
      }

      setResumeId(data.resume_id);
      localStorage.setItem("resume_id", data.resume_id);
      setMessage("Resume uploaded successfully!");
    } catch (error) {
      setMessage(error.message || "Something went wrong.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAnalyze() {
    if (!resumeId || analyzing) return;

    setAnalyzing(true);
    setAnalysisMessage("");

    try {
      const response = await fetch(`/api/resumes/process/${resumeId}`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Resume analysis failed.",
        );
      }

      setAnalysisMessage("Resume analyzed successfully!");
      localStorage.setItem(
        "resume_extraction",
        JSON.stringify(data.extracted_data),
      );
    } catch (error) {
      setAnalysisMessage(error.message || "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  const successful = Boolean(resumeId);

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-7">
        <div className="mb-4 inline-flex rounded-2xl bg-violet-100 p-4 text-violet-600">
          <FileText size={30} />
        </div>

        <h2 className="text-2xl font-bold">Upload your resume</h2>

        <p className="mt-2 text-slate-500">
          Upload your resume to begin building your career profile.
        </p>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-9">
        <label
          htmlFor="resume-file"
          className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-violet-200 bg-violet-50/50 px-6 py-12 text-center transition hover:border-violet-400 hover:bg-violet-50"
        >
          <UploadCloud size={42} className="mb-4 text-violet-600" />

          <span className="font-semibold text-slate-800">
            Click to choose your resume
          </span>

          <span className="mt-2 text-sm text-slate-500">
            PDF or DOCX, maximum 5 MB
          </span>

          <input
            id="resume-file"
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>

        {file && (
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-200 p-4">
            <FileText size={22} className="text-violet-600" />

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{file.name}</p>
              <p className="text-xs text-slate-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>

            {successful && (
              <CheckCircle2 size={21} className="text-emerald-600" />
            )}
          </div>
        )}

        {message && (
          <div
            role="status"
            className={`mt-5 flex items-center gap-2 rounded-xl p-4 text-sm ${
              successful
                ? "bg-emerald-50 text-emerald-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {successful ? (
              <CheckCircle2 size={19} />
            ) : (
              <AlertCircle size={19} />
            )}
            {message}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading || successful}
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {uploading ? (
            <LoaderCircle size={19} className="animate-spin" />
          ) : (
            <UploadCloud size={19} />
          )}

          {uploading ? "Uploading..." : "Upload Resume"}
        </button>

        {successful && (
          <div className="mt-6 border-t border-slate-100 pt-6">
            <h3 className="font-bold text-slate-800">
              Ready to analyze your resume?
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Extract skills, education, experience, projects, certifications,
              awards, and languages.
            </p>

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={analyzing}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
            >
              {analyzing ? (
                <LoaderCircle size={19} className="animate-spin" />
              ) : (
                <Sparkles size={19} />
              )}

              {analyzing ? "Analyzing..." : "Analyze Resume"}
            </button>

            {analysisMessage && (
              <p role="status" className="mt-4 text-sm text-slate-700">
                {analysisMessage}
              </p>
            )}
          </div>
        )}

        <p className="mt-5 text-xs leading-5 text-slate-400">
          Your resume will be stored securely by the application backend. Resume
          analysis will be available in the next step.
        </p>
      </div>
    </section>
  );
}
