import { useState } from "react";
import {
  GraduationCap,
  LayoutDashboard,
  UserRound,
  FileText,
  BrainCircuit,
  BriefcaseBusiness,
  Menu,
  X,
  ArrowRight,
  UploadCloud,
  Sparkles,
  CheckCircle2,
  Clock3,
} from "lucide-react";

import StudentProfile from "./components/StudentProfile";

import ResumeUpload from "./components/ResumeUpload";

import Skills from "./components/Skills";

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "My Profile", icon: UserRound },
  { name: "My Resume", icon: FileText },
  { name: "My Skills", icon: BrainCircuit },
  { name: "Career Tools", icon: BriefcaseBusiness, comingSoon: true },
];

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function navigate(page) {
    setActivePage(page);
    setSidebarOpen(false);
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {sidebarOpen && (
        <button
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-6">
          <div className="rounded-xl bg-violet-600 p-2.5 text-white">
            <GraduationCap size={24} />
          </div>
          <div>
            <h1 className="font-bold leading-tight">AI Career</h1>
            <p className="text-sm font-semibold text-violet-600">Companion</p>
          </div>
          <button
            aria-label="Close menu"
            className="ml-auto lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-6">
          <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </p>

          {navigation.map((item) => {
            const Icon = item.icon;
            const selected = activePage === item.name;

            return (
              <button
                key={item.name}
                disabled={item.comingSoon}
                onClick={() => navigate(item.name)}
                className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                  selected
                    ? "bg-violet-50 text-violet-700"
                    : "text-slate-600 hover:bg-slate-50"
                } ${item.comingSoon ? "cursor-not-allowed opacity-50" : ""}`}
              >
                <Icon size={19} />
                <span className="flex-1">{item.name}</span>
                {item.comingSoon && <span className="text-[10px]">Soon</span>}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-slate-100 p-5">
          <div className="rounded-xl bg-violet-50 p-4">
            <Sparkles className="mb-2 text-violet-600" size={22} />
            <p className="text-sm font-semibold">Your career journey</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Build your profile and discover your strengths.
            </p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-10">
          <div className="flex items-center gap-4">
            <button
              aria-label="Open menu"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"
            >
              <Menu size={23} />
            </button>

            <div>
              <p className="text-xs text-slate-400">Your workspace</p>
              <h2 className="text-lg font-bold">{activePage}</h2>
            </div>
          </div>

          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 font-bold text-violet-700">
            S
          </div>
        </header>

        <main className="mx-auto max-w-6xl space-y-8 px-5 py-8 md:px-10">
          {activePage === "Dashboard" ? (
            <>
              <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-700 via-purple-600 to-indigo-600 p-8 text-white shadow-lg shadow-violet-100 md:p-12">
                <div className="relative z-10 max-w-xl">
                  <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs font-medium">
                    <Sparkles size={15} />
                    Your AI-powered career workspace
                  </div>

                  <h2 className="text-3xl font-bold leading-tight md:text-4xl">
                    Your future starts here.
                  </h2>

                  <p className="mt-4 max-w-md text-sm leading-7 text-violet-100 md:text-base">
                    Create your student profile, upload your resume, and
                    understand your skills—all in one place.
                  </p>

                  <button
                    onClick={() => navigate("My Profile")}
                    className="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-violet-700 transition hover:bg-violet-50"
                  >
                    Create your profile
                    <ArrowRight size={17} />
                  </button>
                </div>

                <GraduationCap
                  size={230}
                  strokeWidth={0.8}
                  className="absolute -bottom-12 -right-10 rotate-[-15deg] text-white/10"
                />
              </section>

              <section>
                <div className="mb-5">
                  <h3 className="text-xl font-bold">Get started</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Complete these steps to build your career profile.
                  </p>
                </div>

                <div className="grid gap-5 md:grid-cols-3">
                  {[
                    {
                      title: "Create your profile",
                      description:
                        "Add your personal and academic information.",
                      icon: UserRound,
                      page: "My Profile",
                      color: "bg-blue-50 text-blue-600",
                    },
                    {
                      title: "Upload your resume",
                      description: "Upload a PDF or DOCX resume for analysis.",
                      icon: UploadCloud,
                      page: "My Resume",
                      color: "bg-violet-50 text-violet-600",
                    },
                    {
                      title: "Explore your skills",
                      description:
                        "Review the information extracted from your resume.",
                      icon: BrainCircuit,
                      page: "My Skills",
                      color: "bg-emerald-50 text-emerald-600",
                    },
                  ].map((item) => {
                    const Icon = item.icon;

                    return (
                      <button
                        key={item.title}
                        onClick={() => navigate(item.page)}
                        className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-md"
                      >
                        <div
                          className={`mb-5 inline-flex rounded-xl p-3 ${item.color}`}
                        >
                          <Icon size={25} />
                        </div>
                        <h4 className="font-bold">{item.title}</h4>
                        <p className="mt-2 min-h-12 text-sm leading-6 text-slate-500">
                          {item.description}
                        </p>
                        <div className="mt-5 flex items-center gap-2 text-sm font-semibold text-violet-600">
                          Get started <ArrowRight size={16} />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>

              <section className="grid gap-5 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-6">
                  <h3 className="mb-5 font-bold">Your progress</h3>
                  <div className="space-y-5">
                    <div className="flex items-center gap-3">
                      <Clock3 className="text-amber-500" size={20} />
                      <span className="flex-1 text-sm">
                        Create student profile
                      </span>
                      <span className="text-xs text-slate-400">
                        Not started
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Clock3 className="text-amber-500" size={20} />
                      <span className="flex-1 text-sm">Upload your resume</span>
                      <span className="text-xs text-slate-400">
                        Not started
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="text-slate-300" size={20} />
                      <span className="flex-1 text-sm text-slate-500">
                        Review extracted skills
                      </span>
                      <span className="text-xs text-slate-400">Pending</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6">
                  <div className="mb-4 flex items-center gap-3">
                    <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600">
                      <BriefcaseBusiness size={23} />
                    </div>
                    <h3 className="font-bold">Career tools</h3>
                  </div>
                  <p className="text-sm leading-7 text-slate-500">
                    Internship matching, skill-gap analysis, cover letters, and
                    interview preparation are planned for upcoming milestones.
                  </p>
                  <span className="mt-5 inline-block rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
                    Coming soon
                  </span>
                </div>
              </section>
            </>
          ) : activePage === "My Profile" ? (
            <StudentProfile />
          ) : activePage === "My Resume" ? (
            <ResumeUpload />
          ) : activePage === "My Skills" ? (
            <Skills />
          ) : (
            <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm md:p-12">
              <div className="mb-5 inline-flex rounded-2xl bg-violet-50 p-4 text-violet-600">
                {activePage === "My Profile" ? (
                  <UserRound size={32} />
                ) : activePage === "My Resume" ? (
                  <FileText size={32} />
                ) : (
                  <BrainCircuit size={32} />
                )}
              </div>

              <h2 className="text-2xl font-bold">{activePage}</h2>

              <p className="mt-3 max-w-lg leading-7 text-slate-500">
                This page is ready for development. Next, we'll connect it to
                your existing FastAPI backend.
              </p>

              <button
                onClick={() => navigate("Dashboard")}
                className="mt-7 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-700"
              >
                Back to dashboard
              </button>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
