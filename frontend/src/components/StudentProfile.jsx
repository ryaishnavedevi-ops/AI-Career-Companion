import { useState, useEffect } from "react";
import {
  UserRound,
  Save,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";


const EMPTY_FORM = {
  full_name: "",
  email: "",
  phone: "",
  location: "",
  professional_summary: "",
};


export default function StudentProfile() {
  const [form, setForm] = useState({ ...EMPTY_FORM });

  const [candidateId, setCandidateId] = useState(
    () => localStorage.getItem("candidate_id")
  );

  const [loading, setLoading] = useState(Boolean(candidateId));
  const [profileReady, setProfileReady] = useState(!candidateId);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("success");
  const [retryCount, setRetryCount] = useState(0);


  // Load an existing student profile.

  useEffect(() => {
    if (!candidateId) return;

    const controller = new AbortController();

    async function loadProfile() {
      try {
        const response = await fetch(
          `/api/students/${encodeURIComponent(candidateId)}`,
          {
            signal: controller.signal,
          }
        );

        const data = await response.json().catch(() => null);

        if (response.status === 404) {
          localStorage.removeItem("candidate_id");
          localStorage.removeItem("resume_id");

          setCandidateId(null);
          setForm({ ...EMPTY_FORM });
          setProfileReady(true);

          setMessageType("error");
          setMessage(
            "Your saved student profile no longer exists. Please create a new profile."
          );

          return;
        }

        if (!response.ok || !data) {
          throw new Error(
            typeof data?.detail === "string"
              ? data.detail
              : "Unable to load your student profile."
          );
        }

        if (controller.signal.aborted) return;

        setForm({
          full_name: data.full_name ?? "",
          email: data.email ?? "",
          phone: data.phone ?? "",
          location: data.location ?? "",
          professional_summary: data.professional_summary ?? "",
        });

        setProfileReady(true);

      } catch (error) {
        if (!controller.signal.aborted) {
          setProfileReady(false);
          setMessageType("error");
          setMessage(
            error.message || "Unable to load your profile."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => controller.abort();

  }, [candidateId, retryCount]);


  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }


  async function handleSubmit(event) {
    event.preventDefault();

    if (saving || loading || !profileReady) return;

    setSaving(true);
    setMessage("");

    const isUpdating = Boolean(candidateId);

    const endpoint = isUpdating
      ? `/api/students/${encodeURIComponent(candidateId)}`
      : "/api/students/";

    const payload = {
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      location: form.location.trim(),
      professional_summary: form.professional_summary.trim(),
    };

    try {
      const response = await fetch(endpoint, {
        method: isUpdating ? "PUT" : "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : `Unable to save your profile (${response.status}).`
        );
      }

      if (!data?.candidate_id) {
        throw new Error(
          "The server returned an invalid student profile."
        );
      }

      if (!isUpdating) {
        localStorage.removeItem("resume_id");
      }

      localStorage.setItem(
        "candidate_id",
        data.candidate_id
      );

      setCandidateId(data.candidate_id);

      setMessageType("success");

      setMessage(
        isUpdating
          ? "Your student profile was updated successfully!"
          : "Your student profile was created successfully!"
      );

    } catch (error) {
      setMessageType("error");
      setMessage(
        error.message || "Something went wrong."
      );
    } finally {
      setSaving(false);
    }
  }


  const fields = [
    {
      name: "full_name",
      label: "Full Name",
      type: "text",
      placeholder: "Enter your full name",
    },
    {
      name: "email",
      label: "Email Address",
      type: "email",
      placeholder: "you@example.com",
    },
    {
      name: "phone",
      label: "Phone Number",
      type: "tel",
      placeholder: "Enter your phone number",
    },
    {
      name: "location",
      label: "Location",
      type: "text",
      placeholder: "City, State",
    },
  ];


  return (
    <section className="mx-auto max-w-3xl">

      <div className="mb-7">

        <div className="mb-4 inline-flex rounded-2xl bg-violet-100 p-4 text-violet-600">
          <UserRound size={30} />
        </div>

        <h2 className="text-2xl font-bold">
          {candidateId
            ? "Your student profile"
            : "Create your student profile"}
        </h2>

        <p className="mt-2 text-slate-500">
          {candidateId
            ? "Review and update your personal and career information."
            : "Tell us a little about yourself to get started."}
        </p>

      </div>


      {loading ? (
        <div
          role="status"
          className="rounded-3xl border border-slate-200 bg-white p-10 text-center"
        >
          <LoaderCircle
            size={32}
            className="mx-auto animate-spin text-violet-600"
          />

          <p className="mt-4 text-sm text-slate-500">
            Loading your student profile...
          </p>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-9"
        >

          <fieldset
            disabled={saving || !profileReady}
            className="space-y-6"
          >

            <div className="grid gap-5 md:grid-cols-2">

              {fields.map((field) => (
                <div key={field.name}>

                  <label
                    htmlFor={field.name}
                    className="mb-2 block text-sm font-semibold text-slate-700"
                  >
                    {field.label}
                  </label>

                  <input
                    id={field.name}
                    name={field.name}
                    type={field.type}
                    value={form[field.name]}
                    onChange={handleChange}
                    placeholder={field.placeholder}
                    required={
                      field.name === "full_name" ||
                      field.name === "email"
                    }
                    readOnly={
                      field.name === "email" &&
                      Boolean(candidateId)
                    }
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-100 read-only:bg-slate-50"
                  />

                </div>
              ))}

            </div>


            <div>

              <label
                htmlFor="professional_summary"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Professional Summary
              </label>

              <textarea
                id="professional_summary"
                name="professional_summary"
                value={form.professional_summary}
                onChange={handleChange}
                placeholder="Describe your education, interests, and career goals..."
                rows={5}
                className="w-full resize-y rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-100"
              />

            </div>

          </fieldset>


          {message && (
            <div
              role={messageType === "error" ? "alert" : "status"}
              className={`flex items-start gap-3 rounded-xl p-4 text-sm ${
                messageType === "error"
                  ? "bg-red-50 text-red-700"
                  : "bg-emerald-50 text-emerald-700"
              }`}
            >

              {messageType === "error" ? (
                <AlertCircle size={18} className="shrink-0" />
              ) : (
                <CheckCircle2 size={18} className="shrink-0" />
              )}

              <p>{message}</p>

            </div>
          )}


          {!profileReady && candidateId && (
            <button
              type="button"
              onClick={() => {
                setLoading(true);
                setMessage("");
                setRetryCount((count) => count + 1);
              }}
              className="rounded-xl border border-violet-200 px-5 py-3 text-sm font-semibold text-violet-700"
            >
              Retry loading profile
            </button>
          )}


          <button
            type="submit"
            disabled={saving || !profileReady}
            className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-60"
          >

            {saving ? (
              <LoaderCircle size={18} className="animate-spin" />
            ) : (
              <Save size={18} />
            )}

            {saving
              ? "Saving..."
              : candidateId
                ? "Update Profile"
                : "Save Profile"}

          </button>

        </form>
      )}

    </section>
  );
}