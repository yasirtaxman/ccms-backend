"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Save, Send, X } from "lucide-react";
import { childrenApi } from "@/lib/children";
import { developmentApi } from "@/lib/development";
import { apiErrorMessage } from "@/lib/api";
import type { Child } from "@/types/children";
import type { DevelopmentIndicator, DevelopmentObservation, DevelopmentObservationPayload, ObservationResponseInput } from "@/types/development";
import { DevelopmentIndicatorField } from "./DevelopmentIndicatorField";

const risky = ["Needs immediate review", "High concern", "Confirmed concern", "Repeated", "High"];
const categories = ["Personal Hygiene & Cleanliness", "Discipline & Responsibility", "Social Behavior", "Emotional Wellbeing", "Confidence & Communication", "Learning Behavior", "Talent & Interests", "Physical Activity & Sports", "Digital Behavior & Screen Awareness", "Safety & Risk Indicators", "Spiritual / Moral Development", "Career / Field Suitability Indicators", "Support Needs", "Positive Strengths"];

export function DevelopmentObservationForm({ observationId, childId }: { observationId?: number; childId?: number }) {
  const router = useRouter();
  const [children, setChildren] = useState<Child[]>([]);
  const [indicators, setIndicators] = useState<DevelopmentIndicator[]>([]);
  const [responses, setResponses] = useState<Record<number, ObservationResponseInput>>({});
  const [open, setOpen] = useState<string>(categories[0]);
  const [form, setForm] = useState<DevelopmentObservationPayload>({ child_id: childId || 0, observation_date: new Date().toISOString().slice(0, 10), observation_frequency: "Monthly", observer_role: "", review_status: "Draft", general_summary: "", recommended_support: "", private_notes: "", responses: [] });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([childrenApi.list(), developmentApi.indicators(), observationId ? developmentApi.getObservation(observationId) : Promise.resolve(null as DevelopmentObservation | null)])
      .then(([kids, items, obs]) => {
        setChildren(kids);
        setIndicators(items);
        if (obs) {
          setForm({ child_id: obs.child_id, observation_date: obs.observation_date, observation_period_start: obs.observation_period_start, observation_period_end: obs.observation_period_end, observation_frequency: obs.observation_frequency, observer_role: obs.observer_role, review_status: obs.review_status, next_review_date: obs.next_review_date, general_summary: obs.general_summary, recommended_support: obs.recommended_support, private_notes: obs.private_notes, responses: obs.responses });
          setResponses(Object.fromEntries(obs.responses.map((response) => [response.indicator_id, response])));
        }
      })
      .catch((e) => setError(apiErrorMessage(e)));
  }, [observationId]);

  const groups = useMemo(() => categories.map((category) => [category, indicators.filter((item) => item.category === category)] as const).filter(([, items]) => items.length), [indicators]);
  const responseList = Object.values(responses);
  const completed = responseList.filter((r) => r.value_boolean !== undefined || r.value_number || r.value_text || r.value_json).length;
  const required = indicators.filter((item) => item.is_required);
  const requiredCompleted = required.filter((item) => responses[item.id]?.value_boolean !== undefined || responses[item.id]?.value_number || responses[item.id]?.value_text || responses[item.id]?.value_json).length;
  const urgentCount = responseList.filter((r) => (r.value_boolean === true && indicators.find((i) => i.id === r.indicator_id)?.indicator_name.includes("Self-harm")) || (r.value_text && risky.includes(r.value_text))).length;
  const urgent = urgentCount > 0;

  const save = async (submit = false) => {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload = { ...form, responses: responseList };
      if (urgent && !payload.recommended_support) throw new Error("Urgent observations require a recommended support note and counselor/manager review.");
      const saved = observationId ? await developmentApi.updateObservation(observationId, payload) : await developmentApi.createObservation(payload);
      if (submit) await developmentApi.submit(saved.id);
      setMessage(submit ? "Observation submitted for review." : "Draft saved successfully.");
      router.push(`/dashboard/development/observations/${saved.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : apiErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 pb-24">
      <header>
        <p className="eyebrow">Development Profile</p>
        <h1 className="page-title">{observationId ? "Edit Observation" : "New Development Observation"}</h1>
        <p className="page-subtitle">Compact support-focused observation form. Records current indicators only.</p>
      </header>
      {error && <div className="notice-error">{error}</div>}
      {message && <div className="notice-success">{message}</div>}
      {urgent && <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">Review required indicator selected. Add recommended support and submit for counselor/manager review.</div>}

      <section className="panel">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-bold">Observation Details</h2>
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge label={`Completed: ${completed} / ${indicators.length}`} />
            <Badge label={`Required: ${requiredCompleted} / ${required.length}`} />
            <Badge label={`Urgent flags: ${urgentCount}`} tone={urgent ? "warning" : "neutral"} />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field label="Child"><select className="field-control" value={form.child_id} onChange={(e) => setForm({ ...form, child_id: Number(e.target.value) })}><option value={0}>Select child</option>{children.map((child) => <option value={child.id} key={child.id}>{child.child_id} - {child.full_name}</option>)}</select></Field>
          <Field label="Observation date"><input className="field-control" type="date" value={form.observation_date} onChange={(e) => setForm({ ...form, observation_date: e.target.value })} /></Field>
          <Field label="Frequency"><select className="field-control" value={form.observation_frequency} onChange={(e) => setForm({ ...form, observation_frequency: e.target.value })}>{["Monthly", "Weekly", "As Needed", "Incident Based", "Counselor Review", "Teacher Review", "Warden Review"].map((item) => <option key={item}>{item}</option>)}</select></Field>
          <Field label="Period start"><input className="field-control" type="date" value={form.observation_period_start || ""} onChange={(e) => setForm({ ...form, observation_period_start: e.target.value || null })} /></Field>
          <Field label="Period end"><input className="field-control" type="date" value={form.observation_period_end || ""} onChange={(e) => setForm({ ...form, observation_period_end: e.target.value || null })} /></Field>
          <Field label="Next review date"><input className="field-control" type="date" value={form.next_review_date || ""} onChange={(e) => setForm({ ...form, next_review_date: e.target.value || null })} /></Field>
          <Field label="Review status"><select className="field-control" value={form.review_status || "Draft"} onChange={(e) => setForm({ ...form, review_status: e.target.value })}>{["Draft", "Submitted", "Reviewed", "Needs Follow-up", "Closed", "Archived"].map((item) => <option key={item}>{item}</option>)}</select></Field>
        </div>
      </section>

      <div className="space-y-3">
        {groups.map(([category, items]) => {
          const answered = items.filter((item) => responses[item.id]?.value_boolean !== undefined || responses[item.id]?.value_number || responses[item.id]?.value_text || responses[item.id]?.value_json).length;
          return <section className="panel p-0" key={category}>
            <button type="button" className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left" onClick={() => setOpen(open === category ? "" : category)}>
              <span className="font-bold text-slate-900">{category}</span>
              <span className="text-xs text-slate-500">{answered} / {items.length}</span>
            </button>
            {open === category && <div className="border-t border-slate-100">{items.map((item) => <DevelopmentIndicatorField key={item.id} indicator={item} value={responses[item.id]} onChange={(value) => setResponses((current) => ({ ...current, [item.id]: value }))} />)}</div>}
          </section>;
        })}
      </div>

      <section className="panel">
        <h2 className="mb-4 text-lg font-bold">Summary & Recommended Support</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="General summary"><textarea className="field-control min-h-28" value={form.general_summary || ""} onChange={(e) => setForm({ ...form, general_summary: e.target.value })} /></Field>
          <Field label="Recommended support"><textarea className="field-control min-h-28" value={form.recommended_support || ""} onChange={(e) => setForm({ ...form, recommended_support: e.target.value })} /></Field>
          <label className="form-field md:col-span-2"><span>Private notes</span><textarea className="field-control min-h-20" value={form.private_notes || ""} onChange={(e) => setForm({ ...form, private_notes: e.target.value })} /></label>
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-slate-200 bg-white/95 px-4 py-3 shadow-lg backdrop-blur md:left-72">
        <div className="mx-auto flex max-w-6xl flex-wrap justify-end gap-3">
          <button className="secondary-button" onClick={() => router.back()}><X size={16} />Cancel</button>
          <button className="secondary-button" disabled={saving || !form.child_id} onClick={() => save(false)}><Save size={16} />Save Draft</button>
          <button className="primary-button" disabled={saving || !form.child_id} onClick={() => save(true)}><Send size={16} />Submit for Review</button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="form-field"><span>{label}</span>{children}</label>;
}

function Badge({ label, tone = "neutral" }: { label: string; tone?: "neutral" | "warning" }) {
  return <span className={`rounded-full px-3 py-1 font-semibold ${tone === "warning" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}>{label}</span>;
}
