
import { useState } from "react";
import { UserRound, Save, LoaderCircle } from "lucide-react";

export default function StudentProfile() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    location: "",
    professional_summary: "",
  });

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");

    try {
      const response = await fetch("/api/students/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to save your profile."
        );
      }

      setMessage("Your student profile was created successfully!");
      localStorage.setItem("candidate_id", data.candidate_id);
    } catch (error) {
      setMessage(error.message || "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  const fields = [
    { name: "full_name", label: "Full Name", type: "text", placeholder: "Enter your full name" },
    { name: "email", label: "Email Address", type: "email", placeholder: "you@example.com" },
    { name: "phone", label: "Phone Number", type: "tel", placeholder: "Enter your phone number" },
    { name: "location", label: "Location", type: "text", placeholder: "City, State" },
  ];

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-7">
        <div className="mb-4 inline-flex rounded-2xl bg-violet-100 p-4 text-violet-600">
          <UserRound size={30} />
        </div>
        <h2 className="text-2xl font-bold">Create your student profile</h2>
        <p className="mt-2 text-slate-500">
          Tell us a little about yourself to get started.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-9"
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
                required={field.name === "full_name" || field.name === "email"}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-100"
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

        {message && (
          <p role="status" className="rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
            {message}
          </p>
        )}

        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-60"
        >
          {saving ? <LoaderCircle size={18} className="animate-spin" /> : <Save size={18} />}
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </form>
    </section>
  );
}
