import { Activity, BookOpenCheck, Building2, HeartPulse, ShieldCheck, UsersRound } from "lucide-react";
import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-slate-100 lg:grid lg:grid-cols-[1.08fr_.92fr]">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-blue-900 via-blue-800 to-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -left-24 top-24 size-72 rounded-full bg-blue-400/20 blur-3xl" />
        <div className="absolute -bottom-28 right-0 size-80 rounded-full bg-cyan-300/10 blur-3xl" />
        <div className="relative flex items-center gap-3 text-xl font-bold">
          <span className="grid size-12 place-items-center rounded-2xl bg-white/15 ring-1 ring-white/20">
            <ShieldCheck size={26} />
          </span>
          <span>CCMS</span>
        </div>
        <div className="relative max-w-2xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[.25em] text-blue-200">Secure child care management</p>
          <h1 className="text-5xl font-bold leading-tight">Better information for better care.</h1>
          <p className="mt-6 text-lg leading-8 text-blue-100">
            A secure workspace for child records, accommodation, health, education, sponsorship, case management, and development tracking.
          </p>
          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            {[
              ["Child records", UsersRound],
              ["Accommodation", Building2],
              ["Health & education", HeartPulse],
              ["Audited activity", Activity],
            ].map(([label, Icon]) => (
              <div key={String(label)} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-blue-50">
                <Icon size={18} />
                <span>{String(label)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="relative flex items-center justify-between text-sm text-blue-200">
          <span>Child Care Management System</span>
          <span className="inline-flex items-center gap-2"><BookOpenCheck size={16} /> Authorized workspace</span>
        </div>
      </section>
      <section className="grid min-h-screen place-items-center p-5 sm:p-8 lg:min-h-0">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white/95 p-7 shadow-xl shadow-slate-200/70 sm:p-9">
          <div className="mb-8 text-center sm:text-left">
            <div className="mx-auto mb-5 grid size-14 place-items-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100 sm:mx-0">
              <ShieldCheck size={30} />
            </div>
            <p className="eyebrow">CCMS secure sign in</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-950">Welcome back</h1>
            <p className="mt-2 text-sm leading-6 text-slate-500">Sign in to continue to CCMS.</p>
          </div>
          <LoginForm />
          <p className="mt-8 text-center text-xs text-slate-400">Authorized personnel only • Activity is audited</p>
        </div>
      </section>
    </main>
  );
}
