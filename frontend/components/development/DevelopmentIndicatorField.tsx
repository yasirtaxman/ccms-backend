"use client";

import type { DevelopmentIndicator, ObservationResponseInput } from "@/types/development";

const ratingLabels = ["1 Poor", "2 Needs Improvement", "3 Satisfactory", "4 Good", "5 Excellent"];

export function cleanDisplay(value: unknown): string {
  if (value === null || value === undefined || value === "" || value === "-" || value === "string") return "Not recorded";
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => cleanDisplay(item)).filter((item) => item !== "Not recorded").join(", ") || "Not recorded" : "Not recorded";
  }
  return String(value);
}

export function DevelopmentIndicatorField({ indicator, value, onChange }: { indicator: DevelopmentIndicator; value?: ObservationResponseInput; onChange: (value: ObservationResponseInput) => void }) {
  const base = { indicator_id: indicator.id };
  const set = (patch: Partial<ObservationResponseInput>) => onChange({ ...base, ...value, ...patch });
  const options = Array.isArray(indicator.options_json) ? indicator.options_json.map(String) : [];
  const active = value?.value_boolean !== undefined || value?.value_number || value?.value_text || value?.value_json;

  return (
    <div className={`grid gap-2 border-t border-slate-100 px-3 py-2.5 text-sm lg:grid-cols-[40%_25%_35%] lg:items-center ${active ? "bg-blue-50/40" : "bg-white"}`}>
      <div className="min-w-0">
        <div className="font-medium text-slate-800">{indicator.indicator_name}</div>
        <div className="mt-1 flex flex-wrap gap-1">
          {indicator.is_required && <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-700">Required</span>}
          {indicator.is_sensitive && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">Review Required</span>}
        </div>
      </div>
      <div>{inputControl(indicator, value, set, options)}</div>
      <input className="field-control h-9" placeholder="Optional note" value={value?.note ?? ""} onChange={(event) => set({ note: event.target.value })} />
    </div>
  );
}

function inputControl(indicator: DevelopmentIndicator, value: ObservationResponseInput | undefined, set: (patch: Partial<ObservationResponseInput>) => void, options: string[]) {
  if (indicator.input_type === "checkbox") {
    return <label className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2"><input type="checkbox" checked={Boolean(value?.value_boolean)} onChange={(event) => set({ value_boolean: event.target.checked })} /><span>Observed</span></label>;
  }
  if (indicator.input_type === "yes_no") {
    return <select className="field-control h-9" value={value?.value_boolean === undefined || value?.value_boolean === null ? "" : String(value.value_boolean)} onChange={(event) => set({ value_boolean: event.target.value === "" ? null : event.target.value === "true" })}><option value="">Select</option><option value="true">Yes</option><option value="false">No</option></select>;
  }
  if (indicator.input_type === "rating_1_to_5") {
    return <div className="flex flex-wrap gap-1" title={ratingLabels.join(" | ")}>{[1, 2, 3, 4, 5].map((number) => <button type="button" key={number} onClick={() => set({ value_number: number })} className={`h-8 w-8 rounded-full border text-xs font-semibold ${value?.value_number === number ? "border-blue-700 bg-blue-700 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-blue-300"}`} aria-label={ratingLabels[number - 1]}>{number}</button>)}</div>;
  }
  if (indicator.input_type === "dropdown") {
    return <select className="field-control h-9" value={value?.value_text ?? ""} onChange={(event) => set({ value_text: event.target.value || null })}><option value="">Select</option>{options.map((option) => <option key={option}>{option}</option>)}</select>;
  }
  if (indicator.input_type === "multi_select") {
    return <select multiple className="field-control min-h-20" value={(value?.value_json as string[]) || []} onChange={(event) => set({ value_json: Array.from(event.target.selectedOptions).map((item) => item.value) })}>{options.map((option) => <option key={option}>{option}</option>)}</select>;
  }
  return <input className="field-control h-9" value={value?.value_text ?? ""} onChange={(event) => set({ value_text: event.target.value })} placeholder="Short note" />;
}
